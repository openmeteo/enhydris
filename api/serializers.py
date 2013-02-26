from rest_framework import serializers
from enhydris.hcore import models
from enhydris.api.authentication import RemoteInstanceAuthentication

ts_auth = RemoteInstanceAuthentication(realm="Timeseries realm")


class StationSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Station
        exclude = ('creator',)
