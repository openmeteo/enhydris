from rest_framework import serializers

from enhydris import models


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Station
        exclude = ("creator",)


class TimeseriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Timeseries
        fields = "__all__"


class WaterDivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WaterDivision
        fields = "__all__"


class GentityAltCodeTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GentityAltCodeType
        fields = "__all__"


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Organization
        fields = "__all__"


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Person
        fields = "__all__"


class StationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.StationType
        fields = "__all__"


class TimeZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TimeZone
        fields = "__all__"


class PoliticalDivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PoliticalDivision
        fields = "__all__"


class IntervalTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IntervalType
        fields = "__all__"


class FileTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FileType
        fields = "__all__"


class EventTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EventType
        fields = "__all__"


class InstrumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.InstrumentType
        fields = "__all__"


class WaterBasinSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WaterBasin
        fields = "__all__"


class TimeStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TimeStep
        fields = "__all__"


class VariableSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Variable
        fields = "__all__"


class UnitOfMeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UnitOfMeasurement
        fields = "__all__"


class GentityAltCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GentityAltCode
        fields = "__all__"


class GentityFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GentityFile
        fields = "__all__"


class GentityEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GentityEvent
        fields = "__all__"


class OverseerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Overseer
        fields = "__all__"


class InstrumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Instrument
        fields = "__all__"
