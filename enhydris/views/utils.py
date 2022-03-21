from django.views.generic import DetailView

from enhydris.views_common import ensure_extent_is_large_enough


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
