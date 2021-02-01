import datetime as dt
import mimetypes
import os
from io import StringIO
from wsgiref.util import FileWrapper

from django.db import IntegrityError
from django.db.models import Prefetch
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

import iso8601
import numpy as np
from htimeseries import HTimeseries

from enhydris import models
from enhydris.views_common import StationListViewMixin

from . import permissions, serializers
from .csv import prepare_csv


class StationViewSet(StationListViewMixin, ModelViewSet):
    serializer_class = serializers.StationSerializer

    def get_permissions(self):
        if self.action == "create":
            pc = [permissions.CanCreateStation]
        else:
            pc = [permissions.CanEditOrReadOnly]
        return [x() for x in pc]

    def list(self, request):
        response = super().list(request)
        response.data["bounding_box"] = self._get_bounding_box()
        return response

    @action(detail=False, methods=["get"])
    def csv(self, request):
        data = prepare_csv(
            self.get_queryset()
            .select_related("owner")
            .prefetch_related(
                Prefetch(
                    "timeseriesgroup_set",
                    queryset=models.TimeseriesGroup.objects.select_related(
                        "variable", "unit_of_measurement", "time_zone"
                    )
                    .prefetch_related("timeseries_set")
                    .order_by("variable__id"),
                )
            )
        )
        response = HttpResponse(data, content_type="application/zip")
        response["Content-Disposition"] = "attachment; filename=data.zip"
        response["Content-Length"] = len(data)
        return response


class GareaViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.GareaSerializer
    queryset = models.Garea.objects.all()


class OrganizationViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.OrganizationSerializer
    queryset = models.Organization.objects.all()


class PersonViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.PersonSerializer
    queryset = models.Person.objects.all()


class TimeZoneViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.TimeZoneSerializer
    queryset = models.TimeZone.objects.all()


class EventTypeViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.EventTypeSerializer
    queryset = models.EventType.objects.all()


class VariableViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.VariableSerializer
    queryset = models.Variable.objects.all()


class UnitOfMeasurementViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.UnitOfMeasurementSerializer
    queryset = models.UnitOfMeasurement.objects.all()


class GentityEventViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.GentityEventSerializer

    def get_queryset(self):
        return models.GentityEvent.objects.filter(gentity_id=self.kwargs["station_id"])


class GentityFileViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.GentityFileSerializer

    def get_permissions(self):
        if self.action == "content":
            pc = [permissions.CanAccessGentityFileContent]
        else:
            pc = [permissions.CanEditOrReadOnly]
        return [x() for x in pc]

    def get_queryset(self):
        return models.GentityFile.objects.filter(gentity_id=self.kwargs["station_id"])

    @action(detail=True, methods=["get"])
    def content(self, request, pk=None, *, station_id):
        gfile = self.get_object()
        self.check_object_permissions(request, gfile)
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


class TimeseriesGroupViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.TimeseriesGroupSerializer

    def get_queryset(self):
        return models.TimeseriesGroup.objects.filter(
            gentity_id=self.kwargs["station_id"]
        )


class TimeseriesViewSet(ModelViewSet):
    CHART_MAX_INTERVALS = 200
    queryset = models.Timeseries.objects.all()
    serializer_class = serializers.TimeseriesSerializer

    def get_permissions(self):
        if self.action in ("data", "bottom", "chart"):
            pc = [permissions.CanAccessTimeseriesData]
        else:
            pc = [permissions.CanEditOrReadOnly]
        return [x() for x in pc]

    def get_queryset(self):
        try:
            return models.Timeseries.objects.filter(
                timeseries_group_id=self.kwargs["timeseries_group_id"]
            )
        except KeyError:
            # Sometimes we know the station_id but not the timeseries_group_id. This
            # happens in backwards-compatible URLs like /api/stations/1403/timeseries/.
            # We don't unit-test this since it's deprecated and will be removed in a
            # future version.
            return models.Timeseries.objects.filter(
                timeseries_group__gentity_id=self.kwargs["station_id"]
            )

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
            timeseries_group_id = int(serializer.get_initial()["timeseries_group"])
        except ValueError:
            raise Http404
        timeseries_group = get_object_or_404(
            models.TimeseriesGroup, id=timeseries_group_id
        )
        station = timeseries_group.gentity.gpoint.station
        if not request.user.is_authenticated:
            return Response("Unauthorized", status=status.HTTP_401_UNAUTHORIZED)
        if not request.user.has_perm("enhydris.change_station", station):
            return Response("Forbidden", status=status.HTTP_403_FORBIDDEN)

        # Check whether the station and timeseries group ids in the url and in the
        # posted data are consistent
        if str(timeseries_group.gentity_id) != self.kwargs["station_id"]:
            return Response("Wrong gentity_id", status=status.HTTP_400_BAD_REQUEST)
        if str(timeseries_group.id) != self.kwargs["timeseries_group_id"]:
            return Response(
                "Wrong timeseries_group_id", status=status.HTTP_400_BAD_REQUEST
            )

        # All checks passed, call inherited method to do the actual work.
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=["get", "post"])
    def data(self, request, pk=None, *, station_id, timeseries_group_id=None):
        if request.method in ("GET", "HEAD"):
            return self._get_data(request, pk)
        elif request.method == "POST":
            return self._post_data(request, pk)

    @action(detail=True, methods=["get"])
    def bottom(self, request, pk=None, *, station_id, timeseries_group_id=None):
        ts = get_object_or_404(models.Timeseries, pk=pk)
        self.check_object_permissions(request, ts)
        response = HttpResponse(content_type="text/plain")
        response.write(ts.get_last_record_as_string())
        return response

    @action(detail=True, methods=["get"])
    def chart(self, request, pk=None, *, station_id, timeseries_group_id=None):
        timeseries = get_object_or_404(models.Timeseries, pk=pk)
        self.check_object_permissions(request, timeseries)
        serializer = serializers.TimeseriesRecordChartSerializer(
            self._get_chart_data(request, timeseries), many=True
        )
        return Response(serializer.data)

    def _get_chart_data(self, request, timeseries):
        start_date, end_date = self._get_date_bounds(request, timeseries)
        df = self._drop_nan_rows(timeseries, start_date, end_date)
        return self._get_stats_for_all_intervals(df)

    def _drop_nan_rows(self, timeseries, start_date, end_date):
        return timeseries.get_data(
            start_date=start_date, end_date=end_date
        ).data.dropna(subset=["value"])

    def _get_stats_for_all_intervals(self, df):
        number_of_samples = min(self.CHART_MAX_INTERVALS, len(df.index))
        if number_of_samples < 2:
            return []
        min_time = df.index.min()
        max_time = df.index.max()
        interval = (max_time - min_time) / number_of_samples
        result = []
        start_time = min_time
        while start_time < max_time:
            end_time = start_time + interval
            result.append(self._get_stats_for_interval(df, start_time, end_time))
            start_time = end_time
        return result

    def _get_stats_for_interval(self, df, start_time, end_time):
        df_part = df[start_time:end_time]
        min_value = df_part["value"].min()
        max_value = df_part["value"].max()
        mean_value = df_part["value"].mean()
        if np.isnan(min_value):
            min_value = max_value = mean_value = None
        return {
            "timestamp": (start_time + (end_time - start_time) / 2).timestamp(),
            "min": min_value,
            "max": max_value,
            "mean": mean_value,
        }

    def _get_date_bounds(self, request, timeseries):
        tz = timeseries.timeseries_group.time_zone.as_tzinfo
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        start_date = self._get_date_from_string(start_date, tz)
        end_date = self._get_date_from_string(end_date, tz)
        return start_date, end_date

    def _get_data(self, request, pk, format=None):
        timeseries = get_object_or_404(models.Timeseries, pk=int(pk))
        self.check_object_permissions(request, timeseries)
        start_date, end_date = self._get_date_bounds(request, timeseries)
        fmt_param = request.GET.get("fmt", "csv").lower()

        if fmt_param == "hts":
            fmt = HTimeseries.FILE
            version = 5
            extension = "hts"
            content_type = "text/vnd.openmeteo.timeseries"
        elif fmt_param == "hts2":
            fmt = HTimeseries.FILE
            version = 2
            extension = "hts"
            content_type = "text/vnd.openmeteo.timeseries"
        else:
            fmt = HTimeseries.TEXT
            version = "irrelevant"
            extension = "csv"
            content_type = "text/csv"
        response = HttpResponse(content_type=content_type + "; charset=utf-8")
        response["Content-Disposition"] = 'inline; filename="{}.{}"'.format(
            pk, extension
        )
        if request.method == "GET":
            ahtimeseries = timeseries.get_data(start_date=start_date, end_date=end_date)
            ahtimeseries.write(response, format=fmt, version=version)
        return response

    def _post_data(self, request, pk, format=None):
        try:
            atimeseries = get_object_or_404(models.Timeseries, pk=int(pk))
            self.check_object_permissions(request, atimeseries)
            atimeseries.append_data(StringIO(request.data["timeseries_records"]))
            return HttpResponse(status=status.HTTP_204_NO_CONTENT)
        except (IntegrityError, iso8601.ParseError, ValueError) as e:
            return HttpResponse(
                status=status.HTTP_400_BAD_REQUEST,
                content=str(e),
                content_type="text/plain",
            )

    def _get_date_from_string(self, adate, tz):
        date = self._parse_date(adate, tz)
        if not date:
            return None
        return self._bring_date_within_system_limits(date)

    def _parse_date(self, adate, tz):
        try:
            return iso8601.parse_date(adate, default_timezone=tz)
        except iso8601.ParseError:
            return None

    def _bring_date_within_system_limits(self, date):
        if date.isoformat() < "1680-01-01T00:00":
            date = dt.datetime(1680, 1, 1, 0, 0, tzinfo=date.tzinfo)
        if date.isoformat() > "2260-01-01T00:00":
            date = dt.datetime(2260, 1, 1, 0, 0, tzinfo=date.tzinfo)
        return date
