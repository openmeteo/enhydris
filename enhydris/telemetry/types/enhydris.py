import configparser
import datetime as dt
from io import StringIO

from django.utils.translation import gettext_lazy as _

import requests
from enhydris_api_client import EnhydrisApiClient, MalformedResponseError

from enhydris.telemetry import TelemetryError
from enhydris.telemetry.types import TelemetryAPIClientBase


class TelemetryAPIClient(TelemetryAPIClientBase):
    name = "Enhydris"
    password_label = _("API token")
    device_locator_label = _("Location of the other Enhydris instance")
    device_locator_help = _("For example, https://enhydris.example.com/.")
    hide_username = True
    hide_data_timezone = True
    sensor_prompt = _(
        "To which local time series does the remote time series "
        "{sensor_label} correspond?"
    )
    ignore_sensor_prompt = _("Ignore this remote time series")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = self.telemetry.password
        self.api_client = EnhydrisApiClient(
            base_url=self.telemetry.device_locator, token=self.token
        )

    def get_stations(self):
        with self.api_client as client:
            try:
                result = {x["id"]: x["name"] for x in client.list_stations()}
            except (requests.RequestException, MalformedResponseError) as e:
                raise TelemetryError(str(e))
        return result

    def get_sensors(self):
        station_id = self.telemetry.remote_station_id
        result = {}
        try:
            with self.api_client as client:
                for tg in client.list_timeseries_groups(station_id):
                    for ts in client.list_timeseries(station_id, tg["id"]):
                        ts_name = (
                            f"{tg['name']} - {ts['type']} {ts['name']} "
                            f"{ts['time_step']}"
                        )
                        result[f"{tg['id']} {ts['id']}"] = ts_name
        except (requests.RequestException, MalformedResponseError) as e:
            raise TelemetryError(str(e))
        return result

    def get_measurements(self, sensor_id, timeseries_end_date):
        station_id = int(self.telemetry.remote_station_id)
        tg_id, ts_id = map(int, sensor_id.split())
        start_date = self._get_start_date(sensor_id, timeseries_end_date)
        with self.api_client as client:
            try:
                data = client.read_tsdata(
                    station_id, tg_id, ts_id, start_date=start_date
                )
            except (requests.RequestException, configparser.ParsingError) as e:
                raise TelemetryError(str(e))
        result = StringIO()
        data.write(result)
        result.seek(0)
        return result

    def _get_start_date(self, sensor_id, timeseries_end_date):
        if timeseries_end_date is not None:
            timeseries_end_date = timeseries_end_date.replace(tzinfo=dt.timezone.utc)
            start_date = timeseries_end_date + dt.timedelta(minutes=1)
        else:
            start_date = dt.datetime(1990, 1, 1, tzinfo=dt.timezone.utc)
        return start_date
