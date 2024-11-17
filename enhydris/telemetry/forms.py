from django import forms
from django.utils.translation import gettext_lazy as _

from enhydris.telemetry import TelemetryError
from enhydris.telemetry.models import Telemetry, timezone_choices


class FormBase(forms.Form):
    def __init__(self, *args, **kwargs):
        self.driver = kwargs.pop("driver")
        self.station = kwargs.pop("station")
        super().__init__(*args, **kwargs)


class EssentialDataForm(FormBase, forms.ModelForm):
    class Meta:
        model = Telemetry
        fields = [
            "type",
            "fetch_interval_minutes",
            "fetch_offset_minutes",
        ]


class ConnectionDataForm(FormBase):
    device_locator = forms.CharField(required=False)
    data_timezone = forms.ChoiceField(choices=timezone_choices)
    username = forms.CharField()
    password = forms.CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = self.driver.username_label
        self.fields["password"].label = self.driver.password_label
        self.fields["device_locator"].label = self.driver.device_locator_label
        self.fields["device_locator"].help_text = self.driver.device_locator_help_text
        if self.driver.hide_device_locator:
            self.fields["device_locator"].widget = forms.HiddenInput()
        if self.driver.hide_data_timezone:
            self.fields["data_timezone"].widget = forms.HiddenInput(
                attrs={"value": "UTC"}
            )
            self.fields["data_timezone"].required = False

    def clean(self):
        cleaned_data = super().clean()
        try:
            telemetry = Telemetry(
                username=cleaned_data.get("username"),
                password=cleaned_data.get("password"),
                device_locator=cleaned_data.get("device_locator"),
            )
            with self.driver(telemetry):
                pass  # Just testing that connection does not raise error
        except TelemetryError as e:
            raise forms.ValidationError(str(e))
        return cleaned_data


class ChooseStationForm(FormBase):
    remote_station_id = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.initial["username"]
        passwd = self.initial["password"]
        loc = self.initial["device_locator"]
        telemetry = Telemetry(username=user, password=passwd, device_locator=loc)
        with self.driver(telemetry) as api_client:
            stations = api_client.get_stations()
        choices = []
        for key, value in stations.items():
            choices.append((key, f"{value} ({key})"))
        self.fields["remote_station_id"].choices = choices


class ChooseSensorForm(FormBase):
    def __init__(self, *args, **kwargs):
        from enhydris import models

        super().__init__(*args, **kwargs)
        telemetry = Telemetry(
            username=self.initial["username"],
            password=self.initial["password"],
            device_locator=self.initial["device_locator"],
            station=self.station,
            remote_station_id=self.initial["remote_station_id"],
        )
        with self.driver(telemetry) as api_client:
            sensors = api_client.get_sensors()
        station = models.Station.objects.get(pk=self.station.id)
        timeseries_groups = station.timeseriesgroup_set
        choices = [("", _("Ignore this sensor"))]
        choices.extend(
            [(tg.id, f"{tg.name} ({tg.id})") for tg in timeseries_groups.all()]
        )
        for sensor_id, sensor_name in sensors.items():
            self.fields[f"sensor_{sensor_id}"] = forms.ChoiceField(
                label=_(
                    "To which Enhydris time series does sensor "
                    '"{sensor_name}" ({sensor_id}) correspond?'
                ).format(sensor_name=sensor_name, sensor_id=sensor_id),
                choices=choices,
                required=False,
            )

    def clean(self):
        cleaned_data = super().clean()
        seen_timeseries_group_ids = set()
        for sensor_id, timeseries_group_id in cleaned_data.items():
            if timeseries_group_id in seen_timeseries_group_ids:
                raise forms.ValidationError(
                    "A given time series may be specified for only one sensor"
                )
            seen_timeseries_group_ids.add(timeseries_group_id)
        return cleaned_data
