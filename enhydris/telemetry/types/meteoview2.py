import datetime as dt
import json
from io import StringIO

from django import forms
from django.utils.translation import ugettext_lazy as _

import requests

from enhydris.telemetry.types import TelemetryBase


class ErrorResponse(requests.HTTPError):
    pass


class Meteoview2ApiClient:
    def __init__(self, email, key):
        self.email = email
        self.key = key
        self.api_url = "https://meteoview2.gr/api/"

    def login(self):
        data = self.make_request(
            "POST",
            f"{self.api_url}token",
            data={"email": self.email, "key": self.key},
        )
        self.token = data["token"]

    def get_stations(self):
        data = self.make_request(
            "GET",
            f"{self.api_url}stations",
            headers={"Authorization": f"Bearer {self.token}"},
        )
        return data["stations"]

    def get_sensors(self, station_code):
        data = self.make_request(
            "POST",
            f"{self.api_url}sensors",
            headers={"Authorization": f"Bearer {self.token}"},
            data={"station_code": station_code},
        )
        return data["sensors"]

    def get_measurements(self, sensor_id, timeseries_end_date):
        start_date = self._get_start_date(sensor_id, timeseries_end_date)
        end_date = start_date + dt.timedelta(days=180)
        data = None
        now = dt.datetime.now() + dt.timedelta(days=1)
        while start_date.replace(tzinfo=None) < now:
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
        prev_timestamp = None
        for r in data["measurements"][0]["values"]:
            year = int(r["year"])
            month = int(r["month"]) + 1
            day = int(r["day"])
            hour = int(r["hour"])
            minute = int(r["minute"])
            timestamp = dt.datetime(year, month, day, hour, minute, 0)
            if timestamp == prev_timestamp:
                # We have two timestamps possibly differing in seconds only. Enhydris
                # can't handle that.
                continue
            prev_timestamp = timestamp
            result += f'{timestamp.isoformat()},{r["mvalue"]},\n'
        return StringIO(result)

    def _get_start_date(self, sensor_id, timeseries_end_date):
        if timeseries_end_date is not None:
            start_date = timeseries_end_date + dt.timedelta(minutes=1)
        else:
            start_date = dt.datetime(1990, 1, 1)
        return start_date

    def make_request(self, method, url, *args, **kwargs):
        if "data" in kwargs:
            kwargs.setdefault("headers", {})
            kwargs["headers"]["content-type"] = "application/json"
            kwargs["data"] = json.dumps(kwargs["data"])
        response = requests.request(method, url, *args, **kwargs)
        response.raise_for_status()
        data = response.json()
        if "code" not in data:
            raise ErrorResponse('Missing "code"', response=response)
        if int(data["code"]) != 200:
            raise ErrorResponse(
                f'{data["code"]} {data.get("message", "")}', response=response
            )
        return data


class LoginDataForm(forms.Form):
    email = forms.EmailField()
    api_key = forms.CharField()

    def clean(self):
        cleaned_data = super().clean()
        try:
            email = cleaned_data.get("email")
            api_key = cleaned_data.get("api_key")
            meteoview2_api_client = Meteoview2ApiClient(email, api_key)
            meteoview2_api_client.login()
        except requests.RequestException as e:
            s = str(e)
            error_message = _("Could not login to meteoview; the error was: %s") % s
            raise forms.ValidationError(error_message)
        return cleaned_data


class ChooseStationForm(forms.Form):
    station = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        meteoview2_api_client = Meteoview2ApiClient(
            self.initial["email"], self.initial["api_key"]
        )
        meteoview2_api_client.login()
        stations = meteoview2_api_client.get_stations()
        choices = []
        for key in stations:
            station = stations[key]
            code = station["code"]
            title = station["title"]
            choices.append((code, f"{title} ({code})"))
        self.fields["station"].choices = choices


class ChooseSensorForm(forms.Form):
    def __init__(self, *args, **kwargs):
        from enhydris import models

        super().__init__(*args, **kwargs)
        configuration = kwargs["initial"]
        station_id = configuration["station_id"]
        station_code = configuration["station"]
        meteoview2_api_client = Meteoview2ApiClient(
            configuration["email"], configuration["api_key"]
        )
        meteoview2_api_client.login()
        sensors = meteoview2_api_client.get_sensors(station_code)
        station = models.Station.objects.get(pk=station_id)
        timeseries_groups = station.timeseriesgroup_set
        choices = [("", _("Ignore this sensor"))]
        choices.extend(
            [(tg.id, f"{tg.name} ({tg.id})") for tg in timeseries_groups.all()]
        )
        for sensor in sensors:
            sensor_id = sensor["id"]
            title = sensor["title"]
            self.fields[f"sensor_{sensor_id}"] = forms.ChoiceField(
                label=_(
                    "To which Enhydris time series does sensor "
                    '"{title}" ({sensor_id}) correspond?'
                ).format(title=title, sensor_id=sensor_id),
                choices=choices,
                required=False,
            )


class Telemetry(TelemetryBase):
    name = "Metrica MeteoView2"
    wizard_steps = [LoginDataForm, ChooseStationForm, ChooseSensorForm]

    def fetch(self):
        self._setup_api_client()
        self._fetch_sensors()

    def _setup_api_client(self):
        configuration = self.telemetry_model.configuration
        email = configuration["email"]
        api_key = configuration["api_key"]
        self.meteoview2_api_client = Meteoview2ApiClient(email, api_key)
        self.meteoview2_api_client.login()

    def _fetch_sensors(self):
        configuration = self.telemetry_model.configuration
        for key in configuration:
            if not key.startswith("sensor_"):
                continue
            sensor_id = key.partition("_")[2]
            if configuration[key]:
                timeseries_group_id = int(configuration[key])
                self._fetch_sensor(sensor_id, timeseries_group_id)

    def _fetch_sensor(self, sensor_id, timeseries_group_id):
        from enhydris.models import Timeseries

        timeseries, created = Timeseries.objects.get_or_create(
            timeseries_group_id=timeseries_group_id, type=Timeseries.INITIAL
        )
        measurements = self.meteoview2_api_client.get_measurements(
            sensor_id=sensor_id, timeseries_end_date=timeseries.end_date
        )
        timeseries.append_data(measurements)
