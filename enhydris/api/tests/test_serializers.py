from django.contrib.auth.models import User
from django.utils import translation
from rest_framework.test import APITestCase

from model_mommy import mommy

from enhydris import models
from enhydris.api.serializers import (
    StationSerializer,
    TimeseriesGroupSerializer,
    TimeseriesSerializer,
)


class StationSerializerTestCase(APITestCase):
    def setUp(self):
        station = mommy.make(
            models.Station,
            name="hello",
            overseer="Bilbo Baggins",
            maintainers=[mommy.make(User, username="Bilbo")],
        )
        self.serializer = StationSerializer(station)

    def test_name(self):
        self.assertEqual(self.serializer.data["name"], "hello")

    def test_overseer(self):
        self.assertEqual(self.serializer.data["overseer"], "Bilbo Baggins")

    def test_no_maintainers(self):
        # There shouldn't be information about maintainers, this is security information
        self.assertTrue("maintainers" not in self.serializer.data)


class TimeseriesGroupSerializerTestCase(APITestCase):
    def setUp(self):
        timeseries_group = mommy.make(
            models.TimeseriesGroup,
            name="My time series group",
        )
        self.serializer = TimeseriesGroupSerializer(timeseries_group)

    def test_name(self):
        self.assertEqual(self.serializer.data["name"], "My time series group")


class TimeseriesSerializerTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.timeseries_group = mommy.make(models.TimeseriesGroup)

    def test_type_serialization_for_initial(self):
        serializer = TimeseriesSerializer(models.Timeseries(type=100))
        self.assertEqual(serializer.data["type"], "Initial")

    def test_type_serialization_for_checked(self):
        serializer = TimeseriesSerializer(models.Timeseries(type=200))
        self.assertEqual(serializer.data["type"], "Checked")

    def test_type_serialization_for_initial_when_nondefault_language(self):
        serializer = TimeseriesSerializer(models.Timeseries(type=100))
        with translation.override("el"):
            self.assertEqual(serializer.data["type"], "Initial")

    def test_type_deserialization_for_initial(self):
        serializer = TimeseriesSerializer(
            data={
                "type": "Initial",
                "timeseries_group": self.timeseries_group.id,
                "time_step": "",
            }
        )
        assert serializer.is_valid(), serializer.errors
        self.assertEqual(serializer.validated_data["type"], 100)

    def test_type_deserialization_for_checked(self):
        serializer = TimeseriesSerializer(
            data={
                "type": "Checked",
                "timeseries_group": self.timeseries_group.id,
                "time_step": "",
            }
        )
        assert serializer.is_valid(), serializer.errors
        self.assertEqual(serializer.validated_data["type"], 200)


class TimeseriesSerializerUniqueTypeTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.timeseries_group = mommy.make(
            models.TimeseriesGroup,
            variable__descr="Temperature",
        )

    def test_only_one_initial_timeseries_per_group(self):
        self._create_timeseries(models.Timeseries.INITIAL)
        self.assertFalse(self._get_serializer("Initial").is_valid())

    def test_only_one_checked_timeseries_per_group(self):
        self._create_timeseries(models.Timeseries.CHECKED)
        self.assertFalse(self._get_serializer("Checked").is_valid())

    def test_only_one_regularized_timeseries_per_group(self):
        self._create_timeseries(models.Timeseries.REGULARIZED)
        self.assertFalse(self._get_serializer("Regularized").is_valid())

    def _create_timeseries(self, type):
        """Create a time series of the specified type with empty time step."""
        self.timeseries = mommy.make(
            models.Timeseries,
            timeseries_group=self.timeseries_group,
            type=type,
            time_step="",
        )

    def _get_serializer(self, type):
        """Create a serializer with the specified type and hourly time step.

        If the serializer had the same time step as the one used in
        _create_timeseries(), then the serializer would be invalid because of violation
        of the unique key (timeseries_group, type, time_step). We choose a different
        time step so that it won't be invalid for this reason. We want to check whether
        it's invalid because of attempting to create two initial (or two checked, or two
        regularized) time series for the same time series group.
        """
        return TimeseriesSerializer(
            data={
                "type": type,
                "timeseries_group": self.timeseries_group.id,
                "time_step": "H",
            }
        )
