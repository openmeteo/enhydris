from django.conf import settings
from django.urls import reverse
from django.views.generic import ListView, RedirectView

from enhydris import models
from enhydris.views_common import StationListViewMixin

from .utils import MapWithSingleStationBaseView


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


class StationDetail(MapWithSingleStationBaseView):
    model = models.Station
    template_name = "enhydris/station_detail/main.html"

    def get_queryset(self):
        return models.Station.on_site.all()


class StationEdit(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse("admin:enhydris_station_change", args=(kwargs["pk"],))
