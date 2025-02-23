from io import StringIO

from rest_framework.test import APITestCase

from model_bakery import baker

from enhydris import models
from enhydris.tests import ClearCacheMixin

from .test_search import SearchTestCaseBase


class SearchWithYearExistingInOneStationTest(
    ClearCacheMixin, SearchTestCaseBase, APITestCase
):
    search_term = "ts_has_years:2005,2012,2016"
    search_result = "Tharbad"

    def _create_models(self):
        komboti = baker.make(models.Station, name="Komboti")
        tharbad = baker.make(models.Station, name="Tharbad")
        self.komboti_temperature = self._make_timeseries(
            komboti, "Temperature", "2005-03-23 18:20,5,\r\n2012-03-24 18:25,6,\r\n"
        )
        self.komboti_rain = self._make_timeseries(
            komboti, "Rain", "2005-03-23 18:20,5,\r\n2011-03-24 18:25,6,\r\n"
        )
        self.tharbad_temperature = self._make_timeseries(
            tharbad, "Temperature", "2005-03-23 18:20,5,\r\n2012-03-24 18:25,6,\r\n"
        )
        self.tharbad_rain = self._make_timeseries(
            tharbad, "Rain", "2005-03-23 18:20,5,\r\n2016-03-24 18:25,6,\r\n"
        )

    def _make_timeseries(self, station, variable_descr, datastr):
        result = baker.make(
            models.Timeseries,
            timeseries_group__gentity=station,
            timeseries_group__variable__descr=variable_descr,
        )
        result.set_data(StringIO(datastr), default_timezone="Etc/GMT-2")
        return result


class SearchWithYearsExistingInAllStationsTest(SearchWithYearExistingInOneStationTest):
    search_term = "ts_has_years:2005,2012"
    search_result = {"Komboti", "Tharbad"}
    number_of_results = 2


class SearchWithYearsExistingNowhereTest(SearchWithYearExistingInOneStationTest):
    search_term = "ts_has_years:2005,2012,2018"
    search_result = set()
    number_of_results = 0


class SearchWithGarbageTest(SearchWithYearExistingInOneStationTest):
    search_term = "ts_has_years:hello,world"
    status_code = 404
