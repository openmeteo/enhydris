from django.conf import settings
from django.views.generic import ListView

from . import models
from .views_common import StationListViewMixin


class StationListView(StationListViewMixin, ListView):
    template_name = "enhydris/station_list.html"
    model = models.Station

    def get_paginate_by(self, queryset):
        return getattr(settings, "ENHYDRIS_STATIONS_PER_PAGE", 100)

    def render_to_response(self, *args, **kwargs):
        self.request.map_viewport = self._get_bounding_box()
        return super().render_to_response(*args, **kwargs)
