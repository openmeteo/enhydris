from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import View

from enhydris import forms


class DownloadData(View):
    def get(self, *args, **kwargs):
        self.form = forms.DownloadDataForm(self.request.GET)
        if self.form.is_valid():
            return self._get_redirect_response(*args, **kwargs)
        else:
            raise Http404

    def _get_redirect_response(self, *args, **kwargs):
        fields = {
            "pk": self.form.cleaned_data["timeseries_id"],
            "timeseries_group_id": self.form.cleaned_data["timeseries_group_id"],
            "station_id": self.form.cleaned_data["station_id"],
        }
        fmt = self.form.cleaned_data["format"]
        url = reverse("timeseries-data", kwargs=fields) + f"?fmt={fmt}"
        return HttpResponseRedirect(url)
