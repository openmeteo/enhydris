from StringIO import StringIO

from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404

import iso8601
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from enhydris.hcore import models
from enhydris.api.permissions import CanEditOrReadOnly, CanCreateStation
from enhydris.api.serializers import StationSerializer, TimeseriesSerializer
import pytz


modelnames = (
    'Lentity Person Organization Gentity Gpoint Gline Garea '
    'PoliticalDivision WaterDivision WaterBasin '
    'GentityAltCodeType GentityAltCode FileType GentityFile EventType '
    'GentityEvent StationType Station Overseer InstrumentType '
    'Instrument Variable UnitOfMeasurement TimeZone TimeStep IntervalType '
    'Timeseries'
).split()


@api_view(('GET',))
def api_root(request, format=None):
    d = {}
    for m in modelnames:
        d[m] = reverse(m + '-list', request=request, format=format)
    return Response(d)


class ListAPIView(generics.ListAPIView):

    def get_queryset(self):
        modified_after = '1900-01-01'
        if 'modified_after' in self.kwargs:
            modified_after = self.kwargs['modified_after']
        modified_after = iso8601.parse_date(modified_after,
                                            default_timezone=pytz.utc)
        return self.queryset.exclude(last_modified__lte=modified_after)


class Tsdata(APIView):
    """
    Take a timeseries id and return the actual timeseries data to the client,
    or update a time series with new records.
    """
    permission_classes = (CanEditOrReadOnly,)

    def get(self, request, pk, format=None):
        timeseries = models.Timeseries.objects.get(pk=int(pk))
        self.check_object_permissions(request, timeseries)
        result = StringIO()
        timeseries.get_all_data().write(result)
        return HttpResponse(result.getvalue(), content_type="text/plain")

    def put(self, request, pk, format=None):
        try:
            atimeseries = models.Timeseries.objects.get(pk=int(pk))
            self.check_object_permissions(request, atimeseries)
            nrecords = atimeseries.append_data(StringIO(request.DATA[
                'timeseries_records']))
            return HttpResponse(str(nrecords), content_type="text/plain")
        except ValueError as e:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST,
                                content=str(e),
                                content_type="text/plain")

    def post(self, request, pk, format=None):
        """
        We temporarily keep post the same as put so that older
        versions of loggertodb continue to work
        """
        return self.put(request, pk, format=None)


class TimeseriesList(generics.ListCreateAPIView):
    queryset = models.Timeseries.objects.all()
    serializer_class = TimeseriesSerializer
    permission_classes = (CanEditOrReadOnly,)

    def post(self, request, *args, **kwargs):
        """
        Redefine post, checking permissions.
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
            gentity_id = int(serializer.get_initial()['gentity'])
        except ValueError:
            raise Http404
        station = get_object_or_404(models.Station, id=gentity_id)
        if not hasattr(request.user, 'has_row_perm') \
                or not request.user.has_row_perm(station, 'edit'):
            return Response('Forbidden', status=status.HTTP_403_FORBIDDEN)

        return super(TimeseriesList, self).post(request, *args, **kwargs)


class TimeseriesDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Timeseries.objects.all()
    serializer_class = TimeseriesSerializer
    permission_classes = (CanEditOrReadOnly,)


class StationList(generics.ListCreateAPIView):
    queryset = models.Station.objects.all()
    serializer_class = StationSerializer
    permission_classes = (CanCreateStation,)


class StationDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Station.objects.all()
    serializer_class = StationSerializer
    permission_classes = (CanEditOrReadOnly,)
