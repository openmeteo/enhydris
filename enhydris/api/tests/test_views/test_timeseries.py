import datetime as dt
import json
from io import StringIO
from typing import Any
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User
from django.test.utils import override_settings
from rest_framework.test import APITestCase

import numpy as np
import pandas as pd
from htimeseries import HTimeseries
from model_bakery import baker

from enhydris import models
from enhydris.tests import TimeseriesDataMixin


@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class Tsdata404TestCase(APITestCase):
    def setUp(self):
        self.station = baker.make(models.Station)
        self.timeseries_group = baker.make(models.TimeseriesGroup, gentity=self.station)

    def test_get_nonexistent_timeseries(self):
        response = self.client.get(
            f"/api/stations/{self.station.pk}/timeseriesgroups/"
            f"{self.timeseries_group.pk}/timeseries/1234/data/"
        )
        self.assertEqual(response.status_code, 404)

    def test_post_nonexistent_timeseries(self):
        response = self.client.post(
            f"/api/stations/{self.station.pk}/timeseriesgroups/"
            f"{self.timeseries_group.pk}/timeseries/1235/data/"
        )
        self.assertEqual(response.status_code, 404)


@patch("enhydris.models.Timeseries.get_data", return_value=HTimeseries())
@override_settings(ENHYDRIS_ENABLE_TIMESERIES_DATA_VIEWERS=False)
@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class TsdataGetPermissionsTestCase(APITestCase):
    timeseries: models.Timeseries

    @classmethod
    def setUpTestData(cls):
        station = baker.make(models.Station, display_timezone="Etc/GMT-2")
        timeseries_group = baker.make(
            models.TimeseriesGroup,
            gentity=station,
            precision=2,
        )
        cls.timeseries = baker.make(
            models.Timeseries,
            timeseries_group=timeseries_group,
            publicly_available=False,
        )
        cls.url = (
            f"/api/stations/{station.pk}/timeseriesgroups/{timeseries_group.pk}/"
            f"timeseries/{cls.timeseries.pk}/data/"
        )

    def test_anonymous_user_is_denied_by_default(self, m: MagicMock):
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 401)

    def test_anonymous_user_is_accepted_if_publicly_available_is_true(
        self, m: MagicMock
    ):
        self.timeseries.publicly_available = True
        self.timeseries.save()
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 200)

    def test_logged_on_user_is_ok(self, m: MagicMock):
        self.user1 = baker.make(User, is_active=True, is_superuser=False)
        self.client.force_authenticate(user=self.user1)
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 200)


@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class GetDataTestCase(APITestCase, TimeseriesDataMixin):
    @classmethod
    def setUpTestData(cls):
        cls.create_timeseries(publicly_available=True)

    def _get_response(
        self,
        urlsuffix: str = "",
        station_id: int | None = None,
        timeseries_group_id: int | None = None,
    ):
        if station_id is None:
            station_id = self.station.pk
        if timeseries_group_id is None:
            timeseries_group_id = self.timeseries_group.pk
        return self.client.get(
            f"/api/stations/{station_id}/timeseriesgroups/"
            f"{timeseries_group_id}/timeseries/{self.timeseries.pk}/data/"
            f"{urlsuffix}"
        )

    def test_status_code(self):
        response = self._get_response()
        self.assertEqual(response.status_code, 200)

    def test_content_type(self):
        response = self._get_response()
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")

    def test_response_content(self):
        response = self._get_response()
        self.assertEqual(
            response.content.decode(),
            "2017-11-23 17:23,1.00,\r\n2018-11-25 01:00,2.00,\r\n",
        )

    def test_request_with_start_date(self):
        response = self._get_response(urlsuffix="?start_date=2017-11-23T17:24Z")
        self.assertEqual(response.content.decode(), "2018-11-25 01:00,2.00,\r\n")

    def test_response_content_in_other_timezone(self):
        response = self._get_response(urlsuffix="?timezone=UTC")
        self.assertEqual(
            response.content.decode(),
            "2017-11-23 15:23,1.00,\r\n2018-11-24 23:00,2.00,\r\n",
        )

    def test_wrong_station_id(self):
        response = self._get_response(station_id=self.station.pk + 1)
        self.assertEqual(response.status_code, 404)

    def test_wrong_timeseries_group_id(self):
        response = self._get_response(timeseries_group_id=self.timeseries_group.pk + 1)
        self.assertEqual(response.status_code, 404)


@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class GetDataInVariousFormatsTestCase(APITestCase, TimeseriesDataMixin):
    def setUp(self):
        super().setUp()
        self.create_timeseries(publicly_available=True)
        self.get_data_patch = patch(
            "enhydris.models.Timeseries.get_data", return_value=self.htimeseries
        )
        self.base_url = (
            f"/api/stations/{self.station.pk}/timeseriesgroups/"
            f"{self.timeseries_group.pk}/timeseries/{self.timeseries.pk}/data/"
        )

    def test_response_content_hts_version_2(self):
        with self.get_data_patch:
            response = self.client.get(self.base_url + "?fmt=hts2")
        self.assertTrue(response.content.decode().startswith("Version=2\r\n"))

    def test_response_headers_hts_version_2(self):
        with self.get_data_patch:
            response = self.client.get(self.base_url + "?fmt=hts2")
        self.assertEqual(
            response["Content-Type"], "text/vnd.openmeteo.timeseries; charset=utf-8"
        )
        self.assertEqual(
            response["Content-Disposition"],
            f'inline; filename="{self.timeseries.pk}.hts"',
        )

    def test_response_content_hts_version_5(self):
        with self.get_data_patch:
            response = self.client.get(self.base_url + "?fmt=hts")
        self.assertTrue(response.content.decode().startswith("Count=2\r\n"))

    def test_response_headers_hts_version_5(self):
        with self.get_data_patch:
            response = self.client.get(self.base_url + "?fmt=hts")
        self.assertEqual(
            response["Content-Type"], "text/vnd.openmeteo.timeseries; charset=utf-8"
        )
        self.assertEqual(
            response["Content-Disposition"],
            f'inline; filename="{self.timeseries.pk}.hts"',
        )

    def test_response_content_csv(self):
        with self.get_data_patch:
            response = self.client.get(self.base_url + "?fmt=csv")
        self.assertTrue(response.content.decode().startswith("2017-11-23 17:23,"))

    def test_response_headers_csv(self):
        with self.get_data_patch:
            response = self.client.get(self.base_url + "?fmt=csv")
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertEqual(
            response["Content-Disposition"],
            f'inline; filename="{self.timeseries.pk}.csv"',
        )

    def test_response_content_csv_default(self):
        with self.get_data_patch:
            response = self.client.get(self.base_url)
        self.assertTrue(response.content.decode().startswith("2017-11-23 17:23,"))

    def test_response_headers_csv_default(self):
        with self.get_data_patch:
            response = self.client.get(self.base_url)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertEqual(
            response["Content-Disposition"],
            f'inline; filename="{self.timeseries.pk}.csv"',
        )


@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
@patch("enhydris.models.Timeseries.insert_or_append_data")
class TsdataPostTestCase(APITestCase):
    def setUp(self):
        self.user = baker.make(User, username="admin", is_superuser=True)
        self.station = baker.make(models.Station)
        self.timeseries_group = baker.make(
            models.TimeseriesGroup, gentity=self.station, precision=2
        )
        self.timeseries = baker.make(
            models.Timeseries, timeseries_group=self.timeseries_group
        )

    def make_request(self, mode: str = ""):
        self.client.force_authenticate(user=self.user)
        data = {
            "timezone": "Etc/GMT-2",
            "timeseries_records": (
                "2017-11-23 17:23,1.000000,\r\n" "2018-11-25 01:00,2.000000,\r\n",
            ),
        }
        if mode:
            data["mode"] = mode
        self.response = self.client.post(
            f"/api/stations/{self.station.pk}/timeseriesgroups/{self.timeseries_group.pk}"
            f"/timeseries/{self.timeseries.pk}/data/",
            data=data,
        )

    def test_status_code(self, m: MagicMock):
        self.make_request()
        self.assertEqual(self.response.status_code, 204)

    def test_called_append_data(self, m: MagicMock):
        self.make_request()
        self.assertEqual(m.call_count, 1)

    def test_called_append_data_with_correct_arguments(self, m: MagicMock):
        self.make_request()
        self.assertEqual(
            m.call_args.args[0].getvalue(),
            "2017-11-23 17:23,1.000000,\r\n" "2018-11-25 01:00,2.000000,\r\n",
        )
        self.assertEqual(
            m.call_args.kwargs, {"default_timezone": "Etc/GMT-2", "append_only": True}
        )

    def test_disallows_wrong_values_of_mode(self, m: MagicMock):
        self.make_request(mode="invalid_mode")
        self.assertEqual(self.response.status_code, 400)

    def test_allows_insert_mode(self, m: MagicMock):
        self.make_request(mode="insert")
        self.assertEqual(
            m.call_args.args[0].getvalue(),
            "2017-11-23 17:23,1.000000,\r\n" "2018-11-25 01:00,2.000000,\r\n",
        )
        self.assertEqual(
            m.call_args.kwargs, {"default_timezone": "Etc/GMT-2", "append_only": False}
        )


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class TsdataPostAuthorizationTestCase(APITestCase):
    def setUp(self):
        self.user1 = baker.make(User, is_active=True, is_superuser=False)
        self.user2 = baker.make(User, is_active=True, is_superuser=False)
        self.station = baker.make(models.Station, creator=self.user1)
        self.timeseries_group = baker.make(
            models.TimeseriesGroup, gentity=self.station, precision=2
        )
        self.timeseries = baker.make(
            models.Timeseries, timeseries_group=self.timeseries_group
        )

    def _post_tsdata(self):
        return self.client.post(
            f"/api/stations/{self.station.pk}/timeseriesgroups"
            f"/{self.timeseries_group.pk}/timeseries/{self.timeseries.pk}/data/",
            data={
                "timezone": "Etc/GMT-2",
                "timeseries_records": (
                    "2017-11-23 17:23,1.000000,\r\n" "2018-11-25 01:00,2.000000,\r\n",
                ),
            },
        )

    @patch("enhydris.models.Timeseries.insert_or_append_data")
    def test_unauthenticated_user_is_denied_permission_to_post_tsdata(
        self, m: MagicMock
    ):
        self.assertEqual(self._post_tsdata().status_code, 401)

    @patch("enhydris.models.Timeseries.insert_or_append_data")
    def test_unauthorized_user_is_denied_permission_to_post_tsdata(self, m: MagicMock):
        self.client.force_authenticate(user=self.user2)
        self.assertEqual(self._post_tsdata().status_code, 403)

    @patch("enhydris.models.Timeseries.insert_or_append_data")
    def test_authorized_user_can_posttsdata(self, m: MagicMock):
        self.client.force_authenticate(user=self.user1)
        self.assertEqual(self._post_tsdata().status_code, 204)


@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class TsdataPostGarbageTestCase(APITestCase):
    @patch("enhydris.models.Timeseries.insert_or_append_data", side_effect=ValueError)
    def setUp(self, m: MagicMock):
        self.mock_append_data = m
        user = baker.make(User, username="admin", is_superuser=True)
        station = baker.make(models.Station)
        timeseries_group = baker.make(
            models.TimeseriesGroup, gentity=station, precision=2
        )
        timeseries = baker.make(models.Timeseries, timeseries_group=timeseries_group)
        self.client.force_authenticate(user=user)
        self.response = self.client.post(
            f"/api/stations/{station.pk}/timeseriesgroups/{timeseries_group.pk}"
            f"/timeseries/{timeseries.pk}/data/",
            data={
                "timeseries_records": (
                    # The actual content doesn't matter, since the mock will raise
                    # an error.
                    "2017-11-23 17:23,1.000000,\r\n"
                    "2018-aa-25 01:00,2.000000,\r\n",
                )
            },
        )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 400)


@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class TsdataPostDuplicateTimestampsTestCase(APITestCase):
    def setUp(self):
        user = baker.make(User, username="admin", is_superuser=True)
        station = baker.make(models.Station)
        timeseries_group = baker.make(models.TimeseriesGroup, gentity=station)
        timeseries = baker.make(models.Timeseries, timeseries_group=timeseries_group)
        self.client.force_authenticate(user=user)
        self.response = self.client.post(
            f"/api/stations/{station.pk}/timeseriesgroups/{timeseries_group.pk}"
            f"/timeseries/{timeseries.pk}/data/",
            data={
                "timezone": "Etc/GMT-2",
                "timeseries_records": (
                    "2018-11-23 17:23,1.000000,\r\n2018-11-23 17:23,2.000000,\r\n"
                ),
            },
        )

    def test_status_code(self):
        self.assertContains(
            self.response,
            "the following timestamps appear more than once",
            status_code=400,
        )


@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class TsdataStartAndEndDateTestCase(APITestCase):
    def setUp(self):
        self.station = baker.make(models.Station)
        self.timeseries_group = baker.make(
            models.TimeseriesGroup, gentity=self.station, precision=2
        )
        self.timeseries = baker.make(
            models.Timeseries,
            timeseries_group=self.timeseries_group,
            publicly_available=True,
        )

    def _make_request(self, query_string: str):
        return self.client.get(
            f"/api/stations/{self.station.pk}/timeseriesgroups"
            f"/{self.timeseries_group.pk}/timeseries/{self.timeseries.pk}/data"
            f"/?{query_string}"
        )

    @patch("enhydris.models.Timeseries.get_data")
    def test_called_get_data_with_proper_start_date(self, m: MagicMock):
        self._make_request("start_date=2005-08-23T19:54Z")
        m.assert_called_once_with(
            start_date=dt.datetime(2005, 8, 23, 19, 54, tzinfo=ZoneInfo("Etc/GMT")),
            end_date=None,
            timezone=None,
        )

    @patch("enhydris.models.Timeseries.get_data")
    def test_called_get_data_with_proper_end_date(self, m: MagicMock):
        self._make_request("end_date=2005-08-23T19:54Z")
        m.assert_called_once_with(
            start_date=None,
            end_date=dt.datetime(2005, 8, 23, 19, 54, tzinfo=ZoneInfo("Etc/GMT")),
            timezone=None,
        )

    @patch("enhydris.models.Timeseries.get_data")
    def test_called_get_data_with_very_early_start_date(self, m: MagicMock):
        self._make_request("start_date=0001-01-01T00:01Z")
        m.assert_called_once_with(
            start_date=dt.datetime(1680, 1, 1, 0, 0, tzinfo=ZoneInfo("Etc/GMT")),
            end_date=None,
            timezone=None,
        )

    @patch("enhydris.models.Timeseries.get_data")
    def test_called_get_data_with_very_late_start_date(self, m: MagicMock):
        self._make_request("end_date=3999-01-01T00:01Z")
        m.assert_called_once_with(
            start_date=None,
            end_date=dt.datetime(2260, 1, 1, 0, 0, tzinfo=ZoneInfo("Etc/GMT")),
            timezone=None,
        )


@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class TsdataInvalidStartOrEndDateTestCase(APITestCase):
    def setUp(self):
        self.station = baker.make(models.Station)
        self.timeseries_group = baker.make(
            models.TimeseriesGroup, gentity=self.station, precision=2
        )
        self.timeseries = baker.make(
            models.Timeseries,
            timeseries_group=self.timeseries_group,
            publicly_available=True,
        )

    def _make_request(self, query_string: str):
        return self.client.get(
            f"/api/stations/{self.station.pk}/timeseriesgroups"
            f"/{self.timeseries_group.pk}/timeseries/{self.timeseries.pk}/data"
            f"/?{query_string}"
        )

    @patch("enhydris.models.Timeseries.get_data")
    def test_invalid_start_date(self, m: MagicMock):
        self._make_request("?start_date=hello")
        m.assert_called_once_with(start_date=None, end_date=None, timezone=None)

    @patch("enhydris.models.Timeseries.get_data")
    def test_invalid_end_date(self, m: MagicMock):
        self._make_request("?end_date=hello")
        m.assert_called_once_with(start_date=None, end_date=None, timezone=None)


@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class TsdataHeadTestCase(APITestCase):
    def setUp(self):
        self.station = baker.make(models.Station)
        self.timeseries_group = baker.make(
            models.TimeseriesGroup,
            gentity=self.station,
            variable__descr="irrelevant",
            precision=2,
        )
        self.timeseries = baker.make(
            models.Timeseries,
            timeseries_group=self.timeseries_group,
            publicly_available=True,
        )
        self.timeseries.set_data(
            StringIO("2018-12-09 13:10,20,\n"), default_timezone="Etc/GMT"
        )

    def _get_url(self):
        return (
            f"/api/stations/{self.station.pk}/timeseriesgroups"
            f"/{self.timeseries_group.pk}/timeseries/{self.timeseries.pk}/data/"
        )

    def test_get(self):
        response = self.client.get(self._get_url())
        self.assertContains(response, "2018-12-09 13:10,")

    def test_head(self):
        response = self.client.head(self._get_url())
        self.assertNotContains(response, "2018-12-09 13:10,")


@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class TimeseriesBottomTestCase(APITestCase):
    timeseries: models.Timeseries

    def setUp(self):
        self.station = baker.make(models.Station, display_timezone="Etc/GMT-2")
        self.timeseries_group = baker.make(
            models.TimeseriesGroup,
            gentity=self.station,
            precision=2,
        )
        self.timeseries = baker.make(
            models.Timeseries,
            timeseries_group=self.timeseries_group,
            publicly_available=True,
        )
        self.timeseries.set_data(
            StringIO("2018-12-09 13:10,20,\n"), default_timezone="Etc/GMT-2"
        )

    def _get_response(self, timezone: str | None = None):
        params = None
        if timezone:
            params = {"timezone": timezone}
        self.response = self.client.get(
            f"/api/stations/{self.station.pk}/timeseriesgroups/"
            f"{self.timeseries_group.pk}/timeseries/{self.timeseries.pk}/bottom/",
            data=params,
        )

    def test_status_code(self):
        self._get_response()
        self.assertEqual(self.response.status_code, 200)

    def test_content_type(self):
        self._get_response()
        self.assertEqual(self.response["Content-Type"], "text/plain")

    def test_response_content(self):
        self._get_response()
        self.assertEqual(self.response.content.decode(), "2018-12-09 13:10,20.00,")

    def test_response_content_with_timezone(self):
        self._get_response(timezone="Etc/GMT-5")
        self.assertEqual(self.response.content.decode(), "2018-12-09 16:10,20.00,")


@override_settings(ENHYDRIS_ENABLE_TIMESERIES_DATA_VIEWERS=False)
@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class TimeseriesBottomPermissionsTestCase(APITestCase):
    def setUp(self):
        station = baker.make(models.Station)
        timeseries_group = baker.make(
            models.TimeseriesGroup,
            gentity=station,
            precision=2,
        )
        timeseries = baker.make(
            models.Timeseries,
            timeseries_group=timeseries_group,
            publicly_available=False,
        )
        timeseries.set_data(
            StringIO("2018-12-09 13:10,20,\n"), default_timezone="Etc/GMT-2"
        )
        self.url = (
            f"/api/stations/{station.pk}/timeseriesgroups/{timeseries_group.pk}/"
            f"timeseries/{timeseries.pk}/bottom/"
        )

    def test_anonymous_user_is_denied(self):
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 401)

    def test_logged_on_user_is_ok(self):
        self.user1 = baker.make(User, is_active=True, is_superuser=False)
        self.client.force_authenticate(user=self.user1)
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 200)


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class TimeseriesPostTestCase(APITestCase):
    def setUp(self):
        self.user1 = baker.make(User, is_active=True, is_superuser=False)
        self.user2 = baker.make(User, is_active=True, is_superuser=False)
        self.variable = baker.make(models.Variable, descr="Temperature")
        self.unit_of_measurement = baker.make(models.UnitOfMeasurement)
        self.station = baker.make(models.Station, creator=self.user1)
        self.timeseries_group = baker.make(models.TimeseriesGroup, gentity=self.station)

    def _create_timeseries(self, **kwargs: Any):
        return self.client.post(
            f"/api/stations/{self.station.pk}/timeseriesgroups/"
            f"{self.timeseries_group.pk}/timeseries/",
            data={
                "name": "Great time series",
                "timeseries_group": self.timeseries_group.pk,
                "type": "Initial",
                "time_step": "",
                **kwargs,
            },
        )

    def test_unauthenticated_user_is_denied_permission_to_create_timeseries(self):
        self.assertEqual(self._create_timeseries().status_code, 401)

    def test_unauthorized_user_is_denied_permission_to_create_timeseries(self):
        self.client.force_authenticate(user=self.user2)
        self.assertEqual(self._create_timeseries().status_code, 403)

    def test_authorized_user_can_create_timeseries(self):
        self.client.force_authenticate(user=self.user1)
        self.assertEqual(self._create_timeseries().status_code, 201)

    def test_returns_proper_error_when_creating_second_initial_timeseries(self):
        self.client.force_authenticate(user=self.user1)
        self._create_timeseries()
        response = self._create_timeseries(time_step="H")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            json.loads(response.content.decode())["non_field_errors"][0],
            f"A time series with timeseries_group_id={self.timeseries_group.pk} and "
            "type=Initial already exists",
        )


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class TimeseriesPostWithWrongStationOrTimeseriesGroupTestCase(APITestCase):
    def setUp(self):
        self.user = baker.make(User, is_active=True, is_superuser=False)
        self.variable = baker.make(models.Variable, descr="Temperature")
        self.unit_of_measurement = baker.make(models.UnitOfMeasurement)
        self.station1 = baker.make(models.Station, creator=self.user)
        self.timeseries_group_1_1 = baker.make(
            models.TimeseriesGroup, gentity=self.station1
        )
        self.timeseries_group_1_2 = baker.make(
            models.TimeseriesGroup, gentity=self.station1
        )
        self.station2 = baker.make(models.Station, creator=self.user)
        self.timeseries_group_2_1 = baker.make(
            models.TimeseriesGroup, gentity=self.station2
        )

    def _create_timeseries(self, **kwargs: Any):
        self.client.force_authenticate(user=self.user)
        assert isinstance(self.variable.pk, int)  # type: ignore[misc]
        return self.client.post(
            f"/api/stations/{kwargs['station_for_url'].pk}/timeseriesgroups/"
            f"{kwargs['timeseries_group_for_url'].pk}/timeseries/",
            data={
                "name": "Great time series",
                "timeseries_group": kwargs["timeseries_group_for_data"].id,
                "type": "Initial",
                "variable": self.variable.pk,
                "unit_of_measurement": self.unit_of_measurement.pk,
                "precision": 2,
                "time_step": "",
            },
        )

    def test_create_timeseries_with_wrong_station(self):
        response = self._create_timeseries(
            station_for_url=self.station1,
            timeseries_group_for_url=self.timeseries_group_2_1,
            timeseries_group_for_data=self.timeseries_group_2_1,
        )
        self.assertEqual(response.status_code, 400)

    def test_create_timeseries_with_wrong_timeseries_group(self):
        response = self._create_timeseries(
            station_for_url=self.station1,
            timeseries_group_for_url=self.timeseries_group_1_1,
            timeseries_group_for_data=self.timeseries_group_1_2,
        )
        self.assertEqual(response.status_code, 400)

    def test_create_timeseries_with_everything_correct(self):
        response = self._create_timeseries(
            station_for_url=self.station1,
            timeseries_group_for_url=self.timeseries_group_1_1,
            timeseries_group_for_data=self.timeseries_group_1_1,
        )
        self.assertEqual(response.status_code, 201)


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class TimeseriesPostWithWrongTimeseriesTypeTestCase(APITestCase):
    def setUp(self):
        self.user = baker.make(User, is_active=True, is_superuser=False)
        self.variable = baker.make(models.Variable, descr="Temperature")
        self.unit_of_measurement = baker.make(models.UnitOfMeasurement)
        self.station = baker.make(models.Station, creator=self.user)
        self.timeseries_group = baker.make(models.TimeseriesGroup, gentity=self.station)

    def _create_timeseries(self, type: str):
        self.client.force_authenticate(user=self.user)
        assert isinstance(self.variable.pk, int)  # type: ignore[misc]
        return self.client.post(
            f"/api/stations/{self.station.pk}/timeseriesgroups/"
            f"{self.timeseries_group.pk}/timeseries/",
            data={
                "name": "Great time series",
                "timeseries_group": self.timeseries_group.pk,
                "type": type,
                "variable": self.variable.pk,
                "unit_of_measurement": self.unit_of_measurement.pk,
                "precision": 2,
                "time_step": "",
            },
        )

    def test_create_timeseries_with_wrong_type(self):
        response = self._create_timeseries(type="Raw")
        self.assertEqual(response.status_code, 400)

    def test_create_timeseries_with_correct_type(self):
        response = self._create_timeseries(type="Initial")
        self.assertEqual(response.status_code, 201)


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class TimeseriesDeleteTestCase(APITestCase):
    def setUp(self):
        self.user1 = baker.make(User, is_active=True, is_superuser=False)
        self.user2 = baker.make(User, is_active=True, is_superuser=False)
        self.station = baker.make(models.Station, creator=self.user1)
        self.timeseries_group = baker.make(
            models.TimeseriesGroup, gentity=self.station, precision=2
        )
        self.timeseries = baker.make(
            models.Timeseries, timeseries_group=self.timeseries_group
        )

    def _make_request(self):
        return self.client.delete(
            f"/api/stations/{self.station.pk}/timeseriesgroups/"
            f"{self.timeseries_group.pk}/timeseries/{self.timeseries.pk}/"
        )

    def test_unauthenticated_user_is_denied_permission_to_delete_timeseries(self):
        response = self._make_request()
        self.assertEqual(response.status_code, 401)

    def test_unauthorized_user_is_denied_permission_to_delete_timeseries(self):
        self.client.force_authenticate(user=self.user2)
        response = self._make_request()
        self.assertEqual(response.status_code, 403)

    def test_authorized_user_can_delete_timeseries(self):
        self.client.force_authenticate(user=self.user1)
        response = self._make_request()
        self.assertEqual(response.status_code, 204)


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class TimeseriesValidationTestCase(APITestCase):
    def setUp(self):
        self.user = baker.make(User, is_active=True, is_superuser=True)
        self.station = baker.make(models.Station, creator=self.user)
        self.timeseries_group = baker.make(models.TimeseriesGroup, gentity=self.station)
        self.other_group = baker.make(models.TimeseriesGroup, gentity=self.station)
        self.timeseries = baker.make(
            models.Timeseries,
            timeseries_group=self.timeseries_group,
            type=models.Timeseries.INITIAL,
            time_step="",
            name="",
            publicly_available=False,
        )
        self.url = (
            f"/api/stations/{self.station.pk}/timeseriesgroups/{self.timeseries_group.pk}/"
            f"timeseries/{self.timeseries.pk}/"
        )
        self.client.force_authenticate(user=self.user)

    def test_patch_cannot_change_group(self):
        response = self.client.patch(
            self.url,
            data={"timeseries_group": self.other_group.pk},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.timeseries.refresh_from_db()
        self.assertEqual(self.timeseries.timeseries_group.pk, self.timeseries_group.pk)

    def test_patch_can_change_type(self):
        self.assertNotEqual(self.timeseries.type, "Checked")
        response = self.client.patch(
            self.url,
            data={"type": "Checked"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.timeseries.refresh_from_db()
        self.assertEqual(self.timeseries.type, models.Timeseries.CHECKED)

    def test_put_cannot_change_group(self):
        response = self.client.put(
            self.url,
            data={
                "timeseries_group": self.other_group.pk,
                "type": "Initial",
                "time_step": self.timeseries.time_step,
                "name": self.timeseries.name,
                "publicly_available": self.timeseries.publicly_available,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.timeseries.refresh_from_db()
        self.assertEqual(self.timeseries.timeseries_group.pk, self.timeseries_group.pk)

    def test_put_can_allow_type_to_stay_the_same(self):
        response = self.client.put(
            self.url,
            data={
                "timeseries_group": self.timeseries_group.pk,
                "type": "Initial",
                "time_step": self.timeseries.time_step,
                "name": self.timeseries.name,
                "publicly_available": self.timeseries.publicly_available,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)


@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
@patch("enhydris.api.views.TimeseriesViewSet._get_stats_for_all_intervals")
@patch("enhydris.models.Timeseries.get_data")
class TimeseriesChartDateBoundsTestCase(APITestCase, TimeseriesDataMixin):
    def setUp(self):
        # "_get_sampled_data_to_plot" is mocked to avoid executing the actual logic of
        # comparisons in the view, which would compare mocks, raising an exception
        self.create_timeseries(publicly_available=True)
        self.url = (
            f"/api/stations/{self.station.pk}/timeseriesgroups"
            f"/{self.timeseries_group.pk}/timeseries/{self.timeseries.pk}/chart/"
        )

    def test_no_bounds_supplied(self, mock: MagicMock, _):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        mock.assert_called_once_with(start_date=None, end_date=None)

    def test_start_date_filter(self, mock: MagicMock, _):
        response = self.client.get(self.url + "?start_date=2012-03-01T00:00Z")
        self.assertEqual(response.status_code, 200)
        mock.assert_called_once_with(
            start_date=dt.datetime(2012, 3, 1, 0, 0, tzinfo=dt.timezone.utc),
            end_date=None,
        )

    def test_start_date_filter_without_timezone(self, mock: MagicMock, _):
        response = self.client.get(self.url + "?start_date=2012-03-01T00:00")
        self.assertEqual(response.status_code, 400)

    def test_end_date_filter(self, mock: MagicMock, _):
        response = self.client.get(self.url + "?end_date=2012-03-01T00:00Z")
        self.assertEqual(response.status_code, 200)
        mock.assert_called_once_with(
            start_date=None,
            end_date=dt.datetime(2012, 3, 1, 0, 0, tzinfo=dt.timezone.utc),
        )

    def test_start_and_end_date_filters(self, mock: MagicMock, _):
        response = self.client.get(
            self.url + "?start_date=2012-03-01T00:00Z&end_date=2017-03-01T00:00Z"
        )
        self.assertEqual(response.status_code, 200)
        mock.assert_called_once_with(
            start_date=dt.datetime(2012, 3, 1, 0, 0, tzinfo=dt.timezone.utc),
            end_date=dt.datetime(2017, 3, 1, 0, 0, tzinfo=dt.timezone.utc),
        )


class TimeseriesChartTestBase(APITestCase):
    def _assertChartResponse(
        self, response: Any, expected: Any, tolerance_in_days: int = 2
    ):
        """Assert chart response by allowing timestamp tolerance, but not values.

        The expected is a list of {value, date} rather than timestamp to make the
        tests easier to write, they're translated into timestamps for comparison.
        """

        self.assertEqual(response.status_code, 200)
        data = response.json()
        tolerance_in_seconds = 86400 * tolerance_in_days
        for d, e in zip(data, expected):
            self.assertAlmostEqual(d["min"], e["min"])
            self.assertAlmostEqual(d["max"], e["max"])
            self.assertAlmostEqual(d["mean"], e["mean"])
            self.assertAlmostEqual(
                d["timestamp"], e["date"].timestamp(), delta=tolerance_in_seconds
            )

    def _value(
        self,
        yyyymmddhhmm: tuple[int, int, int, int, int],
        min: float | None,
        max: float | None,
        mean: float | None,
    ):
        return {
            "date": dt.datetime(*yyyymmddhhmm),
            "min": min,
            "max": max,
            "mean": mean,
        }


@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
@patch("enhydris.api.views.TimeseriesViewSet.CHART_MAX_INTERVALS", new=20)
@patch("enhydris.models.Timeseries.get_data")
@override_settings(ENHYDRIS_ENABLE_TIMESERIES_DATA_VIEWERS=False)
class TimeseriesChartTestCase(TimeseriesDataMixin, TimeseriesChartTestBase):
    @classmethod
    def _create_timeseries(cls, publicly_available: bool | None = None):
        # Create the timeseries so that we have 5 entries, one per year
        super().create_timeseries(publicly_available=publicly_available)
        cls.htimeseries.data = pd.DataFrame(
            index=[dt.datetime(year, 1, 1) for year in range(2010, 2015)],
            data={"value": [year for year in range(2010, 2015)], "flags": [""] * 5},
            columns=["value", "flags"],
        )
        cls.url = (
            f"/api/stations/{cls.station.pk}/timeseriesgroups"
            f"/{cls.timeseries_group.pk}/timeseries/{cls.timeseries.pk}/chart/"
        )

    def test_unauthenticated_user_denied(self, mock: MagicMock):
        self._create_timeseries(publicly_available=False)
        mock.return_value = self.htimeseries
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_authenticated_user_allowed(self, mock: MagicMock):
        self._create_timeseries(publicly_available=False)
        self.client.force_authenticate(user=baker.make(User, is_active=True))
        mock.return_value = self.htimeseries
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_all_values_returned(self, mock: MagicMock):
        self._create_timeseries(publicly_available=True)
        mock.return_value = self.htimeseries
        response = self.client.get(self.url)
        expected = [
            self._value((2010, 5, 27, 2, 24), min=2010, max=2010, mean=2010),
            self._value((2011, 3, 15, 7, 12), min=2011, max=2011, mean=2011),
            self._value((2012, 1, 1, 12, 0), min=2012, max=2012, mean=2012),
            self._value((2012, 10, 19, 16, 48), min=2013, max=2013, mean=2013),
            self._value((2013, 8, 7, 21, 36), min=2014, max=2014, mean=2014),
        ]
        self._assertChartResponse(response, expected)

    def test_null_values_are_dropped(self, mock: MagicMock):
        self._create_timeseries(publicly_available=True)
        self.htimeseries.data.loc["2010-01-01", "value"] = np.nan
        mock.return_value = self.htimeseries
        response = self.client.get(self.url)
        expected = [
            self._value((2011, 5, 18, 0, 0), min=2011, max=2011, mean=2011),
            self._value((2012, 2, 16, 0, 0), min=2012, max=2012, mean=2012),
            self._value((2012, 11, 16, 0, 0), min=2013, max=2013, mean=2013),
            self._value((2013, 8, 17, 0, 0), min=2014, max=2014, mean=2014),
        ]
        self._assertChartResponse(response, expected)


@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
@patch("enhydris.api.views.TimeseriesViewSet.CHART_MAX_INTERVALS", new=3)
@patch("enhydris.models.Timeseries.get_data")
class TimeseriesChartValuesTestCase(TimeseriesDataMixin, TimeseriesChartTestBase):
    def setUp(self):
        self.create_timeseries(publicly_available=True)
        self.htimeseries.data = pd.DataFrame(
            index=[dt.datetime(year, 1, 1) for year in range(2010, 2021)],
            data={"value": [year for year in range(2010, 2021)], "flags": [""] * 11},
            columns=["value", "flags"],
        )
        self.url = (
            f"/api/stations/{self.station.pk}/timeseriesgroups"
            f"/{self.timeseries_group.pk}/timeseries/{self.timeseries.pk}/chart/"
        )

    def test_simple(self, mock: MagicMock):
        mock.return_value = self.htimeseries
        response = self.client.get(self.url)
        expected = [
            self._value((2011, 9, 1, 16, 0), min=2010, max=2013, mean=2011.5),
            self._value((2015, 1, 1, 0, 0), min=2014, max=2016, mean=2015),
            self._value((2018, 5, 2, 8, 0), min=2017, max=2020, mean=2018.5),
        ]
        self._assertChartResponse(response, expected)

    def test_null(self, mock: MagicMock):
        """Test that unspecified data points get a value of null.

        In this test we use this test time series:
            timestamp  value
            2010-01-01 2010
            2011-01-01 2011
            2020-01-01 2020
        In this case, the second interval should get min and max = None.
        """
        mock.return_value = self.htimeseries
        self.htimeseries.data = pd.DataFrame(
            index=[
                dt.datetime(2010, 1, 1),
                dt.datetime(2011, 1, 1),
                dt.datetime(2020, 1, 1),
            ],
            data={"value": [2010, 2011, 2020], "flags": ["", "", ""]},
            columns=["value", "flags"],
        )
        response = self.client.get(self.url)
        expected = [
            self._value((2011, 9, 1, 16, 0), min=2010, max=2011, mean=2010.5),
            self._value((2015, 1, 1, 0, 0), min=None, max=None, mean=None),
            self._value((2018, 5, 2, 8, 0), min=2020, max=2020, mean=2020),
        ]
        self._assertChartResponse(response, expected)

    def test_insufficient_number_of_records(self, mock: MagicMock):
        mock.return_value = self.htimeseries
        self.htimeseries.data = pd.DataFrame(
            index=[dt.datetime(2010, 1, 1)],
            data={"value": [2010], "flags": [""]},
            columns=["value", "flags"],
        )
        response = self.client.get(self.url)
        expected = []
        self._assertChartResponse(response, expected)
