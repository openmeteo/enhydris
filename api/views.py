from StringIO import StringIO
from django.http import Http404, HttpResponse
from django.db import connection
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from enhydris.hcore import models
from enhydris.api.permissions import CanEditOrReadOnly


modelnames = (
    'Lookup Lentity Person Organization Gentity Gpoint Gline Garea '
    'PoliticalDivisionManager PoliticalDivision WaterDivision WaterBasin '
    'GentityAltCodeType GentityAltCode FileType GentityFile EventType '
    'GentityEvent StationType StationManager Station Overseer InstrumentType '
    'Instrument Variable UnitOfMeasurement TimeZone TimeStep Timeseries'
).split()


@api_view(('GET',))
def api_root(request, format=None):
    d = {}
    for m in modelnames:
        d[m] = reverse(m+'-list', request=request, format=format)
    return Response(d)


class Tsdata(APIView):
    """
    Take a timeseries id and return the actual timeseries data to the client,
    or update a time series with new records.
    """
    permission_classes = CanEditOrReadOnly

    def get_object(self, pk):
        try:
            return models.Timeseries.objects.get(pk=pk)
        except models.Timeseries.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        timeseries = self.get_object(pk)
        timeseries.read_from_db(connection)
        result = StringIO()
        timeseries.write_file(result)
        return HttpResponse(result.getvalue(), content_type="text/plain")

    def put(self, request, pk, format=None):
        try:
            timeseries = self.get_object(pk)
            result_if_error = status.HTTP_400_BAD_REQUEST
            timeseries.read(StringIO(request.POST['timeseries_records']))
            result_if_error = status.HTTP_409_CONFLICT
            timeseries.append_to_db(connection, commit=False)
            return HttpResponse(str(len(timeseries)), content_type="text/plain")
        except ValueError as e:
            return HttpResponse(status_code=result_if_error,
                                content=str(e),
                                content_type="text/plain")


class TimeseriesDetail(generics.RetrieveUpdateDestroyAPIView):
    model = models.Timeseries
    permission_classes = (CanEditOrReadOnly,)
