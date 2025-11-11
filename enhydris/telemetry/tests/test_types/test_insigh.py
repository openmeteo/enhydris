from __future__ import annotations

import datetime as dt
import textwrap
from unittest import TestCase
from unittest.mock import patch

from enhydris.telemetry.models import Telemetry
from enhydris.telemetry.types.insigh import TelemetryAPIClient


class GetStationsTestCase(TestCase):
    def setUp(self) -> None:
        self.patcher = patch("enhydris.telemetry.types.insigh.requests.get")
        self.mock_get = self.patcher.start()
        self.mock_get.return_value.json.return_value = [
            {
                "id": "station-1-id",
                "name": "Station 1",
                "metadata": {
                    "dataChannel": "station-1-data-channel",
                },
            },
            {
                "id": "station-2-id",
                "name": "Station 2",
                "metadata": {
                    "dataChannel": "station-2-data-channel",
                },
            },
        ]
        telemetry = Telemetry(type="insigh.io", password="top-secret-token")
        self.client = TelemetryAPIClient(telemetry)
        self.result = self.client.get_stations()

    def tearDown(self) -> None:
        self.patcher.stop()

    def test_request(self):
        self.mock_get.assert_called_once_with(
            "https://console.insigh.io/mf-rproxy/device/list",
            headers={
                "Authorization": "top-secret-token",
            },
        )

    def test_results(self):
        expected = {
            "station-1-id/station-1-data-channel": "Station 1",
            "station-2-id/station-2-data-channel": "Station 2",
        }
        self.assertEqual(self.result, expected)


class GetSensorsTestCase(TestCase):
    def setUp(self) -> None:
        self.patcher = patch("enhydris.telemetry.types.insigh.requests.get")
        self.mock_get = self.patcher.start()
        self.mock_get.return_value.json.return_value = [
            {
                "time": "2025-11-11T04:45:04Z",
                "name": "f412fac3b9d0-Precipitation",
                "publisher": "station-1-id",
                "subtopic": "station-1-id.transformations",
                "protocol": "transformations:mqtt",
                "unit": "mm",
                "updateTime": "0",
                "value": 0,
                "stringValue": None,
            },
            {
                "time": "2025-11-11T04:45:04Z",
                "name": "f412fac3b9d0-Precipitation_Raw",
                "publisher": "station-1-id",
                "subtopic": "station-1-id",
                "protocol": "mqtt",
                "unit": "count",
                "updateTime": "0",
                "value": 0,
                "stringValue": None,
            },
        ]
        telemetry = Telemetry(
            type="insigh.io",
            password="top-secret-token",
            remote_station_id="station-1-id/station-1-data-channel",
        )
        self.client = TelemetryAPIClient(telemetry)
        self.result = self.client.get_sensors()

    def tearDown(self) -> None:
        self.patcher.stop()

    def test_request(self):
        self.mock_get.assert_called_once_with(
            "https://console.insigh.io/mf-rproxy/device/lastMeasurement",
            headers={
                "Authorization": "top-secret-token",
            },
            params={
                "channel": "station-1-data-channel",
                "id": "station-1-id",
            },
        )

    def test_results(self):
        expected = {
            "Precipitation": "",
            "Precipitation_Raw": "",
        }
        self.assertEqual(self.result, expected)


class GetMeasurementsTestCase(TestCase):
    def setUp(self) -> None:
        self.patcher = patch("enhydris.telemetry.types.insigh.requests.get")
        self.mock_get = self.patcher.start()
        self.mock_get.return_value.text = textwrap.dedent(
            """\
            "time","publisher","R.Humidity_Raw","cell_con_duration","uptime","vbatt","cell_mcc","Temperature_Raw","cell_mnc","cell_rsrp","W.Speed_Raw","cell_rsrq","cell_rssi","pcnt_count_formula_1","Precipitation_Raw","S.Radiation_Raw","board_humidity","pcnt_edge_count_1","board_temp","cell_act_duration","pcnt_period_s_1","cell_att_duration","reset_cause","pcnt_period_1","time_diff","S_Radiation","Precipitation","R_Humidity","W_Speed","Temperature","pcnt_count_formula_2","pcnt_edge_count_2","pcnt_period_2","pcnt_period_s_2"
            "1762834504000","station-1-id",1919.188,,5347,3562,,1228.688,,,397.125,,,0,0,400.125,57.676,0,13.122,,900.608,,4,,,0.12,0,94.95,-0.11,11.79,,,,
            "1762835403000","station-1-id",1914.187,,5347,3538,,1226.25,,,397.062,,,0,0,400.125,57.634,0,13.101,,899.618,,4,,,0.12,0,94.64,-0.11,11.64,,,,
        """
        )
        telemetry = Telemetry(
            type="insigh.io",
            password="top-secret-token",
            remote_station_id="station-1-id/station-1-data-channel",
        )
        self.client = TelemetryAPIClient(telemetry)
        self.mock_get.reset_mock()

    def tearDown(self) -> None:
        self.patcher.stop()

    def test_request_url(self):
        self.client.get_measurements(
            sensor_id="Precipitation", timeseries_end_date=None
        )
        self.mock_get.assert_called_once_with(
            "https://console.insigh.io/mf-rproxy/measurement/queryPack",
            headers={
                "Authorization": "top-secret-token",
            },
            params={
                "channel": "station-1-data-channel",
                "publisher": "station-1-id",
                "startRange": "1970-01-01T00:01:00Z",
                "limit": 25000,
                "format": "csv",
            },
        )

    def test_request_url_with_timeseries_end_date(self):
        self.client.get_measurements(
            sensor_id="Precipitation",
            timeseries_end_date=dt.datetime(
                2024, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc
            ),
        )
        self.mock_get.assert_called_once_with(
            "https://console.insigh.io/mf-rproxy/measurement/queryPack",
            headers={
                "Authorization": "top-secret-token",
            },
            params={
                "channel": "station-1-data-channel",
                "publisher": "station-1-id",
                "startRange": "2024-01-01T12:01:00Z",
                "limit": 25000,
                "format": "csv",
            },
        )

    def test_result_1(self):
        result = self.client.get_measurements(
            sensor_id="Precipitation", timeseries_end_date=None
        )
        expected = textwrap.dedent(
            """\
            2025-11-11T04:15:04,0,
            2025-11-11T04:30:03,0,
            """
        )
        self.assertEqual(result.getvalue(), expected)

    def test_result_2(self):
        result = self.client.get_measurements(
            sensor_id="R_Humidity", timeseries_end_date=None
        )
        expected = textwrap.dedent(
            """\
            2025-11-11T04:15:04,94.95,
            2025-11-11T04:30:03,94.64,
            """
        )
        self.assertEqual(result.getvalue(), expected)
