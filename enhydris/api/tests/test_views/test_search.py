from abc import ABC, abstractmethod

from django.conf import settings
from django.contrib.gis.geos import Point
from django.test import override_settings
from rest_framework.test import APITestCase

from model_mommy import mommy

from enhydris import models


class SearchTestCaseBase(ABC):
    """A test case base that checks whether a search returns correct result.

    Use like this:
        class MySearchTestCase(SearchTestCaseBase, APITestCase):
            search_term = "hello:world"
            search_result = "planet"

            def _create_models(self):
                # Create models such that when searching for "hello:world" the result
                # will be a single station with name "planet".
    """

    status_code = 200
    number_of_results = 1

    def setUp(self):
        self._create_models()
        self.response = self.client.get("/api/stations/", {"q": self.search_term})

    @abstractmethod
    def _create_models(self):
        pass

    def test_status_code(self):
        self.assertEqual(self.response.status_code, self.status_code)

    def test_number_of_results(self):
        if self.status_code == 200:
            self.assertEqual(
                len(self.response.json()["results"]), self.number_of_results
            )

    def test_results(self):
        if self.status_code != 200:
            return
        if self.number_of_results == 1:
            self.assertEqual(
                self.response.json()["results"][0]["name"], self.search_result
            )
        else:
            result_names = {r["name"] for r in self.response.json()["results"]}
            self.assertEqual(result_names, self.search_result)


class SearchByNameTestCase(SearchTestCaseBase, APITestCase):
    search_term = "hobbiton"
    search_result = "Hobbiton"

    def _create_models(self):
        mommy.make(models.Station, name="Hobbiton")
        mommy.make(models.Station, name="Sélune")


class SearchByNameWithAccentsTestCase(SearchByNameTestCase):
    search_term = "selune"
    search_result = "Sélune"


class SearchByShortNameTestCase(SearchTestCaseBase, APITestCase):
    search_term = "hobbiton"
    search_result = "1"

    def _create_models(self):
        mommy.make(models.Station, short_name="Hobbiton", name="1")
        mommy.make(models.Station, short_name="Sélune", name="2")


class SearchByShortNameWithAccentsTestCase(SearchByShortNameTestCase):
    search_term = "selune"
    search_result = "2"


class SearchByRemarksTestCase(SearchTestCaseBase, APITestCase):
    search_term = "very"
    search_result = "Hobbiton"

    def _create_models(self):
        mommy.make(models.Station, remarks="Very important station", name="Hobbiton")
        mommy.make(models.Station, remarks="Station très important", name="Rivendell")


class SearchByRemarksWithAccentsTestCase(SearchByRemarksTestCase):
    search_term = "tres"
    search_result = "Rivendell"


class SearchByWaterDivisionTestCase(SearchTestCaseBase, APITestCase):
    search_term = "water_division:ondor"
    search_result = "Pelargir"

    def _create_models(self):
        mommy.make(models.Station, water_division__name="Sélune", name="Ducey")
        mommy.make(models.Station, water_division__name="Gondor", name="Pelargir")


class SearchByWaterDivisionWithAccentsTestCase(SearchByWaterDivisionTestCase):
    search_term = "water_division:elu"
    search_result = "Ducey"


class SearchGeneralByWaterDivisionTestCase(SearchByWaterDivisionTestCase):
    search_term = "ondor"
    search_result = "Pelargir"


class SearchGeneralByWaterDivisionWithAccentsTestCase(SearchByWaterDivisionTestCase):
    search_term = "elu"
    search_result = "Ducey"


class SearchByWaterBasinTestCase(SearchTestCaseBase, APITestCase):
    search_term = "water_basin:andu"
    search_result = "Hobbiton"

    def _create_models(self):
        mommy.make(models.Station, water_basin__name="Baranduin", name="Hobbiton")
        mommy.make(models.Station, water_basin__name="Lhûn", name="Mithlond")


class SearchByWaterBasinWithAccentsTestCase(SearchByWaterBasinTestCase):
    search_term = "water_basin:hun"
    search_result = "Mithlond"


class SearchGeneralByWaterBasinTestCase(SearchByWaterBasinTestCase):
    search_term = "andu"
    search_result = "Hobbiton"


class SearchGeneralByWaterBasinWithAccentsTestCase(SearchByWaterBasinTestCase):
    search_term = "hun"
    search_result = "Mithlond"


language_settings = {
    "LANGUAGE_CODE": "en",
    "PARLER_LANGUAGES": {
        settings.SITE_ID: ({"code": "en"}, {"code": "fr"}),
        "default": {"fallbacks": ["en"], "hide_untranslated": False},
    },
}


@override_settings(**language_settings)
class SearchByVariableTestCase(SearchTestCaseBase, APITestCase):
    search_term = "variable:rain"
    search_result = "Hobbiton"

    def _create_models(self):
        station1 = mommy.make(models.Station, name="Hobbiton")
        station2 = mommy.make(models.Station, name="Mithlond")
        self._create_timeseries(station1, "Rain", "Pluie")
        self._create_timeseries(station2, "Humidity", "Humidité")

    def _create_timeseries(self, station, var_en, var_fr):
        timeseries = mommy.make(models.Timeseries, gentity=station)
        timeseries.variable.set_current_language("en")
        timeseries.variable.descr = var_en
        timeseries.variable.set_current_language("fr")
        timeseries.variable.descr = var_fr
        timeseries.variable.save()


@override_settings(**language_settings)
class SearchByVariableWithAccentsTestCase(SearchByVariableTestCase):
    search_term = "variable:hûmiDIte"
    search_result = "Mithlond"


@override_settings(**language_settings)
class SearchByVariableInInactiveTranslation(SearchByVariableTestCase):
    def setUp(self):
        self.client.cookies.load({settings.LANGUAGE_COOKIE_NAME: "fr"})
        super().setUp()


class SearchByTsOnlyTestCase(SearchTestCaseBase, APITestCase):
    search_term = "ts_only:"
    search_result = "Hobbiton"

    def _create_models(self):
        station1 = mommy.make(models.Station, name="Hobbiton")
        mommy.make(models.Timeseries, gentity=station1)
        mommy.make(models.Station, name="Mithlond")


class SearchInTimeseriesRemarksTestCase(SearchTestCaseBase, APITestCase):
    search_term = "really important time series"
    search_result = "Mithlond"

    def _create_models(self):
        station1 = mommy.make(models.Station, name="Hobbiton")
        mommy.make(
            models.Timeseries,
            gentity=station1,
            remarks="Cette série chronologique est vraiment importante",
        )
        station2 = mommy.make(models.Station, name="Mithlond")
        mommy.make(
            models.Timeseries,
            gentity=station2,
            remarks="This time series is really important",
        )


class SearchInTimeseriesRemarksWithAccentsTestCase(SearchInTimeseriesRemarksTestCase):
    search_term = "cette serie"
    search_result = "Hobbiton"


class SearchByBboxTestCase(SearchTestCaseBase, APITestCase):
    search_term = "bbox:21,39,22,40"
    search_result = "Komboti"

    def _create_models(self):
        mommy.make(
            models.Station, point=Point(x=21.0607, y=39.0952, srid=4326), name="Komboti"
        )
        mommy.make(
            models.Station, point=Point(x=20.7085, y=38.8336, srid=4326), name="Lefkada"
        )
