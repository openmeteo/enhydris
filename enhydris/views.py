from django.conf import settings
from django.urls import reverse
from django.views.generic import DetailView, ListView, RedirectView

from . import models
from .views_common import StationListViewMixin, ensure_extent_is_large_enough


class StationList(StationListViewMixin, ListView):
    template_name = "enhydris/station_list.html"
    model = models.Station

    def get_paginate_by(self, queryset):
        return getattr(settings, "ENHYDRIS_STATIONS_PER_PAGE", 100)

    def render_to_response(self, *args, **kwargs):
        self.request.map_viewport = self._get_bounding_box()
        return super().render_to_response(*args, **kwargs)


class StationDetail(DetailView):
    model = models.Station
    template_name = "enhydris/station_detail.html"

    def render_to_response(self, *args, **kwargs):
        p = self.object.point
        map_extent = [p.x, p.y, p.x, p.y]
        ensure_extent_is_large_enough(map_extent)
        self.request.map_viewport = map_extent
        return super().render_to_response(*args, **kwargs)


class StationEdit(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse("admin:enhydris_station_change", args=(kwargs["pk"],))
