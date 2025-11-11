import datetime as dt
from typing import Any

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
        try:
            return self.reverse_timeseries_types[data]
        except KeyError:
            raise serializers.ValidationError(
                f'"{data}" is not a valid time series type'
            )


class TimeseriesSerializer(serializers.ModelSerializer[models.Timeseries]):
    type = TimeseriesTypeField()

    class Meta:
        model = models.Timeseries
        fields = "__all__"

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        result = super().validate(attrs)
        self._check_for_change_of_timeseries_group(result)
        self._check_for_uniqueness_of_type(result)
        return result

    def _check_for_change_of_timeseries_group(self, data: dict[str, Any]):
        if not self.instance:
            return
        if "timeseries_group" in data:
            msg = "It is not allowed to change the timeseries_group of a time series."
            new_timeseries_group = data["timeseries_group"]
            if new_timeseries_group != self.instance.timeseries_group:
                raise serializers.ValidationError({"timeseries_group": msg})

    def _check_for_uniqueness_of_type(self, data: dict[str, Any]):
        types = (
            models.Timeseries.INITIAL,
            models.Timeseries.CHECKED,
            models.Timeseries.REGULARIZED,
        )
        tg = data.get("timeseries_group") or self.instance.timeseries_group
        if data.get("type") in types:
            self._check_timeseries_does_not_exist(tg, data["type"])

    def _check_timeseries_does_not_exist(
        self, timeseries_group: models.TimeseriesGroup, type: int
    ):
        queryset = models.Timeseries.objects.filter(
            timeseries_group=timeseries_group, type=type
        ).exclude(id=getattr(self.instance, "id", None))
        if queryset.exists():
            with translation.override(None):
                type_str = str(dict(models.Timeseries.TIMESERIES_TYPES)[type])
            raise serializers.ValidationError(
                f"A time series with timeseries_group_id={timeseries_group.id} and "
                f"type={type_str} already exists"
            )


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


class GentityImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GentityImage
        fields = "__all__"


class GentityEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GentityEvent
        fields = "__all__"


class StationSerializer(serializers.ModelSerializer):
    last_update = serializers.DateTimeField(
        read_only=True, default_timezone=dt.timezone.utc
    )

    class Meta:
        model = models.Station
        exclude = ("creator", "maintainers", "sites", "timeseries_data_viewers")

    def validate_nested_many_serializer(self, value):
        try:
            return [x["id"] for x in value]
        except KeyError as e:
            raise serializers.ValidationError(str(e))

    validate_maintainers = validate_nested_many_serializer


class TimeseriesGroupSerializer(serializers.ModelSerializer[models.TimeseriesGroup]):
    class Meta:
        model = models.TimeseriesGroup
        fields = "__all__"

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        result = super().validate(attrs)
        self._check_for_change_of_gentity(result)
        return result

    def _check_for_change_of_gentity(self, data: dict[str, Any]) -> None:
        if not self.instance or "gentity" not in data:
            return
        msg = "It is not allowed to change the gentity of a time series group."
        if data["gentity"] != self.instance.gentity:
            raise serializers.ValidationError({"gentity": msg})


class TimeseriesRecordChartSerializer(serializers.Serializer):
    timestamp = serializers.IntegerField()
    min = serializers.FloatField()
    max = serializers.FloatField()
    mean = serializers.FloatField()
