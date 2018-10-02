from rest_framework import serializers
from enhydris import models


class StationSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Station
        exclude = ('creator',)


class TimeseriesSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Timeseries
        exclude = ()
