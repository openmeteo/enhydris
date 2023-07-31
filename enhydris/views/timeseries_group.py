from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import RedirectView

from enhydris import forms, models

from .utils import MapWithSingleStationBaseView


class TimeseriesGroupDetail(MapWithSingleStationBaseView):
    model = models.TimeseriesGroup
    template_name = "enhydris/timeseries_group_detail/main.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["download_data_form"] = forms.DownloadDataForm(
            timeseries_group=self.object
        )
        context["timeseries_set"] = self._get_timeseries_set()
        return context

    def _get_timeseries_set(self):
        result = []
        for timeseries in self.object.timeseries_set.all():
            if self.request.user.has_perm("enhydris.view_timeseries_data", timeseries):
                result.append(timeseries)
        return result


class OldTimeseriesDetailRedirectView(RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        timeseries = get_object_or_404(models.Timeseries, id=kwargs["pk"])
        timeseries_group = timeseries.timeseries_group
        gentity = timeseries_group.gentity
        return reverse(
            "timeseries_group_detail",
            kwargs={"station_id": gentity.id, "pk": timeseries_group.id},
        )
