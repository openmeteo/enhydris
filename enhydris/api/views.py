from io import StringIO

from django.db import IntegrityError
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response

import iso8601
import pd2hts
import pytz

from . import serializers
from .permissions import CanEditOrReadOnly, CanCreateStation
from enhydris import models


class ListAPIView(generics.ListAPIView):
    def get_queryset(self):
        modified_after = "1900-01-01"
        if "modified_after" in self.kwargs:
            modified_after = self.kwargs["modified_after"]
        modified_after = iso8601.parse_date(modified_after, default_timezone=pytz.utc)
        return self.queryset.exclude(last_modified__lte=modified_after)


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

    def put(self, request, pk, format=None):
        try:
            atimeseries = models.Timeseries.objects.get(pk=int(pk))
            self.check_object_permissions(request, atimeseries)
            nrecords = atimeseries.append_data(
                StringIO(request.data["timeseries_records"])
            )
            return HttpResponse(str(nrecords), content_type="text/plain")
        except (IntegrityError, iso8601.ParseError) as e:
            return HttpResponse(
                status=status.HTTP_400_BAD_REQUEST,
                content=str(e),
                content_type="text/plain",
            )

    def post(self, request, pk, format=None):
        """
        We temporarily keep post the same as put so that older
        versions of loggertodb continue to work
        """
        return self.put(request, pk, format=None)


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
        if not request.user.has_perm("enhydris.change_station", station):
            return Response("Forbidden", status=status.HTTP_403_FORBIDDEN)

        return super(TimeseriesList, self).post(request, *args, **kwargs)


class TimeseriesDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Timeseries.objects.all()
    serializer_class = serializers.TimeseriesSerializer
    permission_classes = (CanEditOrReadOnly,)


class StationList(generics.ListCreateAPIView):
    queryset = models.Station.objects.all()
    serializer_class = serializers.StationSerializer
    permission_classes = (CanCreateStation,)


class StationDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Station.objects.all()
    serializer_class = serializers.StationSerializer
    permission_classes = (CanEditOrReadOnly,)


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
