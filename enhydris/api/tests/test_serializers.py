from django.contrib.auth.models import User
from django.utils import translation
from rest_framework.test import APITestCase

from model_mommy import mommy

from enhydris import models
from enhydris.api.serializers import StationSerializer, TimeseriesSerializer


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


class TimeseriesSerializerTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.timeseries_group = mommy.make(models.TimeseriesGroup)

    def test_type_serialization_for_raw(self):
        serializer = TimeseriesSerializer(models.Timeseries(type=100))
        self.assertEqual(serializer.data["type"], "Raw")

    def test_type_serialization_for_checked(self):
        serializer = TimeseriesSerializer(models.Timeseries(type=200))
        self.assertEqual(serializer.data["type"], "Checked")

    def test_type_serialization_for_raw_when_nondefault_language(self):
        serializer = TimeseriesSerializer(models.Timeseries(type=100))
        with translation.override("el"):
            self.assertEqual(serializer.data["type"], "Raw")

    def test_type_deserialization_for_raw(self):
        serializer = TimeseriesSerializer(
            data={
                "type": "Raw",
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
