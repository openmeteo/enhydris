from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.views.generic import DetailView

from enhydris.models import Station, TimeseriesGroup
from enhydris.views_common import ensure_extent_is_large_enough

if TYPE_CHECKING:
    MapWithSingleStationBaseViewBase = DetailView[Station | TimeseriesGroup]
else:
    MapWithSingleStationBaseViewBase = DetailView


class MapWithSingleStationBaseView(MapWithSingleStationBaseViewBase):
    def render_to_response(self, *args: Any, **kwargs: Any):
        if isinstance(self.object, Station):
            p = self.object.geom
        else:
            p = self.object.gentity.geom
        map_extent: list[float] = [p.x, p.y, p.x, p.y]  # type: ignore
        ensure_extent_is_large_enough(map_extent)
        self.request.map_viewport = map_extent  # type: ignore
        return super().render_to_response(*args, **kwargs)
