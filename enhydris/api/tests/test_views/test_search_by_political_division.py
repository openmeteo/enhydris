from unittest import skipIf

from django.db import connections
from django.db.utils import DEFAULT_DB_ALIAS
from rest_framework.test import APITestCase

from model_mommy import mommy

from enhydris import models


def check_if_connected_to_old_sqlite():
    """Return True if connected to sqlite<3.8.3

    Used to skip the tests, notably on Travis, which currently runs an old sqlite
    version.

    The correct way would have been to remove the functionality, not just skip
    the tests, because the functionality is still there and will cause an
    internal server error, but this would be too much work given that we use
    SQLite only for development.
    """
    try:
        from django.contrib.gis.db.backends.spatialite import base
        import sqlite3
    except ImportError:
        return False
    if not isinstance(connections[DEFAULT_DB_ALIAS], base.DatabaseWrapper):
        return False
    major, minor, micro = [int(x) for x in sqlite3.sqlite_version.split(".")[:3]]
    return (
        (major < 3)
        or (major == 3 and minor < 8)
        or (major == 3 and minor == 8 and micro < 3)
    )


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


@skipIf(check_if_connected_to_old_sqlite(), "Use sqlite>=3.8.3")
class StationSearchBy2ndLevelPoliticalDivisionTestCase(TestCaseBase):
    def setUp(self):
        super().setUp()
        self.response = self.client.get(
            "/api/Station/?",
            {"q": "political_division:Epirus"},
        )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_number_of_results(self):
        self.assertEqual(len(self.response.json()["results"]), 1)

    def test_results(self):
        self.assertEqual(self.response.json()["results"][0]["name"], "Komboti")


@skipIf(check_if_connected_to_old_sqlite(), "Use sqlite>=3.8.3")
class StationSearchBy3rdLevelPoliticalDivisionTestCase(TestCaseBase):
    def setUp(self):
        super().setUp()
        self.response = self.client.get(
            "/api/Station/?",
            {"q": "political_division:earth"},
        )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_number_of_results(self):
        self.assertEqual(len(self.response.json()["results"]), 1)

    def test_results(self):
        self.assertEqual(self.response.json()["results"][0]["name"], "Tharbad")
