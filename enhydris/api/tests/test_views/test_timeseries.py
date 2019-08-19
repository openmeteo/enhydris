from datetime import datetime
from io import StringIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test.utils import override_settings
from rest_framework.test import APITestCase

import iso8601
import pandas as pd
from htimeseries import HTimeseries
from model_mommy import mommy

from enhydris import models
from enhydris.tests import RandomEnhydrisTimeseriesDataDir


class Tsdata404TestCase(APITestCase):
    def setUp(self):
        self.station = mommy.make(models.Station)

    def test_get_nonexistent_timeseries(self):
        response = self.client.get(
            "/api/stations/{}/timeseries/1234/data/".format(self.station.id)
        )
        self.assertEqual(response.status_code, 404)

    def test_post_nonexistent_timeseries(self):
        response = self.client.post(
            "/api/stations/{}/timeseries/1234/data/".format(self.station.id)
        )
        self.assertEqual(response.status_code, 404)


@override_settings(ENHYDRIS_OPEN_CONTENT=True)
class TsdataGetTestCase(APITestCase):
    def setUp(self):
        ahtimeseries = HTimeseries()
        ahtimeseries.data = pd.DataFrame(
            index=[datetime(2017, 11, 23, 17, 23), datetime(2018, 11, 25, 1, 0)],
            data={"value": [1.0, 2.0], "flags": ["", ""]},
            columns=["value", "flags"],
        )
        station = mommy.make(models.Station)
        timeseries = mommy.make(
            models.Timeseries, gentity=station, time_zone__utc_offset=120, precision=2
        )
        with patch("enhydris.models.Timeseries.get_data", return_value=ahtimeseries):
            self.response = self.client.get(
                "/api/stations/{}/timeseries/{}/data/".format(station.id, timeseries.id)
            )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_content_type(self):
        self.assertEqual(self.response["Content-Type"], "text/plain; charset=utf-8")

    def test_response_content(self):
        self.assertEqual(
            self.response.content.decode(),
            "2017-11-23 17:23,1.000000,\r\n2018-11-25 01:00,2.000000,\r\n",
        )


@override_settings(ENHYDRIS_OPEN_CONTENT=False)
@patch("enhydris.models.Timeseries.get_data", return_value=HTimeseries())
class TsdataGetPermissionsTestCase(APITestCase):
    def setUp(self):
        station = mommy.make(models.Station)
        timeseries = mommy.make(
            models.Timeseries, gentity=station, time_zone__utc_offset=120, precision=2
        )
        self.url = "/api/stations/{}/timeseries/{}/data/".format(
            station.id, timeseries.id
        )

    def test_anonymous_user_is_denied(self, m):
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 401)

    def test_logged_on_user_is_ok(self, m):
        self.user1 = mommy.make(User, is_active=True, is_superuser=False)
        self.client.force_authenticate(user=self.user1)
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 200)


@override_settings(ENHYDRIS_OPEN_CONTENT=True)
class TsdataGetHtsTestCase(APITestCase):
    def setUp(self):
        ahtimeseries = HTimeseries()
        ahtimeseries.data = pd.DataFrame(
            index=[datetime(2017, 11, 23, 17, 23), datetime(2018, 11, 25, 1, 0)],
            data={"value": [1.0, 2.0], "flags": ["", ""]},
            columns=["value", "flags"],
        )
        station = mommy.make(models.Station)
        timeseries = mommy.make(
            models.Timeseries, gentity=station, time_zone__utc_offset=120, precision=2
        )
        with patch("enhydris.models.Timeseries.get_data", return_value=ahtimeseries):
            self.response = self.client.get(
                "/api/stations/{}/timeseries/{}/data/?fmt=hts".format(
                    station.id, timeseries.id
                )
            )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_content_type(self):
        self.assertEqual(self.response["Content-Type"], "text/plain; charset=utf-8")

    def test_response_content(self):
        self.assertTrue(
            self.response.content.decode().endswith(
                "2017-11-23 17:23,1.000000,\r\n2018-11-25 01:00,2.000000,\r\n"
            )
        )

    def test_response_content_header(self):
        self.assertIn("Count=2", self.response.content.decode())


class TsdataPostTestCase(APITestCase):
    @patch("enhydris.models.Timeseries.append_data")
    def setUp(self, m):
        self.mock_append_data = m
        user = mommy.make(User, username="admin", is_superuser=True)
        station = mommy.make(models.Station)
        timeseries = mommy.make(models.Timeseries, gentity=station, precision=2)
        self.client.force_authenticate(user=user)
        self.response = self.client.post(
            "/api/stations/{}/timeseries/{}/data/".format(station.id, timeseries.id),
            data={
                "timeseries_records": (
                    "2017-11-23 17:23,1.000000,\r\n" "2018-11-25 01:00,2.000000,\r\n",
                )
            },
        )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 204)

    def test_called_append_data(self):
        self.assertEqual(self.mock_append_data.call_count, 1)

    def test_called_append_data_with_correct_data(self):
        self.assertEqual(
            self.mock_append_data.call_args[0][0].getvalue(),
            "2017-11-23 17:23,1.000000,\r\n" "2018-11-25 01:00,2.000000,\r\n",
        )


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class TsdataPostAuthorizationTestCase(APITestCase):
    def setUp(self):
        self.user1 = mommy.make(User, is_active=True, is_superuser=False)
        self.user2 = mommy.make(User, is_active=True, is_superuser=False)
        self.station = mommy.make(models.Station, creator=self.user1)
        self.timeseries = mommy.make(
            models.Timeseries, gentity=self.station, precision=2
        )

    def _post_tsdata(self):
        return self.client.post(
            "/api/stations/{}/timeseries/{}/data/".format(
                self.station.id, self.timeseries.id
            ),
            data={
                "timeseries_records": (
                    "2017-11-23 17:23,1.000000,\r\n" "2018-11-25 01:00,2.000000,\r\n",
                )
            },
        )

    @patch("enhydris.models.Timeseries.append_data")
    def test_unauthenticated_user_is_denied_permission_to_post_tsdata(self, m):
        self.assertEqual(self._post_tsdata().status_code, 401)

    @patch("enhydris.models.Timeseries.append_data")
    def test_unauthorized_user_is_denied_permission_to_post_tsdata(self, m):
        self.client.force_authenticate(user=self.user2)
        self.assertEqual(self._post_tsdata().status_code, 403)

    @patch("enhydris.models.Timeseries.append_data")
    def test_authorized_user_can_posttsdata(self, m):
        self.client.force_authenticate(user=self.user1)
        self.assertEqual(self._post_tsdata().status_code, 204)


class TsdataPostGarbageTestCase(APITestCase):
    @patch("enhydris.models.Timeseries.append_data", side_effect=iso8601.ParseError)
    def setUp(self, m):
        self.mock_append_data = m
        user = mommy.make(User, username="admin", is_superuser=True)
        station = mommy.make(models.Station)
        timeseries = mommy.make(models.Timeseries, gentity=station, precision=2)
        self.client.force_authenticate(user=user)
        self.response = self.client.post(
            "/api/stations/{}/timeseries/{}/data/".format(station.id, timeseries.id),
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


@override_settings(ENHYDRIS_OPEN_CONTENT=True)
class TsdataStartAndEndDateTestCase(APITestCase):
    """Test that there's no aware/naive date confusion.

    There was this bug where you'd ask to download from start date, and the start date
    was interpreted as aware whereas the time series data was interpreted as naive. This
    test checks there's no such bug.
    """

    def setUp(self):
        self.tz = mommy.make(models.TimeZone, code="EET", utc_offset=120)
        self.timeseries = mommy.make(models.Timeseries, time_zone=self.tz, precision=2)

    @patch("enhydris.models.Timeseries.get_data")
    def test_called_get_data_with_proper_start_date(self, m):
        self.response = self.client.get(
            "/api/stations/{}/timeseries/{}/data/?start_date=2005-08-23T19:54".format(
                self.timeseries.gentity.id, self.timeseries.id
            )
        )
        m.assert_called_once_with(
            start_date=datetime(2005, 8, 23, 19, 54), end_date=None
        )

    @patch("enhydris.models.Timeseries.get_data")
    def test_called_get_data_with_proper_end_date(self, m):
        self.response = self.client.get(
            "/api/stations/{}/timeseries/{}/data/?end_date=2005-08-23T19:54".format(
                self.timeseries.gentity.id, self.timeseries.id
            )
        )
        m.assert_called_once_with(
            start_date=None, end_date=datetime(2005, 8, 23, 19, 54)
        )


@override_settings(ENHYDRIS_OPEN_CONTENT=True)
class TsdataInvalidStartOrEndDateTestCase(APITestCase):
    def setUp(self):
        self.tz = mommy.make(models.TimeZone, code="EET", utc_offset=120)
        self.timeseries = mommy.make(models.Timeseries, time_zone=self.tz, precision=2)

    @patch("enhydris.models.Timeseries.get_data")
    def test_invalid_start_date(self, m):
        self.response = self.client.get(
            "/api/stations/{}/timeseries/{}/data/?start_date=hello".format(
                self.timeseries.gentity.id, self.timeseries.id
            )
        )
        m.assert_called_once_with(start_date=None, end_date=None)

    @patch("enhydris.models.Timeseries.get_data")
    def test_invalid_end_date(self, m):
        self.response = self.client.get(
            "/api/stations/{}/timeseries/{}/data/?end_date=hello".format(
                self.timeseries.gentity.id, self.timeseries.id
            )
        )
        m.assert_called_once_with(start_date=None, end_date=None)


@override_settings(ENHYDRIS_OPEN_CONTENT=True)
@RandomEnhydrisTimeseriesDataDir()
class TsdataHeadTestCase(APITestCase):
    def setUp(self):
        station = mommy.make(models.Station)
        self.tz = mommy.make(models.TimeZone, code="EET", utc_offset=120)
        self.timeseries = mommy.make(
            models.Timeseries,
            time_zone=self.tz,
            gentity=station,
            variable__descr="irrelevant",
            precision=2,
        )
        self.timeseries.set_data(StringIO("2018-12-09 13:10,20,\n"))

    def test_get(self):
        response = self.client.get(
            "/api/stations/{}/timeseries/{}/data/".format(
                self.timeseries.gentity.id, self.timeseries.id
            )
        )
        self.assertContains(response, "2018-12-09 13:10,")

    def test_head(self):
        response = self.client.head(
            "/api/stations/{}/timeseries/{}/data/".format(
                self.timeseries.gentity.id, self.timeseries.id
            )
        )
        self.assertNotContains(response, "2018-12-09 13:10,")


@override_settings(ENHYDRIS_OPEN_CONTENT=True)
class TimeseriesBottomTestCase(APITestCase):
    @patch(
        "enhydris.models.Timeseries.get_last_line", return_value="2018-12-09 13:10,20,"
    )
    def setUp(self, m):
        station = mommy.make(models.Station)
        timeseries = mommy.make(
            models.Timeseries, gentity=station, time_zone__utc_offset=120, precision=2
        )
        self.response = self.client.get(
            "/api/stations/{}/timeseries/{}/bottom/".format(station.id, timeseries.id)
        )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_content_type(self):
        self.assertEqual(self.response["Content-Type"], "text/plain")

    def test_response_content(self):
        self.assertEqual(self.response.content.decode(), "2018-12-09 13:10,20,")


@override_settings(ENHYDRIS_OPEN_CONTENT=False)
@patch("enhydris.models.Timeseries.get_last_line", return_value="2018-12-09 13:10,20,")
class TimeseriesBottomPermissionsTestCase(APITestCase):
    def setUp(self):
        station = mommy.make(models.Station)
        timeseries = mommy.make(
            models.Timeseries, gentity=station, time_zone__utc_offset=120, precision=2
        )
        self.url = "/api/stations/{}/timeseries/{}/bottom/".format(
            station.id, timeseries.id
        )

    def test_anonymous_user_is_denied(self, m):
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 401)

    def test_logged_on_user_is_ok(self, m):
        self.user1 = mommy.make(User, is_active=True, is_superuser=False)
        self.client.force_authenticate(user=self.user1)
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 200)


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class TimeseriesPostTestCase(APITestCase):
    def setUp(self):
        self.user1 = mommy.make(User, is_active=True, is_superuser=False)
        self.user2 = mommy.make(User, is_active=True, is_superuser=False)
        self.variable = mommy.make(models.Variable)
        self.time_zone = mommy.make(models.TimeZone)
        self.unit_of_measurement = mommy.make(models.UnitOfMeasurement)
        self.station = mommy.make(models.Station, creator=self.user1)

    def _create_timeseries(self):
        return self.client.post(
            "/api/stations/{}/timeseries/".format(self.station.id),
            data={
                "name": "Great time series",
                "gentity": self.station.id,
                "variable": self.variable.id,
                "time_zone": self.time_zone.id,
                "unit_of_measurement": self.unit_of_measurement.id,
                "precision": 2,
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


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class TimeseriesPostWithWrongStationTestCase(APITestCase):
    def setUp(self):
        self.user = mommy.make(User, is_active=True, is_superuser=False)
        self.variable = mommy.make(models.Variable)
        self.time_zone = mommy.make(models.TimeZone)
        self.unit_of_measurement = mommy.make(models.UnitOfMeasurement)
        self.station1 = mommy.make(models.Station, creator=self.user)
        self.station2 = mommy.make(models.Station, creator=self.user)

    def _create_timeseries(self, station_for_url, station_for_data):
        self.client.force_authenticate(user=self.user)
        return self.client.post(
            "/api/stations/{}/timeseries/".format(station_for_url.id),
            data={
                "name": "Great time series",
                "gentity": station_for_data.id,
                "variable": self.variable.id,
                "time_zone": self.time_zone.id,
                "unit_of_measurement": self.unit_of_measurement.id,
                "precision": 2,
            },
        )

    def test_create_timeseries_with_wrong_station(self):
        response = self._create_timeseries(
            station_for_url=self.station1, station_for_data=self.station2
        )
        self.assertEqual(response.status_code, 400)

    def test_create_timeseries_with_correct_station(self):
        response = self._create_timeseries(
            station_for_url=self.station1, station_for_data=self.station1
        )
        self.assertEqual(response.status_code, 201)


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class TimeseriesDeleteTestCase(APITestCase):
    def setUp(self):
        self.user1 = mommy.make(User, is_active=True, is_superuser=False)
        self.user2 = mommy.make(User, is_active=True, is_superuser=False)
        self.station = mommy.make(models.Station, creator=self.user1)
        self.timeseries = mommy.make(
            models.Timeseries, gentity=self.station, precision=2
        )

    def test_unauthenticated_user_is_denied_permission_to_delete_timeseries(self):
        response = self.client.delete(
            "/api/stations/{}/timeseries/{}/".format(
                self.station.id, self.timeseries.id
            )
        )
        self.assertEqual(response.status_code, 401)

    def test_unauthorized_user_is_denied_permission_to_delete_timeseries(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.delete(
            "/api/stations/{}/timeseries/{}/".format(
                self.station.id, self.timeseries.id
            )
        )
        self.assertEqual(response.status_code, 403)

    def test_authorized_user_can_delete_timeseries(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(
            "/api/stations/{}/timeseries/{}/".format(
                self.station.id, self.timeseries.id
            )
        )
        self.assertEqual(response.status_code, 204)
