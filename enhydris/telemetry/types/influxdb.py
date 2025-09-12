import csv
import datetime as dt
import textwrap
from io import StringIO

from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

import requests

from enhydris.telemetry import TelemetryError
from enhydris.telemetry import forms as telemetry_forms
from enhydris.telemetry.models import Telemetry
from enhydris.telemetry.types import TelemetryAPIClientBase


class InfluxConnectionDataForm(telemetry_forms.ConnectionDataForm):
    _bucket = forms.CharField(help_text=_('The InfluxDB "bucket".'))
    _measurement = forms.CharField(
        help_text=_('The InfluxDB "measurement"; i.e. the group of relevant data.')
    )
    _station_tag = forms.CharField(
        help_text=_("The InfluxDB tag that can be used to identify stations.")
    )

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data["additional_config"] = {
            "bucket": cleaned_data.get("_bucket"),
            "measurement": cleaned_data.get("_measurement"),
            "station_tag": cleaned_data.get("_station_tag"),
        }
        cleaned_data.pop("_bucket", None)
        cleaned_data.pop("_measurement", None)
        cleaned_data.pop("_station_tag", None)
        self._check_connection(cleaned_data)

    def _check_connection(self, cleaned_data):
        try:
            telemetry = Telemetry(
                username=cleaned_data.get("username"),
                password=cleaned_data.get("password"),
                device_locator=cleaned_data.get("device_locator"),
                additional_config=cleaned_data.get("additional_config"),
            )
            with self.driver(telemetry) as t:
                nstations = len(t.get_stations())
        except TelemetryError as e:
            raise forms.ValidationError(str(e))
        if not nstations:
            raise forms.ValidationError(
                _('No stations found. Check the "measurement" and "station tag"')
            )


class TelemetryAPIClient(TelemetryAPIClientBase):
    name = "InfluxDB v2"
    username_label = pgettext_lazy("InfluxDB API term", "Organization")
    password_label = _("API token")
    device_locator_label = _("InfluxDB API URL")
    device_locator_help = _("For example, https://influxdb.example.com/api/v2/.")
    hide_data_timezone = True
    forms = [
        telemetry_forms.EssentialDataForm,
        InfluxConnectionDataForm,
        telemetry_forms.ChooseStationForm,
        telemetry_forms.ChooseSensorForm,
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = self.telemetry.username
        self.token = self.telemetry.password
        self.api_url = self.telemetry.device_locator
        if not self.api_url.endswith("/"):
            self.api_url += "/"
        self.api_url += f"query?org={self.organization}"

    def get_stations(self):
        c = self.telemetry.additional_config
        data = self.make_request(
            textwrap.dedent(
                f"""\
                    from(bucket: "{c["bucket"]}")
                    |> range(start: 1990-01-01)
                    |> filter(fn: (r) => r._measurement == "{c["measurement"]}")
                    |> keep(columns: ["{c["station_tag"]}"])
                    |> group()
                    |> distinct(column: "{c["station_tag"]}")
                """
            )
        )
        try:
            return {x["_value"]: "" for x in data}
        except KeyError as e:
            raise TelemetryError(str(e))

    def get_sensors(self):
        c = self.telemetry.additional_config
        data = self.make_request(
            textwrap.dedent(
                f"""\
                    import "influxdata/influxdb/schema"

                    schema.fieldKeys(
                        bucket: "{c["bucket"]}",
                        predicate: (r) => r._measurement == "{c["measurement"]}",
                    )
                """
            )
        )
        try:
            return {x["_value"]: "" for x in data}
        except KeyError as e:
            raise TelemetryError(str(e))

    def get_measurements(self, sensor_id, timeseries_end_date):
        start_date = self._get_start_date(sensor_id, timeseries_end_date)
        t = self.telemetry
        c = self.telemetry.additional_config
        data = self.make_request(
            textwrap.dedent(
                f"""\
                from(bucket: "{c["bucket"]}")
                |> range(start: {start_date.isoformat()})
                |> filter(fn: (r) => r._measurement == "{c["measurement"]}")
                |> filter(fn: (r) => r["{c["station_tag"]}"] == "{t.remote_station_id}")
                |> filter(fn: (r) => r._field == "{sensor_id}")
                |> keep(columns: ["_time", "_value"])
                |> limit(n: 20000)
                """
            )
        )
        try:
            result = ""
            for row in data:
                time = row["_time"][:-1]  # Strip trailing 'Z'
                result += f'{time},{row["_value"]},\n'
            return StringIO(result)
        except KeyError as e:
            raise TelemetryError(str(e))

    def _get_start_date(self, sensor_id, timeseries_end_date):
        if timeseries_end_date is not None:
            timeseries_end_date = timeseries_end_date.replace(tzinfo=dt.timezone.utc)
            start_date = timeseries_end_date + dt.timedelta(minutes=1)
        else:
            start_date = dt.datetime(1990, 1, 1, tzinfo=dt.timezone.utc)
        return start_date

    def make_request(self, querytext):
        from enhydris.telemetry import TelemetryError

        headers = {
            "Content-Type": "application/vnd.flux",
            "Authorization": f"Token {self.token}",
            "Accept": "application/csv",
        }
        try:
            args = [self.api_url]
            kwargs = {
                "verify": False,
                "data": querytext,
                "headers": headers,
                "stream": True,
            }
            with requests.post(*args, **kwargs) as response:
                response.raise_for_status()
                w = response.iter_lines(decode_unicode=True)
                return list(csv.DictReader(w))
        except (
            requests.exceptions.SSLError,
            requests.RequestException,
            csv.Error,
        ) as e:
            raise TelemetryError(str(e))
