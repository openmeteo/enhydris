"""Functionality common to API views and old-fashioned views.

   Unit tested mostly in the API tests.
"""
from django.conf import settings
from django.contrib.gis.db.models import Extent
from django.contrib.gis.geos import Polygon
from django.db.models import Count, Q
from django.http import Http404

from . import models


def ensure_extent_is_large_enough(extent):
    min_viewport = settings.ENHYDRIS_MAP_MIN_VIEWPORT_SIZE
    dx = abs(extent[2] - extent[0])
    if dx < min_viewport:
        extent[2] += 0.5 * (min_viewport - dx)
        extent[0] -= 0.5 * (min_viewport - dx)
    dy = abs(extent[3] - extent[1])
    if dy < min_viewport:
        extent[3] += 0.5 * (min_viewport - dy)
        extent[1] -= 0.5 * (min_viewport - dy)


class StationListViewMixin:
    """Functionality common to StationList views.

    There's a station list api view and a station list normal view. This mixin provides
    functionality common to both.
    """

    def _get_unsorted_undistinct_queryset(self, **kwargs):
        queryset = models.Station.on_site.all()

        # If a gentity_id query parameter is specified, ignore all the rest
        try:
            gentity_id = int(self.request.GET.get("gentity_id", "0"))
            if gentity_id:
                return queryset.filter(id=gentity_id)
        except ValueError:
            raise Http404

        # Perform the search specified by the q parameter
        query_string = self.request.GET.get("q", "")
        for search_term in query_string.split():
            queryset = self._refine_queryset(queryset, search_term)

        # Also filter by the bbox query parameter, if there is one
        bbox = self.request.GET.get("bbox")
        if bbox:
            queryset = self._filter_by_bbox(queryset, bbox)

        return queryset

    def get_queryset(self, **kwargs):
        result = self._get_unsorted_undistinct_queryset(**kwargs).distinct()
        sort_order = self._get_sort_order()
        self.request.session["sort"] = sort_order
        if sort_order:
            result = result.order_by(*sort_order)
        return result

    def _get_sort_order(self):
        """Return sort_order as a list.

        Gets sort order from the request parameters, otherwise from request.session,
        otherwise it's the default, ['name']. Removes duplicate field occurences from
        the list.
        """
        # Get sort order from query parameters
        sort_order = self.request.GET.getlist("sort")

        # If empty, get sort order from session
        if not sort_order:
            sort_order = self.request.session.get("sort", ["name"])

        # Create a copy of sort_order with duplicates and invalid fields removed
        result = []
        fields = [x.name for x in models.Station._meta.get_fields()]
        fields_seen = set()
        for item in sort_order:
            if not item:
                continue
            field = item[1:] if item[0] == "-" else item
            if field in fields_seen or field not in fields:
                continue
            result.append(item)
            fields_seen.add(field)

        return result

    def _refine_queryset(self, queryset, search_term):
        """Return the queryset refined according to search_term.

        search_term can either be a word or a "name:value" string, such as
        variable:temperature.
        """
        if ":" not in search_term:
            return self._general_filter(queryset, search_term)
        else:
            name, dummy, value = search_term.partition(":")
            return self._specific_filter(queryset, name, value)

    def _general_filter(self, queryset, search_term):
        """Return the queryset refined according to search_term.

        search_term is a simple word searched in various places.
        """
        return queryset.filter(
            Q(name__unaccent__icontains=search_term)
            | Q(code__unaccent__icontains=search_term)
            | Q(remarks__unaccent__icontains=search_term)
            | Q(owner__organization__name__unaccent__icontains=search_term)
            | Q(owner__person__first_name__unaccent__icontains=search_term)
            | Q(owner__person__last_name__unaccent__icontains=search_term)
            | Q(timeseriesgroup__remarks__unaccent__icontains=search_term)
        )

    def _specific_filter(self, queryset, name, value):
        """Return the queryset refined according to the specified name and value.

        E.g. name can be "variable" and value can be "temperature". Value can also
        be an integer, in which case it refers to the id.
        """
        method_name = "_filter_by_" + name
        if not hasattr(self, method_name):
            return queryset
        else:
            method = getattr(self, method_name)
            return method(queryset, value)

    def _filter_by_owner(self, queryset, value):
        return queryset.filter(
            Q(owner__organization__name__unaccent__icontains=value)
            | Q(owner__person__first_name__unaccent__icontains=value)
            | Q(owner__person__last_name__unaccent__icontains=value)
        )

    def _filter_by_variable(self, queryset, value):
        return queryset.filter(
            timeseriesgroup__variable__in=models.Variable.objects.filter(
                translations__descr__unaccent__icontains=value
            )
        )

    def _filter_by_bbox(self, queryset, value):
        try:
            minx, miny, maxx, maxy = [float(i) for i in value.split(",")]
        except ValueError:
            raise Http404
        geom = Polygon(
            ((minx, miny), (minx, maxy), (maxx, maxy), (maxx, miny), (minx, miny)),
            srid=4326,
        )
        return queryset.filter(geom__contained=geom)

    def _filter_by_ts_only(self, queryset, value):
        return queryset.annotate(tsnum=Count("timeseriesgroup")).exclude(tsnum=0)

    def _filter_by_ts_has_years(self, queryset, value):
        try:
            years = [int(y) for y in value.split(",")]
        except ValueError:
            raise Http404
        for year in years:
            queryset = queryset.filter(
                timeseriesgroup__timeseries__timeseriesrecord__timestamp__year=year
            )
        return queryset

    def _filter_by_in(self, queryset, value):
        gareas = models.Garea.objects.filter(
            Q(name__unaccent__icontains=value) | Q(code__unaccent__icontains=value)
        )
        search_terms = None
        for garea in gareas:
            item = Q(geom__contained=garea.geom)
            if search_terms is None:
                search_terms = item
            else:
                search_terms = search_terms | item
        if search_terms is None:
            return queryset.none()
        return queryset.filter(search_terms)

    def _get_bounding_box(self):
        queryset = self._get_unsorted_undistinct_queryset()
        extent = queryset.aggregate(Extent("geom"))["geom__extent"]
        if extent is None:
            extent = settings.ENHYDRIS_MAP_DEFAULT_VIEWPORT[:]
        extent = list(extent)

        ensure_extent_is_large_enough(extent)

        return extent
