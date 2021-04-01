from unittest.mock import patch

from rest_framework.test import APITestCase

from model_mommy import mommy

from enhydris import models


class StationSortDefaultTestCase(APITestCase):
    def setUp(self):
        mommy.make(models.Station, name="Rivendell")
        mommy.make(models.Station, name="Hobbiton")
        self.response = self.client.get("/api/stations/")

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_number_of_results(self):
        self.assertEqual(len(self.response.json()["results"]), 2)

    def test_hobbiton_is_first(self):
        self.assertEqual(self.response.json()["results"][0]["name"], "Hobbiton")


class StationSortByReverseNameTestCase(APITestCase):
    def setUp(self):
        mommy.make(models.Station, name="Rivendell")
        mommy.make(models.Station, name="Hobbiton")
        self.response = self.client.get("/api/stations/?sort=-name")

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_number_of_results(self):
        self.assertEqual(len(self.response.json()["results"]), 2)

    def test_rivendell_is_first(self):
        self.assertEqual(self.response.json()["results"][0]["name"], "Rivendell")


@patch(
    "django.db.models.query.QuerySet.order_by",
    return_value=models.Station.objects.none(),
)
class StationSortWithInvalidParametersTestCase(APITestCase):
    def test_invalid_and_duplicate_fields_are_removed(self, m):
        self.client.get(
            "/api/stations/?sort=-name&sort=name&sort=nonexistent&sort=remarks"
        )
        m.assert_called_once_with("-name", "remarks")

    def test_empty_sort_field_is_ignored(self, m):
        self.client.get("/api/stations/?sort=")
        m.assert_not_called()
