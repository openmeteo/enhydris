from datetime import datetime
from io import StringIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test.utils import override_settings
from rest_framework.test import APITestCase

import iso8601
import numpy as np
import pandas as pd
from htimeseries import HTimeseries
from model_mommy import mommy

from enhydris import models
from enhydris.tests import TimeseriesDataMixin


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


@override_settings(ENHYDRIS_OPEN_CONTENT=False)
@patch("enhydris.models.Timeseries.get_data", return_value=HTimeseries())
class TsdataGetPermissionsTestCase(APITestCase):
    def setUp(self):
        station = mommy.make(models.Station)
        timeseries_group = mommy.make(
            models.TimeseriesGroup,
            gentity=station,
            time_zone__utc_offset=120,
            precision=2,
        )
        timeseries = mommy.make(models.Timeseries, timeseries_group=timeseries_group)
        self.url = (
            f"/api/stations/{station.id}/timeseriesgroups/{timeseries_group.id}/"
            f"timeseries/{timeseries.id}/data/"
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
class GetDataTestCase(APITestCase, TimeseriesDataMixin):
    def setUp(self):
        self.create_timeseries()
        p = patch("enhydris.models.Timeseries.get_data", return_value=self.htimeseries)
        with p:
            self.response = self.client.get(
                f"/api/stations/{self.station.id}/timeseriesgroups/"
                f"{self.timeseries_group.id}/timeseries/{self.timeseries.id}/data/"
            )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_content_type(self):
        self.assertEqual(self.response["Content-Type"], "text/csv; charset=utf-8")

    def test_response_content(self):
        self.assertTrue(
            self.response.content.decode().endswith(
                "2017-11-23 17:23,1.000000,\r\n2018-11-25 01:00,2.000000,\r\n"
            )
        )


@override_settings(ENHYDRIS_OPEN_CONTENT=True)
class GetDataInVariousFormatsTestCase(APITestCase, TimeseriesDataMixin):
    def setUp(self):
        super().setUp()
        self.create_timeseries()
        self.get_data_patch = patch(
            "enhydris.models.Timeseries.get_data", return_value=self.htimeseries
        )
        self.base_url = (
            f"/api/stations/{self.station.id}/timeseriesgroups/"
            f"{self.timeseries_group.id}/timeseries/{self.timeseries.id}/data/"
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
        self.assertEqual(response["Content-Disposition"], 'inline; filename="42.hts"')

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
        self.assertEqual(response["Content-Disposition"], 'inline; filename="42.hts"')

    def test_response_content_csv(self):
        with self.get_data_patch:
            response = self.client.get(self.base_url + "?fmt=csv")
        self.assertTrue(response.content.decode().startswith("2017-11-23 17:23,"))

    def test_response_headers_csv(self):
        with self.get_data_patch:
            response = self.client.get(self.base_url + "?fmt=csv")
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertEqual(response["Content-Disposition"], 'inline; filename="42.csv"')

    def test_response_content_csv_default(self):
        with self.get_data_patch:
            response = self.client.get(self.base_url)
        self.assertTrue(response.content.decode().startswith("2017-11-23 17:23,"))

    def test_response_headers_csv_default(self):
        with self.get_data_patch:
            response = self.client.get(self.base_url)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertEqual(response["Content-Disposition"], 'inline; filename="42.csv"')


class TsdataPostTestCase(APITestCase):
    @patch("enhydris.models.Timeseries.append_data")
    def setUp(self, m):
        self.mock_append_data = m
        user = mommy.make(User, username="admin", is_superuser=True)
        station = mommy.make(models.Station)
        timeseries_group = mommy.make(
            models.TimeseriesGroup, gentity=station, precision=2
        )
        timeseries = mommy.make(models.Timeseries, timeseries_group=timeseries_group)
        self.client.force_authenticate(user=user)
        self.response = self.client.post(
            f"/api/stations/{station.id}/timeseriesgroups/{timeseries_group.id}"
            f"/timeseries/{timeseries.id}/data/",
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
        self.timeseries_group = mommy.make(
            models.TimeseriesGroup, gentity=self.station, precision=2
        )
        self.timeseries = mommy.make(
            models.Timeseries, timeseries_group=self.timeseries_group
        )

    def _post_tsdata(self):
        return self.client.post(
            f"/api/stations/{self.station.id}/timeseriesgroups"
            f"/{self.timeseries_group.id}/timeseries/{self.timeseries.id}/data/",
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
        timeseries_group = mommy.make(
            models.TimeseriesGroup, gentity=station, precision=2
        )
        timeseries = mommy.make(models.Timeseries, timeseries_group=timeseries_group)
        self.client.force_authenticate(user=user)
        self.response = self.client.post(
            f"/api/stations/{station.id}/timeseriesgroups/{timeseries_group.id}"
            f"/timeseries/{timeseries.id}/data/",
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


class TsdataPostDuplicateTimestampsTestCase(APITestCase):
    def setUp(self):
        user = mommy.make(User, username="admin", is_superuser=True)
        station = mommy.make(models.Station)
        tz = mommy.make(models.TimeZone, code="EET", utc_offset=120)
        timeseries_group = mommy.make(
            models.TimeseriesGroup, gentity=station, time_zone=tz
        )
        timeseries = mommy.make(models.Timeseries, timeseries_group=timeseries_group)
        self.client.force_authenticate(user=user)
        self.response = self.client.post(
            f"/api/stations/{station.id}/timeseriesgroups/{timeseries_group.id}"
            f"/timeseries/{timeseries.id}/data/",
            data={
                "timeseries_records": (
                    "2018-11-23 17:23,1.000000,\r\n2018-11-23 17:23,2.000000,\r\n"
                )
            },
        )

    def test_status_code(self):
        self.assertContains(
            self.response,
            "the following timestamps appear more than once",
            status_code=400,
        )


@override_settings(ENHYDRIS_OPEN_CONTENT=True)
class TsdataStartAndEndDateTestCase(APITestCase):
    """Test that there's no aware/naive date confusion.

    There was this bug where you'd ask to download from start date, and the start date
    was interpreted as aware whereas the time series data was interpreted as naive. This
    test checks there's no such bug.
    """

    def setUp(self):
        self.tz = mommy.make(models.TimeZone, code="EET", utc_offset=120)
        self.station = mommy.make(models.Station)
        self.timeseries_group = mommy.make(
            models.TimeseriesGroup, gentity=self.station, time_zone=self.tz, precision=2
        )
        self.timeseries = mommy.make(
            models.Timeseries, timeseries_group=self.timeseries_group
        )

    def _make_request(self, query_string):
        return self.client.get(
            f"/api/stations/{self.station.id}/timeseriesgroups"
            f"/{self.timeseries_group.id}/timeseries/{self.timeseries.id}/data"
            f"/?{query_string}"
        )

    @patch("enhydris.models.Timeseries.get_data")
    def test_called_get_data_with_proper_start_date(self, m):
        self._make_request("start_date=2005-08-23T19:54")
        m.assert_called_once_with(
            start_date=datetime(2005, 8, 23, 19, 54, tzinfo=self.tz.as_tzinfo),
            end_date=None,
        )

    @patch("enhydris.models.Timeseries.get_data")
    def test_called_get_data_with_proper_end_date(self, m):
        self._make_request("end_date=2005-08-23T19:54")
        m.assert_called_once_with(
            start_date=None,
            end_date=datetime(2005, 8, 23, 19, 54, tzinfo=self.tz.as_tzinfo),
        )


@override_settings(ENHYDRIS_OPEN_CONTENT=True)
class TsdataInvalidStartOrEndDateTestCase(APITestCase):
    def setUp(self):
        self.tz = mommy.make(models.TimeZone, code="EET", utc_offset=120)
        self.station = mommy.make(models.Station)
        self.timeseries_group = mommy.make(
            models.TimeseriesGroup, gentity=self.station, time_zone=self.tz, precision=2
        )
        self.timeseries = mommy.make(
            models.Timeseries, timeseries_group=self.timeseries_group
        )

    def _make_request(self, query_string):
        return self.client.get(
            f"/api/stations/{self.station.id}/timeseriesgroups"
            f"/{self.timeseries_group.id}/timeseries/{self.timeseries.id}/data"
            f"/?{query_string}"
        )

    @patch("enhydris.models.Timeseries.get_data")
    def test_invalid_start_date(self, m):
        self._make_request("?start_date=hello")
        m.assert_called_once_with(start_date=None, end_date=None)

    @patch("enhydris.models.Timeseries.get_data")
    def test_invalid_end_date(self, m):
        self._make_request("?end_date=hello")
        m.assert_called_once_with(start_date=None, end_date=None)


@override_settings(ENHYDRIS_OPEN_CONTENT=True)
class TsdataHeadTestCase(APITestCase):
    def setUp(self):
        self.station = mommy.make(models.Station)
        self.tz = mommy.make(models.TimeZone, code="EET", utc_offset=120)
        self.timeseries_group = mommy.make(
            models.TimeseriesGroup,
            time_zone=self.tz,
            gentity=self.station,
            variable__descr="irrelevant",
            precision=2,
        )
        self.timeseries = mommy.make(
            models.Timeseries, timeseries_group=self.timeseries_group
        )
        self.timeseries.set_data(StringIO("2018-12-09 13:10,20,\n"))

    def _get_url(self):
        return (
            f"/api/stations/{self.station.id}/timeseriesgroups"
            f"/{self.timeseries_group.id}/timeseries/{self.timeseries.id}/data/"
        )

    def test_get(self):
        response = self.client.get(self._get_url())
        self.assertContains(response, "2018-12-09 13:10,")

    def test_head(self):
        response = self.client.head(self._get_url())
        self.assertNotContains(response, "2018-12-09 13:10,")


@override_settings(ENHYDRIS_OPEN_CONTENT=True)
class TimeseriesBottomTestCase(APITestCase):
    def setUp(self):
        station = mommy.make(models.Station)
        timeseries_group = mommy.make(
            models.TimeseriesGroup,
            gentity=station,
            time_zone__utc_offset=120,
            precision=2,
        )
        timeseries = mommy.make(models.Timeseries, timeseries_group=timeseries_group)
        timeseries.set_data(StringIO("2018-12-09 13:10,20,\n"))
        self.response = self.client.get(
            f"/api/stations/{station.id}/timeseriesgroups/{timeseries_group.id}/"
            f"timeseries/{timeseries.id}/bottom/"
        )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_content_type(self):
        self.assertEqual(self.response["Content-Type"], "text/plain")

    def test_response_content(self):
        self.assertEqual(self.response.content.decode(), "2018-12-09 13:10,20.00,")


@override_settings(ENHYDRIS_OPEN_CONTENT=False)
class TimeseriesBottomPermissionsTestCase(APITestCase):
    def setUp(self):
        station = mommy.make(models.Station)
        timeseries_group = mommy.make(
            models.TimeseriesGroup,
            gentity=station,
            time_zone__utc_offset=120,
            precision=2,
        )
        timeseries = mommy.make(models.Timeseries, timeseries_group=timeseries_group)
        timeseries.set_data(StringIO("2018-12-09 13:10,20,\n"))
        self.url = (
            f"/api/stations/{station.id}/timeseriesgroups/{timeseries_group.id}/"
            f"timeseries/{timeseries.id}/bottom/"
        )

    def test_anonymous_user_is_denied(self):
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 401)

    def test_logged_on_user_is_ok(self):
        self.user1 = mommy.make(User, is_active=True, is_superuser=False)
        self.client.force_authenticate(user=self.user1)
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 200)


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class TimeseriesPostTestCase(APITestCase):
    def setUp(self):
        self.user1 = mommy.make(User, is_active=True, is_superuser=False)
        self.user2 = mommy.make(User, is_active=True, is_superuser=False)
        self.variable = mommy.make(models.Variable, descr="Temperature")
        self.time_zone = mommy.make(models.TimeZone)
        self.unit_of_measurement = mommy.make(models.UnitOfMeasurement)
        self.station = mommy.make(models.Station, creator=self.user1)
        self.timeseries_group = mommy.make(models.TimeseriesGroup, gentity=self.station)

    def _create_timeseries(self):
        return self.client.post(
            f"/api/stations/{self.station.id}/timeseriesgroups/"
            f"{self.timeseries_group.id}/timeseries/",
            data={
                "name": "Great time series",
                "timeseries_group": self.timeseries_group.id,
                "type": models.Timeseries.RAW,
                "variable": self.variable.id,
                "time_zone": self.time_zone.id,
                "unit_of_measurement": self.unit_of_measurement.id,
                "precision": 2,
                "time_step": "",
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
class TimeseriesPostWithWrongStationOrTimeseriesGroupTestCase(APITestCase):
    def setUp(self):
        self.user = mommy.make(User, is_active=True, is_superuser=False)
        self.variable = mommy.make(models.Variable, descr="Temperature")
        self.time_zone = mommy.make(models.TimeZone)
        self.unit_of_measurement = mommy.make(models.UnitOfMeasurement)
        self.station1 = mommy.make(models.Station, creator=self.user)
        self.timeseries_group_1_1 = mommy.make(
            models.TimeseriesGroup, gentity=self.station1
        )
        self.timeseries_group_1_2 = mommy.make(
            models.TimeseriesGroup, gentity=self.station1
        )
        self.station2 = mommy.make(models.Station, creator=self.user)
        self.timeseries_group_2_1 = mommy.make(
            models.TimeseriesGroup, gentity=self.station2
        )

    def _create_timeseries(self, **kwargs):
        self.client.force_authenticate(user=self.user)
        return self.client.post(
            f"/api/stations/{kwargs['station_for_url'].id}/timeseriesgroups/"
            f"{kwargs['timeseries_group_for_url'].id}/timeseries/",
            data={
                "name": "Great time series",
                "timeseries_group": kwargs["timeseries_group_for_data"].id,
                "type": models.Timeseries.RAW,
                "variable": self.variable.id,
                "time_zone": self.time_zone.id,
                "unit_of_measurement": self.unit_of_measurement.id,
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
class TimeseriesDeleteTestCase(APITestCase):
    def setUp(self):
        self.user1 = mommy.make(User, is_active=True, is_superuser=False)
        self.user2 = mommy.make(User, is_active=True, is_superuser=False)
        self.station = mommy.make(models.Station, creator=self.user1)
        self.timeseries_group = mommy.make(
            models.TimeseriesGroup, gentity=self.station, precision=2
        )
        self.timeseries = mommy.make(
            models.Timeseries, timeseries_group=self.timeseries_group
        )

    def _make_request(self):
        return self.client.delete(
            f"/api/stations/{self.station.id}/timeseriesgroups/"
            f"{self.timeseries_group.id}/timeseries/{self.timeseries.id}/"
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


@override_settings(ENHYDRIS_OPEN_CONTENT=True)
@patch("enhydris.api.views.TimeseriesViewSet._get_sampled_data_to_plot")
@patch("enhydris.models.Timeseries.get_data")
class TimeseriesChartDateBoundsTestCase(APITestCase, TimeseriesDataMixin):
    def setUp(self):
        # "_get_sampled_data_to_plot" is mocked to avoid executing the actual logic of
        # comparisions in the view, which would compare mocks; raising an exception
        self.create_timeseries()
        self.url = (
            f"/api/stations/{self.station.id}/timeseriesgroups"
            f"/{self.timeseries_group.id}/timeseries/{self.timeseries.id}/chart/"
        )

    def test_no_bounds_supplied(self, mock, _):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        mock.assert_called_once_with(start_date=None, end_date=None)

    def test_start_date_filter(self, mock, _):
        response = self.client.get(self.url + "?start_date=2012-03-01T00:00")
        self.assertEqual(response.status_code, 200)
        mock.assert_called_once_with(
            start_date=datetime(
                2012, 3, 1, 0, 0, tzinfo=self.timeseries_group.time_zone.as_tzinfo
            ),
            end_date=None,
        )

    def test_end_date_filter(self, mock, _):
        response = self.client.get(self.url + "?end_date=2012-03-01T00:00")
        self.assertEqual(response.status_code, 200)
        mock.assert_called_once_with(
            start_date=None,
            end_date=datetime(
                2012, 3, 1, 0, 0, tzinfo=self.timeseries_group.time_zone.as_tzinfo
            ),
        )

    def test_start_and_end_date_filters(self, mock, _):
        response = self.client.get(
            self.url + "?start_date=2012-03-01T00:00&end_date=2017-03-01T00:00"
        )
        self.assertEqual(response.status_code, 200)
        mock.assert_called_once_with(
            start_date=datetime(
                2012, 3, 1, 0, 0, tzinfo=self.timeseries_group.time_zone.as_tzinfo
            ),
            end_date=datetime(
                2017, 3, 1, 0, 0, tzinfo=self.timeseries_group.time_zone.as_tzinfo
            ),
        )


class TimeseriesChartTestMixin:
    def _assertChartResponse(self, response, expected, tolerance_in_days=2):
        """Assert chart response by allowing timestamp tolerance, but not values.

        The expected is a list of {value, date} rather than timestamp to make the
        tests easier to write, they're translated into timestamps for comparison.
        """

        self.assertEqual(response.status_code, 200)
        data = response.json()
        tolerance_in_seconds = 86400 * tolerance_in_days
        for d, e in zip(data, expected):
            self.assertEqual(d["value"], e["value"])
            self.assertAlmostEqual(
                d["timestamp"], e["date"].timestamp(), delta=tolerance_in_seconds
            )


@override_settings(ENHYDRIS_OPEN_CONTENT=True)
@patch("enhydris.api.views.TimeseriesViewSet.CHART_MAXIMUM_NUMBER_OF_SAMPLES", new=20)
@patch("enhydris.models.Timeseries.get_data")
class TimeseriesChartTestCase(
    APITestCase, TimeseriesDataMixin, TimeseriesChartTestMixin
):
    def create_timeseries(self):
        # Create the timeseries so that we have 5 entries, one per year basically
        super().create_timeseries()
        self.htimeseries.data = pd.DataFrame(
            index=[datetime(year, 1, 1) for year in range(2010, 2015)],
            data={"value": [year for year in range(2010, 2015)], "flags": [""] * 5},
            columns=["value", "flags"],
        )

    def setUp(self):
        self.create_timeseries()
        self.url = (
            f"/api/stations/{self.station.id}/timeseriesgroups"
            f"/{self.timeseries_group.id}/timeseries/{self.timeseries.id}/chart/"
        )

    @override_settings(ENHYDRIS_OPEN_CONTENT=False)
    def test_unauthenticated_user_denied(self, mock):
        mock.return_value = self.htimeseries
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    @override_settings(ENHYDRIS_OPEN_CONTENT=False)
    def test_authenticated_user_allowed(self, mock):
        self.client.force_authenticate(user=mommy.make(User, is_active=True))
        mock.return_value = self.htimeseries
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_all_values_returned(self, mock):
        mock.return_value = self.htimeseries
        response = self.client.get(self.url)
        expected = [
            {"date": datetime(year, 1, 1), "value": f"{year}.00"}
            for year in range(2010, 2015)
        ]
        self._assertChartResponse(response, expected)

    def test_null_values_are_dropped(self, mock):
        self.htimeseries.data.loc["2010-01-01", "value"] = np.nan
        mock.return_value = self.htimeseries
        response = self.client.get(self.url)
        expected = [
            {"date": datetime(year, 1, 1), "value": f"{year}.00"}
            for year in range(2011, 2015)
        ]
        self._assertChartResponse(response, expected)


@override_settings(ENHYDRIS_OPEN_CONTENT=True)
@patch("enhydris.api.views.TimeseriesViewSet.CHART_MAXIMUM_NUMBER_OF_SAMPLES", new=3)
@patch("enhydris.models.Timeseries.get_data")
class TimeseriesChartSamplingTestCase(
    APITestCase, TimeseriesDataMixin, TimeseriesChartTestMixin
):
    def setUp(self):
        self.create_timeseries()
        self.htimeseries.data = pd.DataFrame(
            index=[datetime(year, 1, 1) for year in range(2010, 2021)],
            data={"value": [year for year in range(2010, 2021)], "flags": [""] * 11},
            columns=["value", "flags"],
        )
        self.url = (
            f"/api/stations/{self.station.id}/timeseriesgroups"
            f"/{self.timeseries_group.id}/timeseries/{self.timeseries.id}/chart/"
        )

    def test_data_sampled_by_equal_time_distance(self, mock):
        mock.return_value = self.htimeseries
        response = self.client.get(self.url)
        expected = [
            {"date": datetime(year, 1, 1), "value": f"{year}.00"}
            for year in [2010, 2015, 2020]
        ]
        self._assertChartResponse(response, expected)
