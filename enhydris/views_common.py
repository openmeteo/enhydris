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
        queryset = models.Station.objects.all()

        # Apply SITE_STATION_FILTER
        if len(settings.ENHYDRIS_SITE_STATION_FILTER) > 0:
            queryset = queryset.filter(**settings.ENHYDRIS_SITE_STATION_FILTER)

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

        # Create a copy of sort_order with duplicates and nonexistent fields removed
        result = []
        fields = [x.name for x in models.Station._meta.get_fields()]
        fields_seen = set()
        for item in sort_order:
            field = item[1:] if item[0] == "-" else item
            if field in fields_seen or field not in fields:
                continue
            result.append(item)
            fields_seen.add(field)

        return result

    def _refine_queryset(self, queryset, search_term):
        """Return the queryset refined according to search_term.

        search_term can either be a word or a "name:value" string, such as
        political_division:greece.
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
            | Q(short_name__unaccent__icontains=search_term)
            | Q(remarks__unaccent__icontains=search_term)
            | Q(water_basin__name__unaccent__icontains=search_term)
            | Q(water_division__name__unaccent__icontains=search_term)
            | Q(political_division__name__unaccent__icontains=search_term)
            | Q(owner__organization__name__unaccent__icontains=search_term)
            | Q(owner__person__first_name__unaccent__icontains=search_term)
            | Q(owner__person__last_name__unaccent__icontains=search_term)
            | Q(timeseries__remarks__unaccent__icontains=search_term)
        )

    def _specific_filter(self, queryset, name, value):
        """Return the queryset refined according to the specified name and value.

        E.g. name can be "political_division" and value can be "greece". Value can also
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

    def _filter_by_water_division(self, queryset, value):
        return queryset.filter(water_division__name__unaccent__icontains=value)

    def _filter_by_water_basin(self, queryset, value):
        return queryset.filter(water_basin__name__unaccent__icontains=value)

    def _filter_by_variable(self, queryset, value):
        return queryset.filter(
            timeseries__variable__in=models.Variable.objects.filter(
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
        return queryset.filter(geometry__contained=geom)

    def _filter_by_ts_only(self, queryset, value):
        return queryset.annotate(tsnum=Count("timeseries")).exclude(tsnum=0)

    def _filter_by_ts_has_years(self, queryset, value):
        try:
            years = [int(y) for y in value.split(",")]
        except ValueError:
            raise Http404
        return queryset.extra(
            where=[
                " AND ".join(
                    [
                        "enhydris_station.gpoint_ptr_id IN "
                        "(SELECT t.gentity_id FROM enhydris_timeseries t "
                        "WHERE " + str(year) + " BETWEEN "
                        "EXTRACT(YEAR FROM t.start_date_utc) AND "
                        "EXTRACT(YEAR FROM t.end_date_utc))"
                        for year in years
                    ]
                )
            ]
        )

    def _filter_by_political_division(self, queryset, value):
        return queryset.extra(
            where=[
                """
                enhydris_station.gpoint_ptr_id IN (
                SELECT id FROM enhydris_gentity WHERE political_division_id IN (
                    WITH RECURSIVE mytable(garea_ptr_id) AS (
                        SELECT garea_ptr_id FROM enhydris_politicaldivision
                        WHERE garea_ptr_id IN (
                            SELECT id FROM enhydris_gentity
                            WHERE LOWER(UNACCENT(name)) LIKE LOWER(UNACCENT('%%{}%%')))
                    UNION ALL
                        SELECT pd.garea_ptr_id
                        FROM enhydris_politicaldivision pd, mytable
                        WHERE pd.parent_id=mytable.garea_ptr_id
                    )
                    SELECT g.id FROM enhydris_gentity g, mytable
                    WHERE g.id=mytable.garea_ptr_id))
                """.format(
                    value, value
                )
            ]
        )

    _filter_by_country = _filter_by_political_division  # synonym

    def _get_bounding_box(self):
        queryset = self._get_unsorted_undistinct_queryset()
        extent = queryset.aggregate(Extent("geometry"))["geometry__extent"]
        if extent is None:
            extent = settings.ENHYDRIS_MAP_DEFAULT_VIEWPORT[:]
        else:
            extent = list(extent)

        ensure_extent_is_large_enough(extent)

        return extent
