from django.conf import settings
from django.contrib.gis.geos import Point
from django.test import override_settings
from rest_framework.test import APITestCase

from model_mommy import mommy

from enhydris import models


class StationSearchByOwnerTestCase(APITestCase):
    def setUp(self):
        owner1 = mommy.make(models.Organization, name="The Assassination Bureau, Ltd")
        owner2 = mommy.make(models.Organization, name="United Federation of Planets")
        mommy.make(models.Station, owner=owner1, name="Hobbiton")
        mommy.make(models.Station, owner=owner2, name="Rivendell")
        self.response = self.client.get("/api/stations/", {"q": "owner:assassination"})

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
        self.response = self.client.get("/api/stations/", {"q": "type:elf"})

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
        self.response = self.client.get("/api/stations/", {"q": "water_division:ordor"})

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
        self.response = self.client.get("/api/stations/", {"q": "water_basin:andu"})

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_number_of_results(self):
        self.assertEqual(len(self.response.json()["results"]), 1)

    def test_results(self):
        self.assertEqual(self.response.json()["results"][0]["name"], "Hobbiton")


language_settings = {
    "LANGUAGE_CODE": "en",
    "PARLER_LANGUAGES": {
        settings.SITE_ID: ({"code": "en"}, {"code": "el"}),
        "default": {"fallbacks": ["en"], "hide_untranslated": False},
    },
}


@override_settings(**language_settings)
class StationSearchByVariableTestCase(APITestCase):
    def setUp(self):
        station1 = mommy.make(models.Station, name="Hobbiton")
        station2 = mommy.make(models.Station, name="Mithlond")
        self._create_timeseries(station1, "Rain", "Βροχόπτωση")
        self._create_timeseries(station2, "Temperature", "Θερμοκρασία")
        self.response = self.client.get("/api/stations/", {"q": "variable:rain"})

    def _create_timeseries(self, station, var_en, var_el):
        timeseries = mommy.make(models.Timeseries, gentity=station)
        timeseries.variable.set_current_language("en")
        timeseries.variable.descr = var_en
        timeseries.variable.set_current_language("el")
        timeseries.variable.descr = var_el
        timeseries.variable.save()

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_number_of_results(self):
        self.assertEqual(len(self.response.json()["results"]), 1)

    def test_results(self):
        self.assertEqual(self.response.json()["results"][0]["name"], "Hobbiton")


@override_settings(**language_settings)
class StationSearchByVariableInInactiveTranslation(StationSearchByVariableTestCase):
    def setUp(self):
        self.client.cookies.load({settings.LANGUAGE_COOKIE_NAME: "el"})
        super().setUp()


class StationSearchByTsOnlyTestCase(APITestCase):
    def setUp(self):
        station1 = mommy.make(models.Station, name="Hobbiton")
        mommy.make(models.Timeseries, gentity=station1)
        mommy.make(models.Station, name="Mithlond")
        self.response = self.client.get("/api/stations/", {"q": "ts_only:"})

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
            "/api/stations/", {"q": "really important time series"}
        )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_number_of_results(self):
        self.assertEqual(len(self.response.json()["results"]), 1)

    def test_results(self):
        self.assertEqual(self.response.json()["results"][0]["name"], "Mithlond")


class StationSearchByBboxTestCase(APITestCase):
    def setUp(self):
        mommy.make(
            models.Station, point=Point(x=21.0607, y=39.0952, srid=4326), name="Komboti"
        )
        mommy.make(
            models.Station, point=Point(x=20.7085, y=38.8336, srid=4326), name="Lefkada"
        )
        self.response = self.client.get("/api/stations/", {"q": "bbox:21,39,22,40"})

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_number_of_results(self):
        self.assertEqual(len(self.response.json()["results"]), 1)

    def test_results(self):
        self.assertEqual(self.response.json()["results"][0]["name"], "Komboti")
