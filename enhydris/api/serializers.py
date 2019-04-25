from django.contrib.auth.models import User
from rest_framework import serializers

from enhydris import models


class UserSerializer(serializers.ModelSerializer):
    # To see why we specify the id, check https://stackoverflow.com/questions/36473795/
    id = serializers.IntegerField(required=False)

    # We also convert these two fields to optional, so that when used as a nested
    # serializer they don't need to be specified (usually the id suffices as we don't
    # create a user at the same time as a station, we always use an existing user).
    username = serializers.CharField(max_length=150, required=False)
    password = serializers.CharField(max_length=128, required=False)

    class Meta:
        model = User
        fields = "__all__"


class TimeseriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Timeseries
        fields = "__all__"


class WaterDivisionSerializer(serializers.ModelSerializer):
    # To see why we specify the id, check https://stackoverflow.com/questions/36473795/
    id = serializers.IntegerField(required=False)

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
    # To see why we specify the id, check https://stackoverflow.com/questions/36473795/
    id = serializers.IntegerField(required=False)

    class Meta:
        model = models.Person
        fields = "__all__"


class StationTypeSerializer(serializers.ModelSerializer):
    # To see why we specify the id, check https://stackoverflow.com/questions/36473795/
    id = serializers.IntegerField(required=False)

    class Meta:
        model = models.StationType
        fields = "__all__"


class TimeZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TimeZone
        fields = "__all__"


class PoliticalDivisionSerializer(serializers.ModelSerializer):
    # To see why we specify the id, check https://stackoverflow.com/questions/36473795/
    id = serializers.IntegerField(required=False)

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
    # To see why we specify the id, check https://stackoverflow.com/questions/36473795/
    id = serializers.IntegerField(required=False)

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


class StationSerializer(serializers.ModelSerializer):
    water_basin = WaterBasinSerializer(required=False)
    water_division = WaterDivisionSerializer(required=False)
    political_division = PoliticalDivisionSerializer(required=False)
    stype = StationTypeSerializer(many=True, required=False)
    overseers = PersonSerializer(many=True, required=False)

    class Meta:
        model = models.Station
        exclude = ("creator", "maintainers")

    def validate_nested_serializer(self, value):
        try:
            return value["id"]
        except KeyError as e:
            raise serializers.ValidationError(str(e))

    validate_water_basin = validate_nested_serializer
    validate_water_division = validate_nested_serializer
    validate_political_division = validate_nested_serializer

    def validate_nested_many_serializer(self, value):
        try:
            return [x["id"] for x in value]
        except KeyError as e:
            raise serializers.ValidationError(str(e))

    validate_stype = validate_nested_many_serializer
    validate_overseers = validate_nested_many_serializer
    validate_maintainers = validate_nested_many_serializer
