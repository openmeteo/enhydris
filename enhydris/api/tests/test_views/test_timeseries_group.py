from rest_framework.test import APITestCase

from model_mommy import mommy

from enhydris import models


class TimeseriesGroupListTestCase(APITestCase):
    def setUp(self):
        self.station = mommy.make(models.Station, name="Hobbiton")
        self.timeseries_group = mommy.make(
            models.TimeseriesGroup, name="Temperature", gentity=self.station
        )
        self.response = self.client.get(
            f"/api/stations/{self.station.id}/timeseriesgroups/"
        )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_number_of_returned_items(self):
        self.assertEqual(len(self.response.json()["results"]), 1)

    def test_name(self):
        self.assertEqual(self.response.json()["results"][0]["name"], "Temperature")
