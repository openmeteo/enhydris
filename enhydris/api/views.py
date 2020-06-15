import mimetypes
import os
from io import StringIO
from wsgiref.util import FileWrapper

from django.conf import settings
from django.db import IntegrityError
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
        data = prepare_csv(self.get_queryset())
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


class TimeseriesViewSet(ModelViewSet):
    queryset = models.Timeseries.objects.all()
    serializer_class = serializers.TimeseriesSerializer

    def get_permissions(self):
        if self.action in ("data", "bottom", "chart"):
            pc = [permissions.CanAccessTimeseriesData]
        else:
            pc = [permissions.CanEditOrReadOnly]
        return [x() for x in pc]

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
        if request.method in ("GET", "HEAD"):
            return self._get_data(request, pk)
        elif request.method == "POST":
            return self._post_data(request, pk)

    @action(detail=True, methods=["get"])
    def bottom(self, request, pk=None, *, station_id):
        ts = get_object_or_404(models.Timeseries, pk=pk)
        self.check_object_permissions(request, ts)
        response = HttpResponse(content_type="text/plain")
        response.write(ts.get_last_record_as_string())
        return response

    @action(detail=True, methods=["get"])
    def chart(self, request, pk=None, *, station_id):
        timeseries = get_object_or_404(models.Timeseries, pk=pk)
        self.check_object_permissions(request, timeseries)
        serializer = serializers.TimeseriesRecordChartSerializer(
            self._get_chart_data(request, timeseries), many=True
        )
        return Response(serializer.data)

    def _get_chart_data(self, request, timeseries):
        start_date, end_date = self._get_date_bounds(request, timeseries)
        # Drop rows with value "NaN"
        data_frame = timeseries.get_data(
            start_date=start_date, end_date=end_date
        ).data.dropna(subset=["value"])
        return self._sample_equidistant(data_frame)

    def _sample_equidistant(self, df):
        """
        Divides dataframe/timeseries by time into "number_of_samples" equally,
        and returns a list of dicts, where each dict contains timestamp, value
        """
        number_of_samples = min(
            settings.ENHYDRIS_TS_GRAPH_BIG_STEP_DENOMINATOR, len(df.index)
        )
        min_time = df.index.min()
        # To accommodate the first data point
        current_time = min_time
        interval = (df.index.max() - df.index.min()) / (number_of_samples - 1)
        tolerance = interval / 2
        result = []
        for _ in range(number_of_samples):
            try:
                idx = df.index.get_loc(
                    current_time, method="nearest", tolerance=tolerance
                )
                value = df.iloc[idx].value
            except KeyError:
                # If no matching index is found (i.e the tolerance is exceeded)
                # a KeyError is raised rather than returning null gracefully
                value = pd.np.nan
            result.append({"timestamp": current_time.timestamp(), "value": value})
            current_time += interval
        return result

    def _get_date_bounds(self, request, timeseries):
        tz = timeseries.time_zone.as_tzinfo
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
        if date.isoformat() < pd.Timestamp.min.isoformat():
            date = pd.Timestamp.min
        if date.isoformat() > pd.Timestamp.max.isoformat():
            date = pd.Timestamp.max
        return date
