from django import forms

from enhydris.telemetry.models import Telemetry


class CommonDataForm(forms.ModelForm):
    class Meta:
        model = Telemetry
        fields = [
            "type",
            "data_time_zone",
            "fetch_interval_minutes",
            "fetch_offset_minutes",
            "fetch_offset_time_zone",
        ]
