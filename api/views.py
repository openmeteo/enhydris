from StringIO import StringIO
from django.http import Http404, HttpResponse
from django.db import connection
from rest_framework import generics, status
from rest_framework.views import APIView
from enhydris.core import models
from enhydris.api import serializers
from enhydris.api.permissions import CanEditOrReadOnly

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
    serializer_class = serializers.TimeseriesSerializer
    permission_classes = (CanEditOrReadOnly,)
