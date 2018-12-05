from io import StringIO

from django.conf import settings
from django.contrib.gis.geos import Polygon
from django.db import IntegrityError
from django.db.models import Count, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

import iso8601
import pd2hts

from enhydris import models

from . import serializers
from .permissions import CanCreateStation, CanEditOrReadOnly


class Tsdata(APIView):
    """
    Take a timeseries id and return the actual timeseries data to the client,
    or update a time series with new records.
    """

    permission_classes = (CanEditOrReadOnly,)

    def get(self, request, pk, format=None):
        try:
            timeseries = models.Timeseries.objects.get(pk=int(pk))
            self.check_object_permissions(request, timeseries)
            response = HttpResponse(content_type="text/plain")
            pd2hts.write(timeseries.get_data(), response)
            return response
        except models.Timeseries.DoesNotExist:
            raise Http404

    def post(self, request, pk, format=None):
        try:
            atimeseries = models.Timeseries.objects.get(pk=int(pk))
            self.check_object_permissions(request, atimeseries)
            atimeseries.append_data(StringIO(request.data["timeseries_records"]))
            return HttpResponse(status=status.HTTP_204_NO_CONTENT)
        except models.Timeseries.DoesNotExist:
            raise Http404
        except (IntegrityError, iso8601.ParseError) as e:
            return HttpResponse(
                status=status.HTTP_400_BAD_REQUEST,
                content=str(e),
                content_type="text/plain",
            )


class TimeseriesList(generics.ListCreateAPIView):
    queryset = models.Timeseries.objects.all()
    serializer_class = serializers.TimeseriesSerializer
    permission_classes = (CanEditOrReadOnly,)

    def post(self, request, *args, **kwargs):
        """Redefine post, checking permissions.

        Django-rest-framework does not do object-level permission when
        creating a new object, so we have to completely customize the post
        method. Maybe there's a better way, such as using a mixin for the
        functionality below (especially when the API is extended to include
        other types as well).
        """
        # Get the data
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Check permissions
        try:
            gentity_id = int(serializer.get_initial()["gentity"])
        except ValueError:
            raise Http404
        station = get_object_or_404(models.Station, id=gentity_id)
        if not request.user.is_authenticated():
            return Response("Unauthorized", status=status.HTTP_401_UNAUTHORIZED)
        if not request.user.has_perm("enhydris.change_station", station):
            return Response("Forbidden", status=status.HTTP_403_FORBIDDEN)

        return super(TimeseriesList, self).post(request, *args, **kwargs)


class TimeseriesDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Timeseries.objects.all()
    serializer_class = serializers.TimeseriesSerializer
    permission_classes = (CanEditOrReadOnly,)


class StationListPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000


class StationViewSet(ModelViewSet):
    serializer_class = serializers.StationSerializer
    pagination_class = StationListPagination

    def get_permissions(self):
        pc = [CanCreateStation] if self.action == "create" else [CanEditOrReadOnly]
        return [x() for x in pc]

    def get_queryset(self, distinct=True, **kwargs):
        result = models.Station.objects.all()

        # Apply SITE_STATION_FILTER
        if len(settings.ENHYDRIS_SITE_STATION_FILTER) > 0:
            result = result.filter(**settings.ENHYDRIS_SITE_STATION_FILTER)

        # Perform the search specified by the q parameter
        query_string = self.request.GET.get("q", "")
        for search_term in query_string.split():
            result = self._refine_queryset(result, search_term)

        # By default, only return distinct rows. We provide a way to
        # override this by calling with distinct=False, because distinct()
        # is incompatible with some things (namely extent()).
        if distinct:
            result = result.distinct()

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
            Q(name__icontains=search_term)
            | Q(name_alt__icontains=search_term)
            | Q(short_name__icontains=search_term)
            | Q(short_name_alt__icontains=search_term)
            | Q(remarks__icontains=search_term)
            | Q(remarks_alt__icontains=search_term)
            | Q(water_basin__name__icontains=search_term)
            | Q(water_basin__name_alt__icontains=search_term)
            | Q(water_division__name__icontains=search_term)
            | Q(water_division__name_alt__icontains=search_term)
            | Q(political_division__name__icontains=search_term)
            | Q(political_division__name_alt__icontains=search_term)
            | Q(owner__organization__name__icontains=search_term)
            | Q(owner__person__first_name__icontains=search_term)
            | Q(owner__person__last_name__icontains=search_term)
            | Q(timeseries__remarks__icontains=search_term)
            | Q(timeseries__remarks_alt__icontains=search_term)
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
            Q(owner__organization__name__icontains=value)
            | Q(owner__organization__name_alt__icontains=value)
            | Q(owner__person__first_name__icontains=value)
            | Q(owner__person__first_name_alt__icontains=value)
            | Q(owner__person__last_name_alt__icontains=value)
            | Q(owner__person__last_name__icontains=value)
        )

    def _filter_by_type(self, queryset, value):
        return queryset.filter(
            Q(stype__descr__icontains=value) | Q(stype__descr_alt__icontains=value)
        )

    def _filter_by_water_division(self, queryset, value):
        return queryset.filter(
            Q(water_division__name__icontains=value)
            | Q(water_division__name_alt__icontains=value)
        )

    def _filter_by_water_basin(self, queryset, value):
        return queryset.filter(
            Q(water_basin__name__icontains=value)
            | Q(water_basin__name_alt__icontains=value)
        )

    def _filter_by_variable(self, queryset, value):
        return queryset.filter(
            Q(timeseries__variable__descr__icontains=value)
            | Q(timeseries__variable__descr_alt__icontains=value)
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
        return queryset.filter(point__contained=geom)

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
                            WHERE LOWER(name) LIKE LOWER('%%{}%%')
                            OR LOWER(name_alt) LIKE LOWER('%%{}%%'))
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


class WaterDivisionViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.WaterDivisionSerializer
    queryset = models.WaterDivision.objects.all()


class GentityAltCodeTypeViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.GentityAltCodeTypeSerializer
    queryset = models.GentityAltCodeType.objects.all()


class OrganizationViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.OrganizationSerializer
    queryset = models.Organization.objects.all()


class PersonViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.PersonSerializer
    queryset = models.Person.objects.all()


class StationTypeViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.StationTypeSerializer
    queryset = models.StationType.objects.all()


class TimeZoneViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.TimeZoneSerializer
    queryset = models.TimeZone.objects.all()


class PoliticalDivisionViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.PoliticalDivisionSerializer
    queryset = models.PoliticalDivision.objects.all()


class IntervalTypeViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.IntervalTypeSerializer
    queryset = models.IntervalType.objects.all()


class FileTypeViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.FileTypeSerializer
    queryset = models.FileType.objects.all()


class EventTypeViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.EventTypeSerializer
    queryset = models.EventType.objects.all()


class InstrumentTypeViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.InstrumentTypeSerializer
    queryset = models.InstrumentType.objects.all()


class WaterBasinViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.WaterBasinSerializer
    queryset = models.WaterBasin.objects.all()


class TimeStepViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.TimeStepSerializer
    queryset = models.TimeStep.objects.all()


class VariableViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.VariableSerializer
    queryset = models.Variable.objects.all()


class UnitOfMeasurementViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.UnitOfMeasurementSerializer
    queryset = models.UnitOfMeasurement.objects.all()


class GentityAltCodeViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.GentityAltCodeSerializer
    queryset = models.GentityAltCode.objects.all()


class GentityFileViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.GentityFileSerializer
    queryset = models.GentityFile.objects.all()


class GentityEventViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.GentityEventSerializer
    queryset = models.GentityEvent.objects.all()


class OverseerViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.OverseerSerializer
    queryset = models.Overseer.objects.all()


class InstrumentViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.InstrumentSerializer
    queryset = models.Instrument.objects.all()
