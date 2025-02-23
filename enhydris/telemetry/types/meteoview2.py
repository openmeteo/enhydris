import datetime as dt
import json
from io import StringIO
from zoneinfo import ZoneInfo

from django.utils.translation import gettext_lazy as _

import requests

from enhydris.telemetry.types import TelemetryAPIClientBase


class TelemetryAPIClient(TelemetryAPIClientBase):
    name = "Metrica MeteoView2"
    username_label = _("Email")
    password_label = _("API key")
    device_locator_label = _("Meteoview API URL")
    device_locator_help = _(
        "If this is left blank, https://meteoview2.gr/api/ will be used."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.telemetry.device_locator:
            self.api_url = "https://meteoview2.gr/api/"
        else:
            self.api_url = self.telemetry.device_locator
            if not self.api_url.endswith("/"):
                self.api_url += "/"

    def connect(self):
        data = self.make_request(
            "POST",
            f"{self.api_url}token",
            data={"email": self.telemetry.username, "key": self.telemetry.password},
        )
        self.token = data["token"]

    def get_stations(self):
        data = self.make_request(
            "POST",
            f"{self.api_url}stations",
            headers={"Authorization": f"Bearer {self.token}"},
        )
        return {v["code"]: v["title"] for k, v in data["stations"].items()}

    def get_sensors(self):
        data = self.make_request(
            "POST",
            f"{self.api_url}sensors",
            headers={"Authorization": f"Bearer {self.token}"},
            data={"station_code": self.telemetry.remote_station_id},
        )
        return {s["id"]: s["title"] for s in data["sensors"]}

    def get_measurements(self, sensor_id, timeseries_end_date):
        start_date = self._get_start_date(sensor_id, timeseries_end_date)
        end_date = start_date + dt.timedelta(days=180)
        data = None
        now = dt.datetime.now() + dt.timedelta(days=1)
        while start_date < now:
            data = self.make_request(
                "POST",
                f"{self.api_url}measurements",
                headers={"Authorization": f"Bearer {self.token}"},
                data={
                    "sensor": [sensor_id],
                    "datefrom": start_date.date().isoformat(),
                    "timefrom": start_date.time().isoformat()[:5],
                    "dateto": end_date.date().isoformat(),
                },
            )
            if data["measurements"][0]["total_values"]:
                break
            start_date = end_date + dt.timedelta(minutes=1)
            end_date = start_date + dt.timedelta(days=180)
        if not data or data["measurements"][0]["total_values"] == 0:
            return StringIO("")
        result = ""
        for r in data["measurements"][0]["values"]:
            year = int(r["year"])
            month = int(r["month"]) + 1
            day = int(r["day"])
            hour = int(r["hour"])
            minute = int(r["minute"])
            timestamp = dt.datetime(year, month, day, hour, minute, 0)
            result += f'{timestamp.isoformat()},{r["mvalue"]},\n'
        return StringIO(result)

    def _get_start_date(self, sensor_id, timeseries_end_date):
        if timeseries_end_date is not None:
            timeseries_end_date = timeseries_end_date.astimezone(
                ZoneInfo(self.telemetry.data_timezone)
            ).replace(tzinfo=None)
            start_date = timeseries_end_date + dt.timedelta(minutes=1)
        else:
            start_date = dt.datetime(1990, 1, 1)
        return start_date

    def make_request(self, method, url, *args, **kwargs):
        from enhydris.telemetry import TelemetryError

        if "data" in kwargs:
            kwargs.setdefault("headers", {})
            kwargs["headers"]["content-type"] = "application/json"
            kwargs["data"] = json.dumps(kwargs["data"])
        try:
            response = requests.request(method, url, verify=False, *args, **kwargs)
            response.raise_for_status()
        except (requests.exceptions.SSLError, requests.RequestException) as e:
            raise TelemetryError(str(e))
        data = response.json()
        if "code" not in data:
            raise TelemetryError('Missing "code"')
        if int(data["code"]) != 200:
            raise TelemetryError(f'{data["code"]} {data.get("message", "")}')
        return data
