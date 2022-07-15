import datetime as dt
import json
from unittest import TestCase
from unittest.mock import patch

from freezegun import freeze_time
from requests import Timeout

from enhydris.telemetry.types.meteoview2 import ErrorResponse, Meteoview2ApiClient


class Meteoview2ApiClientTestCaseBase(TestCase):
    def setUp(self):
        self.meteoview2_api_client = Meteoview2ApiClient(
            "myemail@somewhere.com", "topsecretapikey"
        )


@patch("enhydris.telemetry.types.meteoview2.requests")
class MakeRequestTestCase(Meteoview2ApiClientTestCaseBase):
    def test_raises_on_bad_status_code(self, mock_requests):
        mock_requests.request.return_value.raise_for_status.side_effect = Timeout
        with self.assertRaises(Timeout):
            self.meteoview2_api_client.make_request("GET", "/")

    def test_raises_when_response_has_no_code(self, mock_requests):
        mock_requests.request.return_value.json.return_value = {}
        with self.assertRaises(ErrorResponse):
            self.meteoview2_api_client.make_request("GET", "/")

    def test_raises_when_code_is_not_200(self, mock_requests):
        mock_requests.request.return_value.json.return_value = {"code": "404"}
        with self.assertRaises(ErrorResponse):
            self.meteoview2_api_client.make_request("GET", "/")

    def test_ok_when_code_is_200(self, mock_requests):
        mock_requests.request.return_value.json.return_value = {"code": "200"}
        self.assertEqual(
            self.meteoview2_api_client.make_request("GET", "/"), {"code": "200"}
        )


@patch("enhydris.telemetry.types.meteoview2.requests")
class LoginTestCase(Meteoview2ApiClientTestCaseBase):
    def test_makes_request(self, mock_requests):
        self._set_successful_request_result(mock_requests)
        self.meteoview2_api_client.login()
        mock_requests.request.assert_called_once_with(
            "POST",
            "https://meteoview2.gr/api/token",
            headers={"content-type": "application/json"},
            data=json.dumps(
                {"email": "myemail@somewhere.com", "key": "topsecretapikey"}
            ),
        )

    def test_sets_token(self, mock_requests):
        self._set_successful_request_result(mock_requests)
        self.meteoview2_api_client.login()
        self.assertEqual(self.meteoview2_api_client.token, "topsecretapitoken")

    def _set_successful_request_result(self, mock_requests):
        mock_requests.request.return_value.json.return_value = {
            "code": "200",
            "token": "topsecretapitoken",
        }


class LoggedOnTestCaseBase(Meteoview2ApiClientTestCaseBase):
    def setUp(self):
        super().setUp()
        self.meteoview2_api_client.token = "topsecretapitoken"


@patch("enhydris.telemetry.types.meteoview2.requests")
class GetStationsTestCase(LoggedOnTestCaseBase):
    def test_makes_request(self, mock_requests):
        self._set_successful_request_result(mock_requests)
        self.meteoview2_api_client.get_stations()
        mock_requests.request.assert_called_once_with(
            "GET",
            "https://meteoview2.gr/api/stations",
            headers={"Authorization": "Bearer topsecretapitoken"},
        )

    def test_returns_stations(self, mock_requests):
        self._set_successful_request_result(mock_requests)
        self.assertEqual(self.meteoview2_api_client.get_stations(), {"hello": "world"})

    def _set_successful_request_result(self, mock_requests):
        mock_requests.request.return_value.json.return_value = {
            "code": "200",
            "stations": {"hello": "world"},
        }


@patch("enhydris.telemetry.types.meteoview2.requests")
class GetSensorsTestCase(LoggedOnTestCaseBase):
    def test_makes_request(self, mock_requests):
        self._set_successful_request_result(mock_requests)
        self.meteoview2_api_client.get_sensors(823)
        mock_requests.request.assert_called_once_with(
            "POST",
            "https://meteoview2.gr/api/sensors",
            headers={
                "content-type": "application/json",
                "Authorization": "Bearer topsecretapitoken",
            },
            data=json.dumps({"station_code": 823}),
        )

    def test_returns_sensors(self, mock_requests):
        self._set_successful_request_result(mock_requests)
        self.meteoview2_api_client.get_sensors(823)
        self.assertEqual(self.meteoview2_api_client.get_sensors(8), {"hello": "world"})

    def _set_successful_request_result(self, mock_requests):
        mock_requests.request.return_value.json.return_value = {
            "code": "200",
            "sensors": {"hello": "world"},
        }


@patch("enhydris.telemetry.types.meteoview2.requests")
@freeze_time("2022-06-14 08:35")
class GetMeasurementsTestCase(LoggedOnTestCaseBase):
    def test_makes_request(self, mock_requests):
        self._set_successful_request_result(mock_requests)
        existing_end_date = dt.datetime(2022, 6, 14, 8, 0)
        self.meteoview2_api_client.get_measurements(8231, existing_end_date)
        mock_requests.request.assert_called_once_with(
            "POST",
            "https://meteoview2.gr/api/measurements",
            headers={
                "content-type": "application/json",
                "Authorization": "Bearer topsecretapitoken",
            },
            data=json.dumps(
                {
                    "sensor": [8231],
                    "datefrom": "2022-06-14",
                    "timefrom": "08:01",
                    "dateto": "2022-12-11",
                }
            ),
        )

    def test_return_value(self, mock_requests):
        self._set_successful_request_result(mock_requests)
        existing_end_date = dt.datetime(2022, 6, 14, 8, 0)
        result = self.meteoview2_api_client.get_measurements(8231, existing_end_date)
        self.assertEqual(
            result.getvalue(), "2022-06-14T08:10:00,1.42,\n2022-06-14T08:20:00,1.43,\n"
        )

    def test_request_when_no_start_date(self, mock_requests):
        """Test request when no start date

        get_measurements() can be called with timeseries_end_date=None. In that case, it
        should assume a start date of 1 Jan 1990. (In that case the API wouldn't respond
        with what we mock it to respond with, i.e. values in 2022, but this doesn't
        affect the unit test.)
        """
        self._set_successful_request_result(mock_requests)
        self.meteoview2_api_client.get_measurements(8231, None)
        mock_requests.request.assert_called_once_with(
            "POST",
            "https://meteoview2.gr/api/measurements",
            headers={
                "content-type": "application/json",
                "Authorization": "Bearer topsecretapitoken",
            },
            data=json.dumps(
                {
                    "sensor": [8231],
                    "datefrom": "1990-01-01",
                    "timefrom": "00:00",
                    "dateto": "1990-06-30",
                }
            ),
        )

    def test_ignores_time_zone(self, mock_requests):
        """Test request when timeseries_end_date is time-zone-aware

        get_measurements() should ignore the time zone of the supplied
        timeseries_end_date.
        """
        self._set_successful_request_result(mock_requests)
        time_zone = dt.timezone(dt.timedelta(hours=5), "MyTimezone")
        existing_end_date = dt.datetime(2022, 6, 14, 8, 0, tzinfo=time_zone)
        self.meteoview2_api_client.get_measurements(8231, existing_end_date)
        mock_requests.request.assert_called_once_with(
            "POST",
            "https://meteoview2.gr/api/measurements",
            headers={
                "content-type": "application/json",
                "Authorization": "Bearer topsecretapitoken",
            },
            data=json.dumps(
                {
                    "sensor": [8231],
                    "datefrom": "2022-06-14",
                    "timefrom": "08:01",
                    "dateto": "2022-12-11",
                }
            ),
        )

    def _set_successful_request_result(self, mock_requests):
        mock_requests.request.return_value.json.return_value = {
            "code": "200",
            "measurements": [
                {
                    "total_values": 2,
                    "values": [
                        {
                            "year": "2022",
                            "month": "5",
                            "day": "14",
                            "hour": "08",
                            "minute": "10",
                            "mvalue": "1.42",
                        },
                        {
                            "year": "2022",
                            "month": "5",
                            "day": "14",
                            "hour": "08",
                            "minute": "20",
                            "mvalue": "1.43",
                        },
                    ],
                }
            ],
        }


@patch("enhydris.telemetry.types.meteoview2.requests")
@freeze_time("2022-06-14 08:35")
class GetMeasurementsTwoRequestsTestCase(LoggedOnTestCaseBase):
    """Test the case where a semester is empty.

    In order to avoid getting too much data at once, get_measurements()
    only requests six months worth of data; it will only get the next
    six months the next time it's called. However, if the six months it
    initially asks for is empty, it immediately requests the next six
    months, and so on, until either it gets some data or it reaches the
    current date. Here we test the case where the six months initially
    asked for are empty and the next six months have some values.
    """

    def test_makes_two_requests(self, mock_requests):
        self._set_successful_request_result(mock_requests)
        existing_end_date = dt.datetime(2021, 6, 14, 8, 0)
        self.meteoview2_api_client.get_measurements(8231, existing_end_date)
        self.assertEqual(mock_requests.request.call_count, 2)

    def test_return_value(self, mock_requests):
        self._set_successful_request_result(mock_requests)
        existing_end_date = dt.datetime(2021, 6, 14, 8, 0)
        result = self.meteoview2_api_client.get_measurements(8231, existing_end_date)
        self.assertEqual(
            result.getvalue(), "2021-12-14T08:10:00,1.42,\n2021-12-14T08:20:00,1.43,\n"
        )

    def _set_successful_request_result(self, mock_requests):
        mock_requests.request.return_value.json.side_effect = [
            {
                "code": "200",
                "measurements": [{"total_values": 0}],
            },
            {
                "code": "200",
                "measurements": [
                    {
                        "total_values": 2,
                        "values": [
                            {
                                "year": "2021",
                                "month": "11",
                                "day": "14",
                                "hour": "08",
                                "minute": "10",
                                "mvalue": "1.42",
                            },
                            {
                                "year": "2021",
                                "month": "11",
                                "day": "14",
                                "hour": "08",
                                "minute": "20",
                                "mvalue": "1.43",
                            },
                        ],
                    }
                ],
            },
        ]


@patch("enhydris.telemetry.types.meteoview2.requests")
@freeze_time("2022-06-14 08:35")
class GetMeasurementsWithTwoCloseTimestampsTestCase(LoggedOnTestCaseBase):
    """Test successive timestamps less than one minute apart

    Enhydris can't handle the case where two timestamps differ in seconds
    only; therefore if such a thing happens we ignore the second timestamp.
    """

    def test_return_value(self, mock_requests):
        self._set_successful_request_result(mock_requests)
        existing_end_date = dt.datetime(2021, 6, 14, 8, 0)
        result = self.meteoview2_api_client.get_measurements(8231, existing_end_date)
        self.assertEqual(
            result.getvalue(),
            "2021-12-14T08:10:00,1.42,\n" "2021-12-14T08:20:00,1.43,\n",
        )

    def _set_successful_request_result(self, mock_requests):
        mock_requests.request.return_value.json.side_effect = [
            {
                "code": "200",
                "measurements": [{"total_values": 0}],
            },
            {
                "code": "200",
                "measurements": [
                    {
                        "total_values": 3,
                        "values": [
                            {
                                "year": "2021",
                                "month": "11",
                                "day": "14",
                                "hour": "08",
                                "minute": "10",
                                "second": "07",
                                "mvalue": "1.42",
                            },
                            {
                                "year": "2021",
                                "month": "11",
                                "day": "14",
                                "hour": "08",
                                "minute": "10",
                                "second": "37",
                                "mvalue": "1.47",
                            },
                            {
                                "year": "2021",
                                "month": "11",
                                "day": "14",
                                "hour": "08",
                                "minute": "20",
                                "mvalue": "1.43",
                            },
                        ],
                    }
                ],
            },
        ]


@patch("enhydris.telemetry.types.meteoview2.requests")
@freeze_time("2022-06-14 08:35")
class GetMeasurementsWithEmptyResultTestCase(LoggedOnTestCaseBase):
    """Test getting measurements where all are empty

    We start at 1990-01-01 and pretend there are no measurements up to
    today (2022-06-14). This will make 66 requests (one for each 180
    days, until it goes past today) and eventually return empty.
    """

    def test_makes_66_requests(self, mock_requests):
        self._set_successful_request_result(mock_requests)
        self.meteoview2_api_client.get_measurements(8231, None)
        self.assertEqual(mock_requests.request.call_count, 66)

    def test_return_value(self, mock_requests):
        self._set_successful_request_result(mock_requests)
        result = self.meteoview2_api_client.get_measurements(8231, None)
        self.assertEqual(result.getvalue(), "")

    def _set_successful_request_result(self, mock_requests):
        mock_requests.request.return_value.json.return_value = {
            "code": "200",
            "measurements": [{"total_values": 0}],
        }
