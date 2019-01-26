from rest_framework.test import APITestCase

from model_mommy import mommy

from enhydris import models


class TestCaseBase(APITestCase):
    def setUp(self):
        mommy.make(
            models.Station,
            name="Komboti",
            political_division__name="Arta",
            political_division__parent__name="Epirus",
            political_division__parent__parent__name="Greece",
        )
        mommy.make(
            models.Station,
            name="Tharbad",
            political_division__name="Cardolan",
            political_division__parent__name="Eriador",
            political_division__parent__parent__name="Middle Earth",
        )


class StationSearchBy2ndLevelPoliticalDivisionTestCase(TestCaseBase):
    def setUp(self):
        super().setUp()
        self.response = self.client.get(
            "/api/stations/", {"q": "political_division:Epirus"}
        )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_number_of_results(self):
        self.assertEqual(len(self.response.json()["results"]), 1)

    def test_results(self):
        self.assertEqual(self.response.json()["results"][0]["name"], "Komboti")


class StationSearchBy3rdLevelPoliticalDivisionTestCase(TestCaseBase):
    def setUp(self):
        super().setUp()
        self.response = self.client.get(
            "/api/stations/", {"q": "political_division:earth"}
        )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_number_of_results(self):
        self.assertEqual(len(self.response.json()["results"]), 1)

    def test_results(self):
        self.assertEqual(self.response.json()["results"][0]["name"], "Tharbad")
