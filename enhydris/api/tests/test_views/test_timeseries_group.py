from django.contrib.auth.models import User
from django.test import override_settings
from rest_framework.test import APITestCase

from model_bakery import baker

from enhydris import models


@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class TimeseriesGroupListTestCase(APITestCase):
    def setUp(self):
        self.station = baker.make(models.Station, name="Hobbiton")
        self.timeseries_group = baker.make(
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


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class TimeseriesGroupPostTestCase(APITestCase):
    def setUp(self):
        self.user1 = baker.make(User, is_active=True, is_superuser=False)
        self.user2 = baker.make(User, is_active=True, is_superuser=False)
        self.variable = baker.make(models.Variable, descr="Temperature")
        self.unit_of_measurement = baker.make(models.UnitOfMeasurement)
        self.station = baker.make(models.Station, creator=self.user1)
        self.station2 = baker.make(models.Station, creator=self.user1)
        self.timeseries_group = baker.make(models.TimeseriesGroup, gentity=self.station)

    def _create_timeseries_group(self, **kwargs):
        return self.client.post(
            f"/api/stations/{self.station.id}/timeseriesgroups/",
            data={
                "name": "Great time series group",
                "gentity": self.station.id,
                "variable": self.variable.id,
                "unit_of_measurement": self.unit_of_measurement.id,
                "precision": 2,
                **kwargs,
            },
        )

    def _update_timeseries_group(self, **kwargs):
        return self.client.put(
            f"/api/stations/{self.station.id}/timeseriesgroups/"
            f"{self.timeseries_group.id}/",
            data={
                "name": "Great time series group",
                "gentity": self.station.id,
                "variable": self.variable.id,
                "unit_of_measurement": self.unit_of_measurement.id,
                "precision": 2,
                **kwargs,
            },
        )

    def test_unauthenticated_user_is_denied_permission_to_create_timeseries_group(self):
        self.assertEqual(self._create_timeseries_group().status_code, 401)

    def test_unauthorized_user_is_denied_permission_to_create_timeseries_group(self):
        self.client.force_authenticate(user=self.user2)
        self.assertEqual(self._create_timeseries_group().status_code, 403)

    def test_authorized_user_can_create_timeseries_group(self):
        self.client.force_authenticate(user=self.user1)
        self.assertEqual(self._create_timeseries_group().status_code, 201)

    def test_returns_error_if_wrong_gentity(self):
        self.client.force_authenticate(user=self.user1)
        self.assertEqual(
            self._create_timeseries_group(gentity=self.station2.id).status_code, 400
        )

    def test_unauthenticated_user_is_denied_permission_to_update_timeseries_group(self):
        self.assertEqual(self._update_timeseries_group().status_code, 401)

    def test_unauthorized_user_is_denied_permission_to_update_timeseries_group(self):
        self.client.force_authenticate(user=self.user2)
        self.assertEqual(self._update_timeseries_group().status_code, 403)

    def test_authorized_user_can_update_timeseries_group(self):
        self.client.force_authenticate(user=self.user1)
        self.assertEqual(self._update_timeseries_group().status_code, 200)


class TimeseriesGroupUpdateValidationTestCase(APITestCase):
    def setUp(self):
        self.user = baker.make(User, is_active=True, is_superuser=True)
        self.station = baker.make(models.Station, creator=self.user)
        self.other_station = baker.make(models.Station)
        self.timeseries_group = baker.make(models.TimeseriesGroup, gentity=self.station)
        self.url = f"/api/stations/{self.station.id}/timeseriesgroups/{self.timeseries_group.id}/"
        self.client.force_authenticate(user=self.user)

    def test_patch_cannot_change_station(self):
        response = self.client.patch(
            self.url, data={"gentity": self.other_station.id}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_put_cannot_change_station(self):
        response = self.client.put(
            self.url,
            data={
                "name": self.timeseries_group.name,
                "gentity": self.other_station.id,
                "variable": self.timeseries_group.variable.id,
                "unit_of_measurement": self.timeseries_group.unit_of_measurement.id,
                "precision": self.timeseries_group.precision,
                "hidden": self.timeseries_group.hidden,
                "remarks": self.timeseries_group.remarks,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
