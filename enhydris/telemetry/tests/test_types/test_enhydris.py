import datetime as dt
import textwrap
from unittest.mock import call, patch

from django.test import TestCase

import requests

from enhydris.telemetry import TelemetryError
from enhydris.telemetry.models import Telemetry
from enhydris.telemetry.types.enhydris import TelemetryAPIClient


class TelemetryAPIClientTestCaseBase(TestCase):
    def setUp(self):
        telemetry = Telemetry(
            username="alice",
            password="topsecretpassword",
            device_locator="http://1.2.3.4",
            remote_station_id="42",
        )
        self.telemetry_api_client = TelemetryAPIClient(telemetry)

    def _assert_common_request_stuff(self, mock_requests_post):
        mock_requests_post.assert_called_once()
        args = mock_requests_post.mock_calls[0].args
        kwargs = mock_requests_post.mock_calls[0].kwargs
        self.assertEqual(args[0], "http://1.2.3.4/query?org=alice")
        self.assertEqual(kwargs["verify"], False)
        self.assertEqual(
            kwargs["headers"],
            {
                "Authorization": "Token topsecretpassword",
                "Content-Type": "application/vnd.flux",
                "Accept": "application/csv",
            },
        )


@patch("requests.Session.get")
class GetStationsTestCase(TelemetryAPIClientTestCaseBase):
    def test_makes_request(self, m):
        self._set_successful_request_result(m)
        self.telemetry_api_client.get_stations()
        m.assert_called_once_with("http://1.2.3.4/api/stations/")

    def test_returns_stations(self, m):
        self._set_successful_request_result(m)
        self.assertEqual(
            self.telemetry_api_client.get_stations(),
            {42: "hobbiton", 43: "rivendell", 44: "bree"},
        )

    def test_raises_on_bad_status_code(self, m):
        m.side_effect = requests.Timeout
        with self.assertRaises(TelemetryError):
            self.telemetry_api_client.get_stations()

    def test_raises_on_ssl_error(self, m):
        m.side_effect = requests.exceptions.SSLError
        with self.assertRaises(TelemetryError):
            self.telemetry_api_client.get_stations()

    def test_raises_on_garbage(self, m):
        m.return_value.json.return_value = ["this,is,not,valid,stuff"]
        with self.assertRaises(TelemetryError):
            self.telemetry_api_client.get_stations()

    def _set_successful_request_result(self, m):
        m.return_value.json.return_value = {
            "count": 3,
            "next": None,
            "previous": None,
            "results": [
                {"id": 42, "name": "hobbiton"},
                {"id": 43, "name": "rivendell"},
                {"id": 44, "name": "bree"},
            ],
        }


@patch("requests.Session.get")
class GetSensorsTestCase(TelemetryAPIClientTestCaseBase):
    def test_makes_request(self, m):
        self._set_successful_request_result(m)
        self.telemetry_api_client.get_sensors()
        expected_call_args_list = [
            call("http://1.2.3.4/api/stations/42/timeseriesgroups/"),
            call("http://1.2.3.4/api/stations/42/timeseriesgroups/421/timeseries/"),
            call("http://1.2.3.4/api/stations/42/timeseriesgroups/422/timeseries/"),
        ]
        self.assertEqual(m.call_args_list, expected_call_args_list)

    def test_returns_timeseries(self, m):
        self.maxDiff = 1024
        self._set_successful_request_result(m)
        self.assertEqual(
            self.telemetry_api_client.get_sensors(),
            {
                "421 4211": "temperature - Initial Raw 5min",
                "421 4212": "temperature - Aggregated Hi 1h",
                "422 4221": "humidity - Initial Raw 5min",
            },
        )

    def test_raises_on_bad_status_code(self, m):
        m.side_effect = requests.Timeout
        with self.assertRaises(TelemetryError):
            self.telemetry_api_client.get_sensors()

    def test_raises_on_ssl_error(self, m):
        m.side_effect = requests.exceptions.SSLError
        with self.assertRaises(TelemetryError):
            self.telemetry_api_client.get_sensors()

    def test_raises_on_garbage(self, m):
        m.return_value.json.return_value = ["this,is,not,valid,stuff"]
        with self.assertRaises(TelemetryError):
            self.telemetry_api_client.get_sensors()

    def _set_successful_request_result(self, m):
        m.return_value.json.side_effect = [
            {
                "count": 3,
                "next": None,
                "previous": None,
                "results": [
                    {"id": 421, "name": "temperature"},
                    {"id": 422, "name": "humidity"},
                ],
            },
            {
                "count": 2,
                "next": None,
                "previous": None,
                "results": [
                    {"id": 4211, "name": "Raw", "type": "Initial", "time_step": "5min"},
                    {"id": 4212, "name": "Hi", "type": "Aggregated", "time_step": "1h"},
                ],
            },
            {
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    {"id": 4221, "name": "Raw", "type": "Initial", "time_step": "5min"},
                ],
            },
        ]


@patch("requests.Session.get")
class GetMeasurementsTestCase(TelemetryAPIClientTestCaseBase):
    def test_makes_request(self, m):
        self._set_successful_request_result(m)
        existing_end_date = dt.datetime(2022, 6, 14, 8, 0, tzinfo=dt.timezone.utc)
        self.telemetry_api_client.get_measurements("421 4211", existing_end_date)
        m.assert_called_once_with(
            "http://1.2.3.4/api/stations/42/timeseriesgroups/421/timeseries/4211/data/",
            params={
                "fmt": "hts",
                "start_date": "2022-06-14T08:01:00+00:00",
                "end_date": None,
                "timezone": None,
            },
        )

    def test_returns_data(self, m):
        self._set_successful_request_result(m)
        existing_end_date = dt.datetime(2022, 6, 14, 8, 0, tzinfo=dt.timezone.utc)
        rslt = self.telemetry_api_client.get_measurements("421 4211", existing_end_date)
        self.assertEqual(
            rslt.getvalue(),
            textwrap.dedent(
                """\
                2025-09-10 14:51,2.100000,\r
                2025-09-10 15:01,2.200000,\r
                """
            ),
        )

    def test_raises_on_bad_status_code(self, m):
        m.side_effect = requests.Timeout
        existing_end_date = dt.datetime(2022, 6, 14, 8, 0, tzinfo=dt.timezone.utc)
        with self.assertRaises(TelemetryError):
            self.telemetry_api_client.get_measurements("421 4211", existing_end_date)

    def test_raises_on_ssl_error(self, m):
        m.side_effect = requests.exceptions.SSLError
        existing_end_date = dt.datetime(2022, 6, 14, 8, 0, tzinfo=dt.timezone.utc)
        with self.assertRaises(TelemetryError):
            self.telemetry_api_client.get_measurements("421 4211", existing_end_date)

    def test_raises_on_garbage(self, m):
        m.return_value.text = "this,is,not,valid,stuff"
        existing_end_date = dt.datetime(2022, 6, 14, 8, 0, tzinfo=dt.timezone.utc)
        with self.assertRaises(TelemetryError):
            self.telemetry_api_client.get_measurements("421 4211", existing_end_date)

    def test_raises_on_binary_garbage(self, m):
        m.return_value.text = "\x00\x01\x02\x03\x04"
        existing_end_date = dt.datetime(2022, 6, 14, 8, 0, tzinfo=dt.timezone.utc)
        with self.assertRaises(TelemetryError):
            self.telemetry_api_client.get_measurements("421 4211", existing_end_date)

    def _set_successful_request_result(self, m):
        m.return_value.text = textwrap.dedent(
            """\
            name=Hello
            timezone=+0000

            2025-09-10 14:51,2.1,
            2025-09-10 15:01,2.2,
            """
        )
