from django import forms
from django.utils.translation import ugettext_lazy as _

from enhydris import models

DOWNLOAD_FORMATS = [
    ("csv", "CSV"),
    ("hts2", "Hydrognomon 4"),
    ("hts", _("Latest HTS")),
]


class DownloadDataForm(forms.Form):
    station_id = forms.IntegerField(widget=forms.HiddenInput)
    timeseries_group_id = forms.IntegerField(widget=forms.HiddenInput)
    timeseries_id = forms.ChoiceField(choices=[], widget=forms.RadioSelect)
    format = forms.ChoiceField(choices=DOWNLOAD_FORMATS, widget=forms.RadioSelect)

    def __init__(self, form_data=None, timeseries_group=None):
        super().__init__(form_data)
        if timeseries_group:
            self.timeseries_group = timeseries_group
            self.fields["timeseries_id"].choices = self.get_choices()
            self.fields["timeseries_group_id"].initial = self.timeseries_group.id
            self.fields["station_id"].initial = self.timeseries_group.gentity.id

    def get_choices(self):
        available_timeseries = self.timeseries_group.timeseries_set.all()
        return [(timeseries.id, str(timeseries)) for timeseries in available_timeseries]

    def clean_timeseries_group_id(self):
        tgid = self.cleaned_data["timeseries_group_id"]
        try:
            self.timeseries_group = models.TimeseriesGroup.objects.get(id=tgid)
        except models.TimeseriesGroup.DoesNotExist:
            raise forms.ValidationError("Invalid TimeseriesGroup")
        self.fields["timeseries_id"].choices = self.get_choices()
        return tgid
