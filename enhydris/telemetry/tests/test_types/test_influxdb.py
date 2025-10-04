import datetime as dt
import textwrap
from unittest.mock import patch

from django.test import TestCase

import requests
from model_bakery import baker

from enhydris.models import Station
from enhydris.telemetry import TelemetryError, drivers
from enhydris.telemetry.models import Telemetry
from enhydris.telemetry.types.influxdb import (
    InfluxConnectionDataForm,
    TelemetryAPIClient,
)


class TelemetryAPIClientTestCaseBase(TestCase):
    def setUp(self):
        telemetry = Telemetry(
            username="alice",
            password="topsecretpassword",
            device_locator="http://1.2.3.4",
            remote_station_id="hobbiton",
            additional_config={
                "bucket": "thebucket",
                "measurement": "themeasurement",
                "station_tag": "thestationtag",
            },
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


@patch("enhydris.telemetry.types.influxdb.requests.post")
class InfluxConnectionDataFormTestCase(TestCase):
    all_form_data = {
        "username": "alice",
        "password": "topsecretpassword",
        "device_locator": "http://1.2.3.4",
        "_bucket": "thebucket",
        "_measurement": "themeasurement",
        "_station_tag": "thestationtag",
    }

    @classmethod
    def setUpTestData(cls):
        cls.station = baker.make(Station)
        cls.form_kwargs = {"driver": drivers["influxdb"], "station": cls.station}

    def test_valid(self, m):
        self._set_successful_request_result(m)
        form = InfluxConnectionDataForm(self.all_form_data, **self.form_kwargs)
        self.assertTrue(form.is_valid())

    def test_requires_bucket(self, m):
        self._set_successful_request_result(m)
        data = {x: y for x, y in self.all_form_data.items() if x != "_bucket"}
        form = InfluxConnectionDataForm(data, **self.form_kwargs)
        self.assertFalse(form.is_valid())

    def test_requires_measurement(self, m):
        self._set_successful_request_result(m)
        data = {x: y for x, y in self.all_form_data.items() if x != "_measurement"}
        form = InfluxConnectionDataForm(data, **self.form_kwargs)
        self.assertFalse(form.is_valid())

    def test_requires_station_tag(self, m):
        self._set_successful_request_result(m)
        data = {x: y for x, y in self.all_form_data.items() if x != "_station_tag"}
        form = InfluxConnectionDataForm(data, **self.form_kwargs)
        self.assertFalse(form.is_valid())

    def test_invalid_on_garbage(self, m):
        m.return_value.__enter__.return_value.iter_lines.return_value = [
            "this,is,not,csv",
            "at,all",
        ]
        form = InfluxConnectionDataForm(self.all_form_data, **self.form_kwargs)
        self.assertFalse(form.is_valid())

    def test_invalid_on_no_stations(self, m):
        m.return_value.__enter__.return_value.iter_lines.return_value = [
            ",result,table,_value"
        ]
        form = InfluxConnectionDataForm(self.all_form_data, **self.form_kwargs)
        self.assertFalse(form.is_valid())

    def _set_successful_request_result(self, mock_post):
        mock_post.return_value.__enter__.return_value.iter_lines.return_value = [
            ",result,table,_value",
            ",_result,0,hobbiton",
            ",_result,0,rivendell",
            ",_result,0,bree",
        ]


@patch("enhydris.telemetry.types.influxdb.requests.post")
class ResponseErrorTestCase(TelemetryAPIClientTestCaseBase):
    def test_raises_on_bad_status_code(self, m):
        m.return_value.__enter__.return_value.raise_for_status.side_effect = (
            requests.Timeout
        )
        with self.assertRaises(TelemetryError):
            self.telemetry_api_client.get_stations()

    def test_raises_on_ssl_error(self, m):
        m.side_effect = requests.exceptions.SSLError
        with self.assertRaises(TelemetryError):
            self.telemetry_api_client.get_stations()


@patch("enhydris.telemetry.types.influxdb.requests.post")
class GetStationsTestCase(TelemetryAPIClientTestCaseBase):
    def test_makes_request(self, mock_requests_post):
        self._set_successful_request_result(mock_requests_post)
        self.telemetry_api_client.get_stations()
        self._assert_common_request_stuff(mock_requests_post)
        self.assertEqual(
            mock_requests_post.mock_calls[0].kwargs["data"],
            textwrap.dedent(
                """\
                    from(bucket: "thebucket")
                    |> range(start: 1990-01-01)
                    |> filter(fn: (r) => r._measurement == "themeasurement")
                    |> keep(columns: ["thestationtag"])
                    |> group()
                    |> distinct(column: "thestationtag")
                """
            ),
        )

    def test_returns_stations(self, mock_requests_post):
        self._set_successful_request_result(mock_requests_post)
        self.assertEqual(
            self.telemetry_api_client.get_stations(),
            {"hobbiton": "", "rivendell": "", "bree": ""},
        )

    def test_raises_on_garbage(self, m):
        m.return_value.__enter__.return_value.iter_lines.return_value = [
            "this,is,not,csv",
            "at,all",
        ]
        with self.assertRaises(TelemetryError):
            self.telemetry_api_client.get_stations()

    def test_raises_on_binary_garbage(self, m):
        m.return_value.__enter__.return_value.iter_lines.return_value = [
            b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09"
        ]
        with self.assertRaises(TelemetryError):
            self.telemetry_api_client.get_stations()

    def _set_successful_request_result(self, mock_post):
        mock_post.return_value.__enter__.return_value.iter_lines.return_value = [
            ",result,table,_value",
            ",_result,0,hobbiton",
            ",_result,0,rivendell",
            ",_result,0,bree",
        ]


@patch("enhydris.telemetry.types.influxdb.requests.post")
class GetSensorsTestCase(TelemetryAPIClientTestCaseBase):
    def test_makes_request(self, mock_requests_post):
        self._set_successful_request_result(mock_requests_post)
        self.telemetry_api_client.get_sensors()
        self._assert_common_request_stuff(mock_requests_post)
        self.assertEqual(
            mock_requests_post.mock_calls[0].kwargs["data"],
            textwrap.dedent(
                """\
                    import "influxdata/influxdb/schema"

                    schema.fieldKeys(
                        bucket: "thebucket",
                        predicate: (r) => r._measurement == "themeasurement",
                    )
                """
            ),
        )

    def test_raises_on_garbage(self, m):
        m.return_value.__enter__.return_value.iter_lines.return_value = [
            "this,is,not,csv",
            "at,all",
        ]
        with self.assertRaises(TelemetryError):
            self.telemetry_api_client.get_sensors()

    def test_returns_sensors(self, mock_requests_post):
        self._set_successful_request_result(mock_requests_post)
        self.telemetry_api_client.get_sensors()
        self.assertEqual(
            self.telemetry_api_client.get_sensors(),
            {"air temperature (degC)": "", "barometric pressure (hPa)": ""},
        )

    def _set_successful_request_result(self, m):
        m.return_value.__enter__.return_value.iter_lines.return_value = [
            ",result,table,_value",
            ",_result,0,air temperature (degC)",
            ",_result,0,barometric pressure (hPa)",
        ]


@patch("enhydris.telemetry.types.influxdb.requests.post")
class GetMeasurementsTestCase(TelemetryAPIClientTestCaseBase):
    def test_makes_request(self, mock_requests_post):
        self._set_successful_request_result(mock_requests_post)
        existing_end_date = dt.datetime(2022, 6, 14, 8, 0, tzinfo=dt.timezone.utc)
        self.telemetry_api_client.get_measurements("temperature", existing_end_date)
        self._assert_common_request_stuff(mock_requests_post)
        self.assertEqual(
            mock_requests_post.mock_calls[0].kwargs["data"],
            textwrap.dedent(
                """\
                from(bucket: "thebucket")
                |> range(start: 2022-06-14T08:01:00+00:00)
                |> filter(fn: (r) => r._measurement == "themeasurement")
                |> filter(fn: (r) => r["thestationtag"] == "hobbiton")
                |> filter(fn: (r) => r._field == "temperature")
                |> keep(columns: ["_time", "_value"])
                |> limit(n: 20000)
                """
            ),
        )

    def test_raises_on_garbage(self, m):
        m.return_value.__enter__.return_value.iter_lines.return_value = [
            "this,is,not,csv",
            "at,all",
        ]
        with self.assertRaises(TelemetryError):
            self.telemetry_api_client.get_measurements("temperature", None)

    def test_return_value(self, mock_requests_post):
        self._set_successful_request_result(mock_requests_post)
        existing_end_date = dt.datetime(2022, 6, 14, 8, 0)
        result = self.telemetry_api_client.get_measurements(
            "temperature", existing_end_date
        )
        self.assertEqual(
            result.getvalue(),
            textwrap.dedent(
                """\
                    2025-09-10T14:51:00,2.1,
                    2025-09-10T15:01:00,2.2,
                    2025-09-10T15:11:00,2.6,
                    2025-09-10T15:21:00,2.2,
                    2025-09-10T15:31:00,1.5,
                """
            ),
        )

    def test_request_when_no_start_date(self, mock_requests_post):
        """Test request when no start date

        get_measurements() can be called with timeseries_end_date=None. In that case, it
        should assume a start date of 1 Jan 1990.
        """
        self._set_successful_request_result(mock_requests_post)
        self.telemetry_api_client.get_measurements("temperature", None)
        self._assert_common_request_stuff(mock_requests_post)
        self.assertEqual(
            mock_requests_post.mock_calls[0].kwargs["data"],
            textwrap.dedent(
                """\
                from(bucket: "thebucket")
                |> range(start: 1990-01-01T00:00:00+00:00)
                |> filter(fn: (r) => r._measurement == "themeasurement")
                |> filter(fn: (r) => r["thestationtag"] == "hobbiton")
                |> filter(fn: (r) => r._field == "temperature")
                |> keep(columns: ["_time", "_value"])
                |> limit(n: 20000)
                """
            ),
        )

    def _set_successful_request_result(self, mock_post):
        mock_post.return_value.__enter__.return_value.iter_lines.return_value = [
            ",result,table,_time,_value",
            ",_result,0,2025-09-10T14:51:00Z,2.1",
            ",_result,0,2025-09-10T15:01:00Z,2.2",
            ",_result,0,2025-09-10T15:11:00Z,2.6",
            ",_result,0,2025-09-10T15:21:00Z,2.2",
            ",_result,0,2025-09-10T15:31:00Z,1.5",
        ]
