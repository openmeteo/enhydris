from django.utils import translation
from rest_framework import serializers

from parler_rest.fields import TranslatedFieldsField
from parler_rest.serializers import TranslatableModelSerializer

from enhydris import models


class TimeseriesTypeField(serializers.Field):
    timeseries_types = dict(models.Timeseries.TIMESERIES_TYPES)
    reverse_timeseries_types = {k: v for v, k in models.Timeseries.TIMESERIES_TYPES}

    def to_representation(self, value):
        with translation.override(None):
            return str(self.timeseries_types[value])

    def to_internal_value(self, data):
        return self.reverse_timeseries_types[data]


class TimeseriesSerializer(serializers.ModelSerializer):
    type = TimeseriesTypeField()

    class Meta:
        model = models.Timeseries
        fields = "__all__"


class GareaSerializer(serializers.ModelSerializer):
    # To see why we specify the id, check https://stackoverflow.com/questions/36473795/
    id = serializers.IntegerField(required=False)

    class Meta:
        model = models.Garea
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


class TimeZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TimeZone
        fields = "__all__"


class EventTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EventType
        fields = "__all__"


class VariableSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=models.Variable, required=False)

    class Meta:
        model = models.Variable
        fields = "__all__"


class UnitOfMeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UnitOfMeasurement
        fields = "__all__"


class GentityFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GentityFile
        fields = "__all__"


class GentityEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GentityEvent
        fields = "__all__"


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Station
        exclude = ("creator", "maintainers")

    def validate_nested_many_serializer(self, value):
        try:
            return [x["id"] for x in value]
        except KeyError as e:
            raise serializers.ValidationError(str(e))

    validate_maintainers = validate_nested_many_serializer


class TimeseriesRecordChartSerializer(serializers.Serializer):
    timestamp = serializers.IntegerField()
    value = serializers.DecimalField(max_digits=6, decimal_places=2)
