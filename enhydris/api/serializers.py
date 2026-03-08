import datetime as dt
from typing import Any

from django.utils import translation
from rest_framework import serializers

from enhydris import models


class TimeseriesTypeField(serializers.Field[int, str, str, Any]):
    timeseries_types = dict(models.Timeseries.TIMESERIES_TYPES)
    reverse_timeseries_types = {
        str(k): v for v, k in models.Timeseries.TIMESERIES_TYPES
    }

    def to_representation(self, value: int):
        with translation.override(None):
            return str(self.timeseries_types[value])

    def to_internal_value(self, data: str):
        try:
            return self.reverse_timeseries_types[data]
        except KeyError:
            raise serializers.ValidationError(
                f'"{data}" is not a valid time series type'
            )


class TimeseriesSerializer(serializers.ModelSerializer[models.Timeseries]):
    type = TimeseriesTypeField()

    class Meta:  # type: ignore
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
        tg = data.get("timeseries_group")
        if not tg:
            assert self.instance is not None
            tg = self.instance.timeseries_group
        if data.get("type") in types:
            self._check_timeseries_does_not_exist(tg, data["type"])

    def _check_timeseries_does_not_exist(
        self, timeseries_group: models.TimeseriesGroup, type: int
    ):
        queryset = models.Timeseries.objects.filter(
            timeseries_group=timeseries_group, type=type
        ).exclude(id=getattr(self.instance, "id", 0))
        if queryset.exists():
            with translation.override(None):
                type_str = str(dict(models.Timeseries.TIMESERIES_TYPES)[type])
            raise serializers.ValidationError(
                f"A time series with timeseries_group_id={timeseries_group.pk} and "
                f"type={type_str} already exists"
            )


class GareaSerializer(serializers.ModelSerializer[models.Garea]):
    # To see why we specify the id, check https://stackoverflow.com/questions/36473795/
    id = serializers.IntegerField(required=False)

    class Meta:  # type: ignore
        model = models.Garea
        fields = "__all__"


class OrganizationSerializer(serializers.ModelSerializer[models.Organization]):
    class Meta:  # type: ignore
        model = models.Organization
        fields = "__all__"


class PersonSerializer(serializers.ModelSerializer[models.Person]):
    # To see why we specify the id, check https://stackoverflow.com/questions/36473795/
    id = serializers.IntegerField(required=False)

    class Meta:  # type: ignore
        model = models.Person
        fields = "__all__"


class EventTypeSerializer(serializers.ModelSerializer[models.EventType]):
    class Meta:  # type: ignore
        model = models.EventType
        fields = "__all__"


class VariableSerializer(serializers.ModelSerializer[models.Variable]):
    translations = serializers.SerializerMethodField()

    class Meta:  # type: ignore
        model = models.Variable
        fields = "__all__"

    def get_translations(self, obj: models.Variable) -> dict[str, dict[str, str]]:
        return {t.language_code: {"descr": t.descr} for t in obj.translations.all()}


class UnitOfMeasurementSerializer(
    serializers.ModelSerializer[models.UnitOfMeasurement]
):
    class Meta:  # type: ignore
        model = models.UnitOfMeasurement
        fields = "__all__"


class GentityFileSerializer(serializers.ModelSerializer[models.GentityFile]):
    class Meta:  # type: ignore
        model = models.GentityFile
        fields = "__all__"


class GentityImageSerializer(serializers.ModelSerializer[models.GentityImage]):
    class Meta:  # type: ignore
        model = models.GentityImage
        fields = "__all__"


class GentityEventSerializer(serializers.ModelSerializer[models.GentityEvent]):
    class Meta:  # type: ignore
        model = models.GentityEvent
        fields = "__all__"


class StationSerializer(serializers.ModelSerializer[models.Station]):
    last_update = serializers.DateTimeField(
        read_only=True, default_timezone=dt.timezone.utc
    )

    class Meta:  # type: ignore
        model = models.Station
        exclude = ("creator", "maintainers", "sites", "timeseries_data_viewers")

    def validate_nested_many_serializer(self, value: list[dict[str, int]]):
        try:
            return [x["id"] for x in value]
        except KeyError as e:
            raise serializers.ValidationError(str(e))

    validate_maintainers = validate_nested_many_serializer


class TimeseriesGroupSerializer(serializers.ModelSerializer[models.TimeseriesGroup]):
    class Meta:  # type: ignore
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


class TimeseriesRecordChartSerializer(serializers.Serializer[dict[str, float]]):
    timestamp = serializers.IntegerField()
    min = serializers.FloatField()
    max = serializers.FloatField()
    mean = serializers.FloatField()
