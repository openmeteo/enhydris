from rest_framework.test import APITestCase

from model_mommy import mommy

from enhydris import models


class StationSearchByOwnerTestCase(APITestCase):
    def setUp(self):
        owner1 = mommy.make(models.Organization, name="The Assassination Bureau, Ltd")
        owner2 = mommy.make(models.Organization, name="United Federation of Planets")
        mommy.make(models.Station, owner=owner1, name="Hobbiton")
        mommy.make(models.Station, owner=owner2, name="Rivendell")
        self.response = self.client.get("/api/Station/", {"q": "owner:assassination"})

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_number_of_results(self):
        self.assertEqual(len(self.response.json()["results"]), 1)

    def test_results(self):
        self.assertEqual(self.response.json()["results"][0]["name"], "Hobbiton")


class StationSearchByTypeTestCase(APITestCase):
    def setUp(self):
        mommy.make(models.Station, stype__descr=["Hydrometric"], name="Hobbiton")
        mommy.make(models.Station, stype__descr=["Elfometric"], name="Rivendell")
        self.response = self.client.get("/api/Station/", {"q": "type:elf"})

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_number_of_results(self):
        self.assertEqual(len(self.response.json()["results"]), 1)

    def test_results(self):
        self.assertEqual(self.response.json()["results"][0]["name"], "Rivendell")


class StationSearchByWaterDivisionTestCase(APITestCase):
    def setUp(self):
        mommy.make(models.Station, water_division__name="Mordor", name="Gorgoroth")
        mommy.make(models.Station, water_division__name="Gondor", name="Pelargir")
        self.response = self.client.get("/api/Station/", {"q": "water_division:ordor"})

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_number_of_results(self):
        self.assertEqual(len(self.response.json()["results"]), 1)

    def test_results(self):
        self.assertEqual(self.response.json()["results"][0]["name"], "Gorgoroth")


class StationSearchByWaterBasinTestCase(APITestCase):
    def setUp(self):
        mommy.make(models.Station, water_basin__name="Baranduin", name="Hobbiton")
        mommy.make(models.Station, water_basin__name="Lhûn", name="Mithlond")
        self.response = self.client.get("/api/Station/", {"q": "water_basin:andu"})

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_number_of_results(self):
        self.assertEqual(len(self.response.json()["results"]), 1)

    def test_results(self):
        self.assertEqual(self.response.json()["results"][0]["name"], "Hobbiton")


class StationSearchByVariableTestCase(APITestCase):
    def setUp(self):
        station1 = mommy.make(models.Station, name="Hobbiton")
        station2 = mommy.make(models.Station, name="Mithlond")
        mommy.make(models.Timeseries, gentity=station1, variable__descr="Rain")
        mommy.make(models.Timeseries, gentity=station2, variable__descr="Temperature")
        self.response = self.client.get("/api/Station/", {"q": "variable:rain"})

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_number_of_results(self):
        self.assertEqual(len(self.response.json()["results"]), 1)

    def test_results(self):
        self.assertEqual(self.response.json()["results"][0]["name"], "Hobbiton")


class StationSearchByTsOnlyTestCase(APITestCase):
    def setUp(self):
        station1 = mommy.make(models.Station, name="Hobbiton")
        mommy.make(models.Timeseries, gentity=station1)
        mommy.make(models.Station, name="Mithlond")
        self.response = self.client.get("/api/Station/", {"q": "ts_only:"})

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_number_of_results(self):
        self.assertEqual(len(self.response.json()["results"]), 1)

    def test_results(self):
        self.assertEqual(self.response.json()["results"][0]["name"], "Hobbiton")


class StationSearchInTimeseriesRemarksTestCase(APITestCase):
    def setUp(self):
        station1 = mommy.make(models.Station, name="Hobbiton")
        mommy.make(
            models.Timeseries,
            gentity=station1,
            remarks="This is an extremely important time series",
        )
        station2 = mommy.make(models.Station, name="Mithlond")
        mommy.make(
            models.Timeseries,
            gentity=station2,
            remarks="This time series is really important",
        )
        self.response = self.client.get(
            "/api/Station/", {"q": "really important time series"}
        )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_number_of_results(self):
        self.assertEqual(len(self.response.json()["results"]), 1)

    def test_results(self):
        self.assertEqual(self.response.json()["results"][0]["name"], "Mithlond")
