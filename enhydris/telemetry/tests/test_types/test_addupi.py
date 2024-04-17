import datetime as dt
from unittest import TestCase
from unittest.mock import patch

from freezegun import freeze_time
from parameterized import parameterized
from requests import Timeout

from enhydris.telemetry import TelemetryError
from enhydris.telemetry.models import Telemetry
from enhydris.telemetry.types.addupi import TelemetryAPIClient


class TelemetryAPIClientTestCaseBase(TestCase):
    def setUp(self):
        telemetry = Telemetry(
            username="alice",
            password="topsecretpassword",
            device_locator="http://1.2.3.4",
            remote_station_id=823,
        )
        self.telemetry_api_client = TelemetryAPIClient(telemetry)


@patch("enhydris.telemetry.types.addupi.requests.get")
class MakeRequestTestCase(TelemetryAPIClientTestCaseBase):
    def test_raises_on_bad_status_code(self, m):
        m.return_value.__enter__.return_value.raise_for_status.side_effect = Timeout
        with self.assertRaises(TelemetryError):
            self.telemetry_api_client._make_request("hello=world")

    def test_ok_when_we_get_an_xml_response(self, m):
        m.return_value.__enter__.return_value.content = b"<somexml>hello</somexml>"
        client = self.telemetry_api_client
        self.assertEqual(client._make_request("hello=world").tag, "somexml")

    def test_accesses_correct_url(self, m):
        m.return_value.__enter__.return_value.content = b"<somexml>hello</somexml>"
        self.telemetry_api_client._make_request("hello=world")
        m.assert_called_once_with("http://1.2.3.4/addUPI?hello=world", verify=False)

    def test_appends_session_id_to_query_string(self, m):
        m.return_value.__enter__.return_value.content = b"<somexml>hello</somexml>"
        self.telemetry_api_client.session_id = "topsecretsessionid"
        self.telemetry_api_client._make_request("hello=world")
        m.assert_called_once_with(
            "http://1.2.3.4/addUPI?hello=world&session-id=topsecretsessionid",
            verify=False,
        )


@patch("enhydris.telemetry.types.addupi.requests.get")
class ConnectTestCase(TelemetryAPIClientTestCaseBase):
    def test_makes_request(self, mock_requests_get):
        self._set_successful_request_result(mock_requests_get)
        self.telemetry_api_client.connect()
        mock_requests_get.assert_called_once_with(
            "http://1.2.3.4/addUPI?function=login&user=alice&passwd=topsecretpassword",
            verify=False,
        )

    def test_sets_session_id(self, mock_requests_get):
        self._set_successful_request_result(mock_requests_get)
        self.telemetry_api_client.connect()
        self.assertEqual(self.telemetry_api_client.session_id, "topsecretsessionid")

    def _set_successful_request_result(self, mock_requests_get):
        mock_requests_get.return_value.__enter__.return_value.content = (
            b"<response><result><string>topsecretsessionid</string></result></response>"
        )


@patch("enhydris.telemetry.types.addupi.requests.get")
class DisconnectTestCase(TelemetryAPIClientTestCaseBase):
    def setUp(self):
        super().setUp()
        self.telemetry_api_client.session_id = "mysessionid"

    def test_makes_request(self, mock_requests_get):
        self._set_request_result(mock_requests_get)
        self.telemetry_api_client.disconnect()
        mock_requests_get.assert_called_once_with(
            "http://1.2.3.4/addUPI?function=logout&session-id=mysessionid",
            verify=False,
        )

    def test_resets_session_id(self, mock_requests_get):
        self._set_request_result(mock_requests_get)
        self.telemetry_api_client.disconnect()
        self.assertFalse(hasattr(self.telemetry_api_client, "session_id"))

    def test_does_not_make_request_if_no_session_id(self, mock_requests_get):
        self._set_request_result(mock_requests_get)
        del self.telemetry_api_client.session_id
        self.telemetry_api_client.disconnect()
        mock_requests_get.assert_not_called()

    def _set_request_result(self, mock_requests_get):
        mock_requests_get.return_value.__enter__.return_value.content = b"<ok></ok>"


class LoggedOnTestCaseBase(TelemetryAPIClientTestCaseBase):
    def setUp(self):
        super().setUp()
        self.telemetry_api_client.session_id = "topsecretsessionid"


@patch("enhydris.telemetry.types.addupi.requests.get")
class GetStationsTestCase(LoggedOnTestCaseBase):
    def test_makes_request(self, mock_requests_get):
        self._set_successful_request_result(mock_requests_get)
        self.telemetry_api_client.get_stations()
        mock_requests_get.assert_called_once_with(
            "http://1.2.3.4/addUPI?function=getconfig&session-id=topsecretsessionid",
            verify=False,
        )

    def test_returns_stations(self, mock_requests_get):
        self._set_successful_request_result(mock_requests_get)
        self.assertEqual(
            self.telemetry_api_client.get_stations(),
            {"1852": "Hobbiton", "2581": "Rivendell"},
        )

    def test_shows_subclass(self, mock_requests_get):
        self._set_successful_request_result(mock_requests_get, "station")
        self.assertEqual(
            self.telemetry_api_client.get_stations(),
            {"1852": "Hobbiton [station]", "2581": "Rivendell [station]"},
        )

    def _set_successful_request_result(self, mock_requests_get, subclass=""):
        mock_requests_get.return_value.__enter__.return_value.content = (
            "<response>"
            f"  <node class='DEVICE' id='1852' name='Hobbiton' subclass='{subclass}'>"
            "  </node>"
            f"  <node class='DEVICE' id='2581' name='Rivendell' subclass='{subclass}'>"
            "  </node>"
            "</response>"
        ).encode()


@patch("enhydris.telemetry.types.addupi.requests.get")
class GetSensorsTestCase(LoggedOnTestCaseBase):
    def test_makes_request(self, mock_requests_get):
        self._set_successful_request_result(mock_requests_get)
        self.telemetry_api_client.get_sensors()
        mock_requests_get.assert_called_once_with(
            "http://1.2.3.4/addUPI?function=getconfig&session-id=topsecretsessionid",
            verify=False,
        )

    def test_returns_sensors(self, mock_requests_get):
        self._set_successful_request_result(mock_requests_get)
        self.telemetry_api_client.get_sensors()
        self.assertEqual(
            self.telemetry_api_client.get_sensors(),
            {"42a": "temperature", "43b": "humidity"},
        )

    def _set_successful_request_result(self, mock_requests_get):
        mock_requests_get.return_value.__enter__.return_value.content = (
            "<response>"
            "  <node class='DEVICE' id='823'>"
            "    <nodes>"
            "      <node id='42a' name='temperature'>"
            "      </node>"
            "      <node id='43b' name='humidity'>"
            "      </node>"
            "    </nodes>"
            "  </node>"
            "</response>"
        ).encode()


@patch("enhydris.telemetry.types.addupi.requests.get")
@freeze_time("2022-06-14 08:35")
class GetMeasurementsTestCase(LoggedOnTestCaseBase):
    def test_makes_request(self, mock_requests_get):
        self._set_successful_request_result(mock_requests_get)
        existing_end_date = dt.datetime(2022, 6, 14, 8, 0, tzinfo=dt.timezone.utc)
        self.telemetry_api_client.get_measurements(8231, existing_end_date)
        # 1655193600 is 2022-06-14T08:00 in seconds from the epoch
        mock_requests_get.assert_called_once_with(
            "http://1.2.3.4/addUPI?function=getdata&id=8231&df=time_t"
            "&date=1655193600&slots=10000&session-id=topsecretsessionid",
            verify=False,
        )

    def test_return_value(self, mock_requests_get):
        self._set_successful_request_result(mock_requests_get)
        existing_end_date = dt.datetime(2022, 6, 14, 8, 0)
        result = self.telemetry_api_client.get_measurements(8231, existing_end_date)
        self.assertEqual(
            result.getvalue(), "2022-06-14T08:10:00,1.42,\n2022-06-14T08:20:00,1.43,\n"
        )

    def test_request_when_no_start_date(self, mock_requests_get):
        """Test request when no start date

        get_measurements() can be called with timeseries_end_date=None. In that case, it
        should assume a start date of 1 Jan 1990 (or 631152000 in time_t). (In that case
        the API wouldn't respond with what we mock it to respond with, i.e. values in
        2022, but this doesn't affect the unit test.)
        """
        self._set_successful_request_result(mock_requests_get)
        self.telemetry_api_client.get_measurements(8231, None)
        mock_requests_get.assert_called_once_with(
            "http://1.2.3.4/addUPI?function=getdata&id=8231&df=time_t"
            "&date=631152000&slots=10000&session-id=topsecretsessionid",
            verify=False,
        )

    def _set_successful_request_result(self, mock_requests_get):
        mock_requests_get.return_value.__enter__.return_value.content = (
            "<response>"
            "    <node>"
            "        <v t='1655194200' s='0'>1.42</v>"
            "        <v t='+600' s='0'>1.43</v>"
            "    </node>"
            "</response>"
        ).encode()


@patch("enhydris.telemetry.types.addupi.requests.get")
@freeze_time("2022-06-14 08:35")
class ReturnedStatusTestCase(LoggedOnTestCaseBase):
    @parameterized.expand(
        [
            (3, 'invalid status value .s="3".'),
            (-100, 'invalid status value .s="-100".'),
            ("hello", 'invalid status value .s="hello".'),
        ]
    )
    def test_error_handling(self, mock_requests_get, s, error_msg):
        self._set_s_request_result(s, mock_requests_get)
        with self.assertRaisesRegex(TelemetryError, error_msg):
            self.telemetry_api_client.get_measurements(8231, None)

    @parameterized.expand(
        [
            (0, ""),
            (1, "INVALID"),
            (2, "INVALID"),
            (-99, "MISSING"),
            (-1, "MISSING"),
        ]
    )
    def test_flag(self, mock_requests_get, s, flag):
        self._set_s_request_result(s, mock_requests_get)
        result = self.telemetry_api_client.get_measurements(8231, None)
        self.assertEqual(result.getvalue(), f"2022-06-14T08:10:00,1.42,{flag}\n")

    def _set_s_request_result(self, s, mock_requests_get):
        mock_requests_get.return_value.__enter__.return_value.content = (
            "<response>"
            "    <node>"
            f"        <v t='1655194200' s='{s}'>1.42</v>"
            "    </node>"
            "</response>"
        ).encode()

    def test_s_attribute_missing(self, mock_requests_get):
        mock_requests_get.return_value.__enter__.return_value.content = (
            "<response>"
            "    <node>"
            "        <v t='1655194200'>1.42</v>"
            "    </node>"
            "</response>"
        ).encode()
        with self.assertRaisesRegex(TelemetryError, 'invalid status value .s="None".'):
            self.telemetry_api_client.get_measurements(8231, None)
