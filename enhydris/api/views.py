from __future__ import annotations

import datetime as dt
import mimetypes
import os
from io import StringIO
from typing import Any
from wsgiref.util import FileWrapper

from django.db import IntegrityError
from django.db.models import Prefetch, QuerySet
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.timezone import is_aware
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

import numpy as np
import pandas as pd
from htimeseries import HTimeseries

from enhydris import models
from enhydris.views_common import StationListViewMixin

from . import permissions, serializers
from .csv import prepare_csv


class StationViewSet(StationListViewMixin, ModelViewSet[models.Station]):
    serializer_class = serializers.StationSerializer

    def get_permissions(self):
        pc: list[Any] = [permissions.SatisfiesAuthenticationRequiredSetting]
        if self.action == "create":
            pc.append(permissions.CanCreateStation)
        else:
            pc.append(permissions.CanEditOrReadOnly)
        return [x() for x in pc]

    def list(self, request: Request):
        response = super().list(request)
        response.data["bounding_box"] = self._get_bounding_box()
        return response

    @action(detail=False, methods=["get"])
    def csv(self, request: Request):
        queryset: QuerySet[models.Station] = (  # type: ignore
            self.get_queryset()  # type: ignore
            .select_related("owner")  # type: ignore
            .prefetch_related(  # type: ignore
                Prefetch(
                    "timeseriesgroup_set",
                    queryset=models.TimeseriesGroup.objects.select_related(
                        "variable", "unit_of_measurement"
                    )
                    .prefetch_related("timeseries_set")
                    .order_by("variable__id"),
                )
            )
        )
        data = prepare_csv(queryset)  # type: ignore
        response = HttpResponse(data, content_type="application/zip")
        response["Content-Disposition"] = "attachment; filename=data.zip"
        response["Content-Length"] = len(data)
        return response


class GareaViewSet(ReadOnlyModelViewSet[models.Garea]):
    serializer_class = serializers.GareaSerializer
    queryset = models.Garea.objects.all()


class OrganizationViewSet(ReadOnlyModelViewSet[models.Organization]):
    serializer_class = serializers.OrganizationSerializer
    queryset = models.Organization.objects.all()


class PersonViewSet(ReadOnlyModelViewSet[models.Person]):
    serializer_class = serializers.PersonSerializer
    queryset = models.Person.objects.all()


class EventTypeViewSet(ReadOnlyModelViewSet[models.EventType]):
    serializer_class = serializers.EventTypeSerializer
    queryset = models.EventType.objects.all()


class VariableViewSet(ReadOnlyModelViewSet[models.Variable]):
    serializer_class = serializers.VariableSerializer
    queryset = models.Variable.objects.all()  # type: ignore


class UnitOfMeasurementViewSet(ReadOnlyModelViewSet[models.UnitOfMeasurement]):
    serializer_class = serializers.UnitOfMeasurementSerializer
    queryset = models.UnitOfMeasurement.objects.all()


class GentityEventViewSet(ReadOnlyModelViewSet[models.GentityEvent]):
    serializer_class = serializers.GentityEventSerializer

    def get_queryset(self):
        return models.GentityEvent.objects.filter(gentity_id=self.kwargs["station_id"])


class GentityFileViewSet(ReadOnlyModelViewSet[models.GentityFile]):
    serializer_class = serializers.GentityFileSerializer

    def get_queryset(self):
        return models.GentityFile.objects.filter(gentity_id=self.kwargs["station_id"])

    @action(detail=True, methods=["get"])
    def content(
        self, request: Request, pk: int | None = None, *, station_id: int | None = None
    ):
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


class GentityImageViewSet(GentityFileViewSet):
    serializer_class = serializers.GentityImageSerializer

    def get_queryset(self):  # type: ignore
        return models.GentityImage.objects.filter(gentity_id=self.kwargs["station_id"])


class TimeseriesGroupViewSet(ModelViewSet[models.TimeseriesGroup]):
    serializer_class = serializers.TimeseriesGroupSerializer
    permission_classes = [
        permissions.SatisfiesAuthenticationRequiredSetting,
        permissions.CanEditOrReadOnly,
    ]

    def get_queryset(self):
        return models.TimeseriesGroup.objects.filter(
            gentity_id=self.kwargs["station_id"]
        )

    def create(self, request: Request, *args: Any, **kwargs: Any):
        """Redefine create, checking permissions and gentity_id.

        Django-rest-framework does not do object-level permission when
        creating a new object, so we have to completely customize the create
        method. In addition, we check that the gentity_id specified in the data
        is the same as the station_id in the URL.
        """
        # Get the data
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Check permissions
        station = get_object_or_404(models.Station, id=self.kwargs["station_id"])
        if not request.user.is_authenticated:
            return Response("Unauthorized", status=status.HTTP_401_UNAUTHORIZED)
        if not request.user.has_perm("enhydris.change_station", station):  # type: ignore
            return Response("Forbidden", status=status.HTTP_403_FORBIDDEN)

        # Check whether the station id in the url and in the posted data are consistent
        if str(serializer.data["gentity"]) != self.kwargs["station_id"]:
            return Response("Wrong gentity_id", status=status.HTTP_400_BAD_REQUEST)

        # All checks passed, call inherited method to do the actual work.
        return super().create(request, *args, **kwargs)


class TimeseriesViewSet(ModelViewSet[models.Timeseries]):
    CHART_MAX_INTERVALS = 200
    queryset = models.Timeseries.objects.all()
    serializer_class = serializers.TimeseriesSerializer
    lookup_value_regex = r"\d+"

    def get_permissions(self):
        pc = [permissions.SatisfiesAuthenticationRequiredSetting]
        if self.action in ("data", "bottom", "chart"):
            pc.append(permissions.CanAccessTimeseriesData)  # type: ignore
        else:
            pc.append(permissions.CanEditOrReadOnly)  # type: ignore
        return [x() for x in pc]

    def get_queryset(self):
        return models.Timeseries.objects.filter(
            timeseries_group__gentity__id=self.kwargs["station_id"],
            timeseries_group_id=self.kwargs["timeseries_group_id"],
        )

    def create(self, request: Request, *args: Any, **kwargs: Any):
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
            timeseries_group_id = int(serializer.get_initial()["timeseries_group"])  # type: ignore
        except ValueError:
            raise Http404
        timeseries_group = get_object_or_404(
            models.TimeseriesGroup, id=timeseries_group_id
        )
        station = timeseries_group.gentity.gpoint.station  # type: ignore
        if not request.user.is_authenticated:
            return Response("Unauthorized", status=status.HTTP_401_UNAUTHORIZED)
        if not request.user.has_perm("enhydris.change_station", station):  # type: ignore
            return Response("Forbidden", status=status.HTTP_403_FORBIDDEN)

        # Check whether the station and timeseries group ids in the url and in the
        # posted data are consistent
        if str(timeseries_group.gentity.pk) != self.kwargs["station_id"]:
            return Response("Wrong gentity_id", status=status.HTTP_400_BAD_REQUEST)
        if str(timeseries_group.pk) != self.kwargs["timeseries_group_id"]:
            return Response(
                "Wrong timeseries_group_id", status=status.HTTP_400_BAD_REQUEST
            )

        # All checks passed, call inherited method to do the actual work.
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=["get", "post"])  # type: ignore
    def data(
        self,
        request: Request,
        pk: int = 0,
        *,
        station_id: int | None = None,
        timeseries_group_id: int | None = None,
    ):
        if request.method in ("GET", "HEAD"):
            return self._get_data(request, pk)
        elif request.method == "POST":
            return self._post_data(request, pk)

    @action(detail=True, methods=["get"])
    def bottom(
        self,
        request: Request,
        pk: int = 0,
        *,
        station_id: int,
        timeseries_group_id: int | None = None,
    ):
        ts = get_object_or_404(models.Timeseries, pk=int(pk))
        self.check_object_permissions(request, ts)
        response = HttpResponse(content_type="text/plain")
        timezone_param = request.GET.get("timezone", "")
        response.write(ts.get_last_record_as_string(timezone=timezone_param))
        return response

    @action(detail=True, methods=["get"])
    def chart(
        self,
        request: Request,
        pk: int = 0,
        *,
        station_id: int,
        timeseries_group_id: int | None = None,
    ):
        timeseries = get_object_or_404(models.Timeseries, pk=int(pk))
        self.check_object_permissions(request, timeseries)
        try:
            serializer = serializers.TimeseriesRecordChartSerializer(
                self._get_chart_data(request, timeseries), many=True
            )
        except ValueError as e:
            return HttpResponse(
                status=status.HTTP_400_BAD_REQUEST,
                content=str(e),
                content_type="text/plain",
            )
        return Response(serializer.data)  # type: ignore

    def _get_chart_data(self, request: Request, timeseries: models.Timeseries):
        start_date, end_date = self._get_date_bounds(request, timeseries)
        df = self._drop_nan_rows(timeseries, start_date, end_date)
        return self._get_stats_for_all_intervals(df)

    def _drop_nan_rows(
        self,
        timeseries: models.Timeseries,
        start_date: dt.datetime | None,
        end_date: dt.datetime | None,
    ) -> pd.DataFrame:
        return timeseries.get_data(
            start_date=start_date, end_date=end_date
        ).data.dropna(  # type: ignore
            subset=["value"]
        )

    def _get_stats_for_all_intervals(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        number_of_samples = min(self.CHART_MAX_INTERVALS, len(df.index))
        if number_of_samples < 2:
            return []
        min_time = df.index.min()
        max_time = df.index.max()
        interval = (max_time - min_time) / number_of_samples
        result: list[dict[str, Any]] = []
        start_time = min_time
        while start_time < max_time:
            end_time = start_time + interval
            result.append(self._get_stats_for_interval(df, start_time, end_time))
            start_time = end_time
        return result

    def _get_stats_for_interval(
        self, df: pd.DataFrame, start_time: dt.datetime, end_time: dt.datetime
    ):
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

    def _get_date_bounds(self, request: Request, timeseries: models.Timeseries):
        start_date = request.GET.get("start_date") or None
        end_date = request.GET.get("end_date") or None
        if start_date is not None:
            start_date = self._get_date_from_string(start_date)  # type: ignore
        if end_date is not None:
            end_date = self._get_date_from_string(end_date)  # type: ignore
        return start_date, end_date

    def _get_data(self, request: Request, pk: int, format: str | None = None):
        timeseries = self.get_object()
        self.check_object_permissions(request, timeseries)
        try:
            start_date, end_date = self._get_date_bounds(request, timeseries)
        except ValueError as e:
            return HttpResponse(
                status=status.HTTP_400_BAD_REQUEST,
                content=str(e),
                content_type="text/plain",
            )
        fmt_param = request.GET.get("fmt", "csv").lower()
        timezone_param = request.GET.get("timezone", None)

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
            version = -1  # Irrelevant
            extension = "csv"
            content_type = "text/csv"
        response = HttpResponse(content_type=content_type + "; charset=utf-8")
        response["Content-Disposition"] = 'inline; filename="{}.{}"'.format(
            pk, extension
        )
        if request.method == "GET":
            ahtimeseries = timeseries.get_data(
                start_date=start_date, end_date=end_date, timezone=timezone_param
            )
            ahtimeseries.write(response, format=fmt, version=version)  # type: ignore
        return response

    def _post_data(self, request: Request, pk: int, format: str | None = None):
        mode = request.data.get("mode", "append")
        if mode not in ("append", "insert"):
            return HttpResponse(
                status=status.HTTP_400_BAD_REQUEST,
                content="Invalid mode value",
                content_type="text/plain",
            )
        try:
            atimeseries = self.get_object()
            self.check_object_permissions(request, atimeseries)
            atimeseries.insert_or_append_data(
                StringIO(request.data["timeseries_records"]),
                default_timezone=request.data["timezone"],
                append_only=(mode == "append"),
            )
            return HttpResponse(status=status.HTTP_204_NO_CONTENT)
        except (IntegrityError, ValueError, KeyError) as e:
            return HttpResponse(
                status=status.HTTP_400_BAD_REQUEST,
                content=str(e),
                content_type="text/plain",
            )

    def _get_date_from_string(self, adate: str):
        date = self._parse_date(adate)
        if not date or not is_aware(date):
            raise ValueError(f"Invalid date: '{adate}' (must contain timezone)")
        return self._bring_date_within_system_limits(date)

    def _parse_date(self, adate: str):
        return dt.datetime.fromisoformat(adate)

    def _bring_date_within_system_limits(self, date: dt.datetime):
        if date < dt.datetime(1680, 1, 1, 0, 0, tzinfo=dt.timezone.utc):
            date = dt.datetime(1680, 1, 1, 0, 0, tzinfo=dt.timezone.utc)
        if date > dt.datetime(2260, 1, 1, 0, 0, tzinfo=dt.timezone.utc):
            date = dt.datetime(2260, 1, 1, 0, 0, tzinfo=dt.timezone.utc)
        return date
