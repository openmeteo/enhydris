import mimetypes
import os
from io import StringIO
from wsgiref.util import FileWrapper

from django.conf import settings
from django.contrib.gis.db.models import Extent
from django.contrib.gis.geos import Polygon
from django.db import IntegrityError
from django.db.models import Count, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

import iso8601
import pandas as pd
from htimeseries import HTimeseries

from enhydris import models

from . import serializers
from .csv import prepare_csv
from .permissions import CanCreateStation, CanEditOrReadOnly


class StationViewSet(ModelViewSet):
    serializer_class = serializers.StationSerializer

    def get_permissions(self):
        pc = [CanCreateStation] if self.action == "create" else [CanEditOrReadOnly]
        return [x() for x in pc]

    def _get_unsorted_queryset(self, distinct=True, **kwargs):
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

    def get_queryset(self, **kwargs):
        result = self._get_unsorted_queryset(**kwargs)
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
            Q(name__icontains=search_term)
            | Q(short_name__icontains=search_term)
            | Q(remarks__icontains=search_term)
            | Q(water_basin__name__icontains=search_term)
            | Q(water_division__name__icontains=search_term)
            | Q(political_division__name__icontains=search_term)
            | Q(owner__organization__name__icontains=search_term)
            | Q(owner__person__first_name__icontains=search_term)
            | Q(owner__person__last_name__icontains=search_term)
            | Q(timeseries__remarks__icontains=search_term)
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
            | Q(owner__person__first_name__icontains=value)
            | Q(owner__person__last_name__icontains=value)
        )

    def _filter_by_type(self, queryset, value):
        return queryset.filter(stype__descr__icontains=value)

    def _filter_by_water_division(self, queryset, value):
        return queryset.filter(water_division__name__icontains=value)

    def _filter_by_water_basin(self, queryset, value):
        return queryset.filter(water_basin__name__icontains=value)

    def _filter_by_variable(self, queryset, value):
        return queryset.filter(timeseries__variable__descr__icontains=value)

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
                            WHERE LOWER(name) LIKE LOWER('%%{}%%'))
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
        queryset = self._get_unsorted_queryset(distinct=False)
        extent = queryset.aggregate(Extent("point"))["point__extent"]
        if extent is None:
            extent = settings.ENHYDRIS_MAP_DEFAULT_VIEWPORT[:]
        else:
            extent = list(extent)

        # Increase extent if it's too small
        min_viewport = settings.ENHYDRIS_MIN_VIEWPORT_IN_DEGS
        dx = abs(extent[2] - extent[0])
        if dx < min_viewport:
            extent[2] += 0.5 * (min_viewport - dx)
            extent[0] -= 0.5 * (min_viewport - dx)
        dy = abs(extent[3] - extent[1])
        if dy < min_viewport:
            extent[3] += 0.5 * (min_viewport - dy)
            extent[1] -= 0.5 * (min_viewport - dy)

        return extent

    def list(self, request):
        response = super().list(request)
        response.data["bounding_box"] = self._get_bounding_box()
        return response

    @action(detail=False, methods=["get"])
    def csv(self, request):
        data = prepare_csv(self.get_queryset())
        response = HttpResponse(data, content_type="application/zip")
        response["Content-Disposition"] = "attachment; filename=data.zip"
        response["Content-Length"] = len(data)
        return response


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

    def get_queryset(self):
        return models.GentityAltCode.objects.filter(
            gentity_id=self.kwargs["station_id"]
        )


class GentityEventViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.GentityEventSerializer

    def get_queryset(self):
        return models.GentityEvent.objects.filter(gentity_id=self.kwargs["station_id"])


class OverseerViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.OverseerSerializer

    def get_queryset(self):
        return models.Overseer.objects.filter(station_id=self.kwargs["station_id"])


class InstrumentViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.InstrumentSerializer

    def get_queryset(self):
        return models.Instrument.objects.filter(station_id=self.kwargs["station_id"])


class GentityFileViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.GentityFileSerializer

    def get_queryset(self):
        return models.GentityFile.objects.filter(gentity_id=self.kwargs["station_id"])

    @action(detail=True, methods=["get"])
    def content(self, request, pk=None, *, station_id):
        gfile = self.get_object()
        try:
            gfile_content_file = gfile.content.file
            filename = gfile_content_file.name
            wrapper = FileWrapper(open(filename, "rb"))
        except (ValueError, IOError):
            raise Http404
        download_name = gfile.content.name.split("/")[-1]
        content_type = mimetypes.guess_type(filename)[0]
        response = HttpResponse(content_type=content_type)
        response["Content-Length"] = os.path.getsize(filename)
        response["Content-Disposition"] = "attachment; filename=" + download_name

        for chunk in wrapper:
            response.write(chunk)

        return response


class TimeseriesViewSet(ModelViewSet):
    queryset = models.Timeseries.objects.all()
    serializer_class = serializers.TimeseriesSerializer
    permission_classes = (CanEditOrReadOnly,)

    def get_queryset(self):
        return models.Timeseries.objects.filter(gentity_id=self.kwargs["station_id"])

    def create(self, request, *args, **kwargs):
        """Redefine create, checking permissions and gentity_id.

        Django-rest-framework does not do object-level permission when
        creating a new object, so we have to completely customize the create
        method. In addition, we check that the gentity_id specified in the data
        is the same as the station_id in the URL.
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
        if not request.user.is_authenticated:
            return Response("Unauthorized", status=status.HTTP_401_UNAUTHORIZED)
        if not request.user.has_perm("enhydris.change_station", station):
            return Response("Forbidden", status=status.HTTP_403_FORBIDDEN)

        # Check the correctness of gentity_id
        if str(gentity_id) != self.kwargs["station_id"]:
            return Response("Wrong gentity_id", status=status.HTTP_400_BAD_REQUEST)

        # All checks passed, call inherited method to do the actual work.
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=["get", "post"])
    def data(self, request, pk=None, *, station_id):
        if request.method == "GET":
            return self._get_data(request, pk)
        elif request.method == "POST":
            return self._post_data(request, pk)

    @action(detail=True, methods=["get"])
    def bottom(self, request, pk=None, *, station_id):
        ts = get_object_or_404(models.Timeseries, pk=pk)
        response = HttpResponse(content_type="text/plain")
        response.write(ts.get_last_line())
        return response

    def _get_data(self, request, pk, format=None):
        timeseries = get_object_or_404(models.Timeseries, pk=int(pk))
        self.check_object_permissions(request, timeseries)

        tz = timeseries.time_zone.as_tzinfo
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        start_date = self._get_date_from_string(start_date, tz)
        end_date = self._get_date_from_string(end_date, tz)

        # The time series data are naive, so we also make start_date and end_date naive.
        if start_date:
            start_date = start_date.replace(tzinfo=None)
        if end_date:
            end_date = end_date.replace(tzinfo=None)

        ahtimeseries = timeseries.get_data(start_date=start_date, end_date=end_date)
        response = HttpResponse(content_type="text/plain; charset=utf-8")
        if request.GET.get("fmt", "").lower() == "hts":
            fmt = HTimeseries.FILE
        else:
            fmt = HTimeseries.TEXT
        ahtimeseries.write(response, format=fmt)
        return response

    def _post_data(self, request, pk, format=None):
        try:
            atimeseries = get_object_or_404(models.Timeseries, pk=int(pk))
            self.check_object_permissions(request, atimeseries)
            atimeseries.append_data(StringIO(request.data["timeseries_records"]))
            return HttpResponse(status=status.HTTP_204_NO_CONTENT)
        except (IntegrityError, iso8601.ParseError) as e:
            return HttpResponse(
                status=status.HTTP_400_BAD_REQUEST,
                content=str(e),
                content_type="text/plain",
            )

    def _get_date_from_string(self, adate, tz):
        if not adate:
            return None
        result = iso8601.parse_date(adate, default_timezone=tz)
        if result.isoformat() < pd.Timestamp.min.isoformat():
            result = pd.Timestamp.min
        if result.isoformat() > pd.Timestamp.max.isoformat():
            result = pd.Timestamp.max
        return result
