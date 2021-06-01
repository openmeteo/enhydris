from django.conf import settings
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView, ListView, RedirectView, View

from . import forms, models
from .views_common import StationListViewMixin, ensure_extent_is_large_enough


class StationList(StationListViewMixin, ListView):
    template_name = "enhydris/station_list/main.html"
    model = models.Station

    def get_paginate_by(self, queryset):
        return getattr(settings, "ENHYDRIS_STATIONS_PER_PAGE", 100)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        parms = self.request.GET.copy()
        context["query_string_parms"] = parms.pop("page", True) and parms.urlencode()
        return context

    def render_to_response(self, *args, **kwargs):
        self.request.map_viewport = self._get_bounding_box()
        return super().render_to_response(*args, **kwargs)


class MapWithSingleStationBaseView(DetailView):
    def render_to_response(self, *args, **kwargs):
        try:
            p = self.object.geom
        except AttributeError:
            p = self.object.gentity.geom
        map_extent = [p.x, p.y, p.x, p.y]
        ensure_extent_is_large_enough(map_extent)
        self.request.map_viewport = map_extent
        return super().render_to_response(*args, **kwargs)


class StationDetail(MapWithSingleStationBaseView):
    model = models.Station
    template_name = "enhydris/station_detail/main.html"


class StationEdit(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse("admin:enhydris_station_change", args=(kwargs["pk"],))


class TimeseriesGroupDetail(MapWithSingleStationBaseView):
    model = models.TimeseriesGroup
    template_name = "enhydris/timeseries_group_detail/main.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["download_data_form"] = forms.DownloadDataForm(
            timeseries_group=self.object
        )
        return context


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
