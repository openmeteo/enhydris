from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from model_mommy import mommy

from enhydris import models
from enhydris.api.serializers import StationSerializer


class StationSerializerTestCase(APITestCase):
    def setUp(self):
        station = mommy.make(
            models.Station,
            name="hello",
            water_basin__name="Baraduin",
            water_division__name="Middle Earth",
            political_division__name="Eriador",
            stype=[mommy.make(models.StationType, descr="Smurfy")],
            overseers=[mommy.make(models.Person, last_name="Baggins")],
            maintainers=[mommy.make(User, username="Bilbo")],
        )
        self.serializer = StationSerializer(station)

    def test_name(self):
        self.assertEqual(self.serializer.data["name"], "hello")

    def test_water_basin(self):
        self.assertEqual(self.serializer.data["water_basin"]["name"], "Baraduin")

    def test_water_division(self):
        self.assertEqual(self.serializer.data["water_division"]["name"], "Middle Earth")

    def test_political_division(self):
        self.assertEqual(self.serializer.data["political_division"]["name"], "Eriador")

    def test_stype(self):
        self.assertEqual(self.serializer.data["stype"][0]["descr"], "Smurfy")

    def test_overseer(self):
        self.assertEqual(self.serializer.data["overseers"][0]["last_name"], "Baggins")

    def test_maintainer(self):
        self.assertEqual(self.serializer.data["maintainers"][0]["username"], "Bilbo")


class StationSerializerNestedValidationTestCase(APITestCase):
    def setUp(self):
        mommy.make(models.Person, id=55)
        mommy.make(models.WaterBasin, id=42)
        mommy.make(models.WaterDivision, id=43)
        mommy.make(models.PoliticalDivision, id=44)
        mommy.make(models.StationType, id=203)
        mommy.make(models.Person, id=204)
        mommy.make(User, id=205)
        self.base_data = {
            "name": "Hobbiton",
            "copyright_years": "2018",
            "copyright_holder": "Bilbo Baggins",
            "owner": 55,
            "point": "SRID=4326;POINT (20.94565 39.12102)",
        }

    def test_correct_nested_water_basin_validates(self):
        serializer = StationSerializer(
            data={**self.base_data, "water_basin": {"id": 42}}
        )
        self.assertTrue(serializer.is_valid())

    def test_incorrect_nested_water_basin_does_not_validate(self):
        serializer = StationSerializer(
            data={**self.base_data, "water_basin": {"di": 42}}
        )
        self.assertFalse(serializer.is_valid())

    def test_correct_nested_water_division_validates(self):
        serializer = StationSerializer(
            data={**self.base_data, "water_division": {"id": 43}}
        )
        self.assertTrue(serializer.is_valid())

    def test_incorrect_nested_water_division_does_not_validate(self):
        serializer = StationSerializer(
            data={**self.base_data, "water_division": {"di": 43}}
        )
        self.assertFalse(serializer.is_valid())

    def test_correct_nested_political_division_validates(self):
        serializer = StationSerializer(
            data={**self.base_data, "political_division": {"id": 44}}
        )
        self.assertTrue(serializer.is_valid())

    def test_incorrect_nested_political_division_does_not_validate(self):
        serializer = StationSerializer(
            data={**self.base_data, "political_division": {"di": 44}}
        )
        self.assertFalse(serializer.is_valid())

    def test_correct_nested_stype_validates(self):
        serializer = StationSerializer(data={**self.base_data, "stype": [{"id": 203}]})
        self.assertTrue(serializer.is_valid())

    def test_incorrect_nested_stype_does_not_validate(self):
        serializer = StationSerializer(data={**self.base_data, "stype": [{"di": 203}]})
        self.assertFalse(serializer.is_valid())

    def test_correct_nested_overseers_validates(self):
        serializer = StationSerializer(
            data={**self.base_data, "overseers": [{"id": 204}]}
        )
        self.assertTrue(serializer.is_valid())

    def test_incorrect_nested_overseers_does_not_validate(self):
        serializer = StationSerializer(
            data={**self.base_data, "overseers": [{"di": 204}]}
        )
        self.assertFalse(serializer.is_valid())

    def test_correct_nested_maintainers_validates(self):
        serializer = StationSerializer(
            data={**self.base_data, "maintainers": [{"id": 205}]}
        )
        serializer.is_valid(raise_exception=True)
        self.assertTrue(serializer.is_valid())

    def test_incorrect_nested_maintainers_does_not_validate(self):
        serializer = StationSerializer(
            data={**self.base_data, "maintainers": [{"di": 205}]}
        )
        self.assertFalse(serializer.is_valid())
