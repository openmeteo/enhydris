from __future__ import annotations

import csv
import datetime as dt
from io import StringIO
from typing import Any, Literal, cast, overload

from django.utils.translation import gettext_lazy as _

import requests

from enhydris.telemetry.types import TelemetryAPIClientBase


class TelemetryAPIClient(TelemetryAPIClientBase):
    name = "insigh.io"
    password_label = _("API token")
    hide_username = True
    hide_device_locator = True
    hide_data_timezone = True

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.token = self.telemetry.password
        self.api_url = "https://console.insigh.io/mf-rproxy/"
        self.cached_measurements: StringIO | None = None

    def get_stations(self) -> dict[str, str]:
        data = self.make_request(f"{self.api_url}device/list", format="json")
        return {f"{v['id']}/{v['metadata']['dataChannel']}": v["name"] for v in data}

    def get_sensors(self) -> dict[str, str]:
        device_id, data_channel = self.telemetry.remote_station_id.split("/")
        data = self.make_request(
            f"{self.api_url}device/lastMeasurement",
            format="json",
            params={"channel": data_channel, "id": device_id},
        )
        names = [v["name"].partition("-")[2] for v in data]
        return {name: "" for name in names}

    def get_measurements(
        self, sensor_id: str, timeseries_end_date: dt.datetime | None
    ) -> StringIO:
        if self.cached_measurements is None:
            self.cached_measurements = self.fetch_measurements(timeseries_end_date)
        self.cached_measurements.seek(0)
        result = StringIO()
        sensor_index: int | None = None
        for i, line in enumerate(csv.reader(self.cached_measurements)):
            if i == 0:
                sensor_index = line.index(sensor_id)
                continue
            assert sensor_index is not None
            timestamp = (
                dt.datetime.fromtimestamp(int(line[0]) // 1000, tz=dt.timezone.utc)
                .replace(tzinfo=None)
                .isoformat()
            )
            value = line[sensor_index]
            result.write(f"{timestamp},{value},\n")
        result.seek(0)
        return result

    def fetch_measurements(self, timeseries_end_date: dt.datetime | None) -> StringIO:
        if timeseries_end_date is None:
            timeseries_end_date = dt.datetime(1970, 1, 1, 0, 0, 0)
        if timeseries_end_date.tzinfo is not None:
            timeseries_end_date = timeseries_end_date.astimezone(dt.timezone.utc)
            timeseries_end_date = timeseries_end_date.replace(tzinfo=None)
        start_timestamp = (
            f"{(timeseries_end_date + dt.timedelta(minutes=1)).isoformat()}Z"
        )
        device_id, data_channel = self.telemetry.remote_station_id.split("/")
        data = self.make_request(
            f"{self.api_url}measurement/queryPack",
            params={
                "channel": data_channel,
                "publisher": device_id,
                "startRange": start_timestamp,
                "limit": 25000,
                "format": "csv",
            },
            format="csv",
        )
        return data

    @overload
    def make_request(
        self, url: str, format: Literal["json"], **kwargs: Any
    ) -> list[dict[str, Any]]: ...

    @overload
    def make_request(
        self, url: str, format: Literal["csv"], **kwargs: Any
    ) -> StringIO: ...

    def make_request(self, url: str, format: str, **kwargs: Any):
        from enhydris.telemetry import TelemetryError

        try:
            headers = {"Authorization": self.token}
            response = requests.get(url, headers=headers, **kwargs)
            response.raise_for_status()
            if format == "json":
                result = response.json()
                assert isinstance(result, list)
                return cast(list[dict[str, Any]], result)
            else:
                return StringIO(response.text)
        except requests.RequestException as e:
            raise TelemetryError(str(e))
