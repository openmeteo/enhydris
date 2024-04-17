from django.contrib.auth.models import User
from django.test import override_settings
from rest_framework.test import APITestCase

from enhydris.tests import TestTimeseriesMixin


@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=True)
class AuthenticationRequiredTestCase(TestTimeseriesMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_user("alice", password="topsecret", is_superuser=True)
        cls._create_test_timeseries()

    def setUp(self):
        response = self.client.post(
            "/api/auth/login/",
            data={"username": "alice", "password": "topsecret"},
        )
        self.token = response.json()["key"]

        # Ensure we aren't logged on
        self.client.credentials()
        self.client.logout()

    def _use_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token}")

    def test_can_get_stations_when_authenticated(self):
        self._use_token()
        response = self.client.get("/api/stations/")
        self.assertEqual(response.status_code, 200)

    def test_cannot_get_stations_when_not_authenticated(self):
        response = self.client.get("/api/stations/")
        self.assertEqual(response.status_code, 401)

    def test_can_get_variables_when_authenticated(self):
        self._use_token()
        response = self.client.get("/api/variables/")
        self.assertEqual(response.status_code, 200)

    def test_cannot_get_variables_when_not_authenticated(self):
        response = self.client.get("/api/variables/")
        self.assertEqual(response.status_code, 401)

    def test_can_get_timeseries_groups_when_authenticated(self):
        self._use_token()
        response = self.client.get(f"/api/stations/{self.station.id}/timeseriesgroups/")
        self.assertEqual(response.status_code, 200)

    def test_cannot_get_timeseries_groups_when_not_authenticated(self):
        response = self.client.get(f"/api/stations/{self.station.id}/timeseriesgroups/")
        self.assertEqual(response.status_code, 401)

    def test_can_get_timeseries_when_authenticated(self):
        self._use_token()
        response = self.client.get(
            f"/api/stations/{self.station.id}/timeseriesgroups/"
            f"{self.timeseries_group.id}/timeseries/"
        )
        self.assertEqual(response.status_code, 200)

    def test_cannot_get_timeseries_when_not_authenticated(self):
        response = self.client.get(
            f"/api/stations/{self.station.id}/timeseriesgroups/"
            f"{self.timeseries_group.id}/timeseries/"
        )
        self.assertEqual(response.status_code, 401)
