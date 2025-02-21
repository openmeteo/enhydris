from unittest.mock import MagicMock

from django.test import TestCase

from model_bakery import baker

from enhydris.models import Station, TimeseriesGroup
from enhydris.telemetry import TelemetryError
from enhydris.telemetry.forms import (
    ChooseSensorForm,
    ChooseStationForm,
    ConnectionDataForm,
)
from enhydris.telemetry.types import TelemetryAPIClientBase


class TestTelemetryAPIClient(TelemetryAPIClientBase):
    username_label = "Email"
    password_label = "API key"
    device_locator_label = "URI"
    device_locator_help_text = "Do it!"
    hide_data_timezone = True
    hide_device_locator = False

    __init__ = MagicMock(return_value=None)
    connect = MagicMock()
    disconnect = MagicMock()
    get_stations = MagicMock()
    get_sensors = MagicMock()

    @classmethod
    def reset_mocks(cls):
        for x in ("__init__", "connect", "disconnect", "get_stations", "get_sensors"):
            getattr(cls, x).reset_mock()


class ConnectionDataFormTestCase(TestCase):
    def setUp(self):
        TestTelemetryAPIClient.reset_mocks()
        username = "hello@world.com"
        password = "topsecret"
        loc = "http://1.2.3.4"
        self.form = ConnectionDataForm(
            {"username": username, "password": password, "device_locator": loc},
            driver=TestTelemetryAPIClient,
            station="irrelevant",
        )

    def test_connects(self):
        self.form.is_valid()
        TestTelemetryAPIClient.connect.assert_called_once()

    def test_disconnects(self):
        self.form.is_valid()
        TestTelemetryAPIClient.disconnect.assert_called_once()

    def test_uses_username(self):
        self.form.is_valid()
        telemetry = TestTelemetryAPIClient.__init__.call_args.args[0]
        self.assertEqual(telemetry.username, "hello@world.com")

    def test_uses_password(self):
        self.form.is_valid()
        telemetry = TestTelemetryAPIClient.__init__.call_args.args[0]
        self.assertEqual(telemetry.password, "topsecret")

    def test_uses_device_locator(self):
        self.form.is_valid()
        telemetry = TestTelemetryAPIClient.__init__.call_args.args[0]
        self.assertEqual(telemetry.device_locator, "http://1.2.3.4")

    def test_valid(self):
        TestTelemetryAPIClient.connect.side_effect = None
        self.assertTrue(self.form.is_valid())

    def test_invalid(self):
        TestTelemetryAPIClient.connect.side_effect = TelemetryError("hi")
        self.assertFalse(self.form.is_valid())

    def test_error_message(self):
        TestTelemetryAPIClient.connect.side_effect = TelemetryError("hi")
        self.assertEqual(self.form.errors["__all__"][0], "hi")

    def test_username_label_is_overriden(self):
        self.assertEqual(self.form.fields["username"].label, "Email")

    def test_password_label_is_overriden(self):
        self.assertEqual(self.form.fields["password"].label, "API key")

    def test_device_locator_label_is_overriden(self):
        self.assertEqual(self.form.fields["device_locator"].label, "URI")

    def test_device_locator_help_text_is_overriden(self):
        self.assertEqual(self.form.fields["device_locator"].help_text, "Do it!")


class ConnectionDataFormHideStuffTestCase(TestCase):
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        username = "hello@world.com"
        password = "topsecret"
        self.form_args = (
            {"username": username, "password": password, "device_locator": ""},
        )
        self.form_kwargs = {
            "driver": TestTelemetryAPIClient,
            "station": "irrelevant",
        }

    def setUp(self):
        self.saved_hide_device_locator = TestTelemetryAPIClient.hide_device_locator
        self.saved_hide_data_timezone = TestTelemetryAPIClient.hide_data_timezone

    def tearDown(self):
        TestTelemetryAPIClient.hide_data_timezone = self.saved_hide_data_timezone
        TestTelemetryAPIClient.hide_device_locator = self.saved_hide_device_locator

    def test_device_locator_hidden(self):
        TestTelemetryAPIClient.hide_device_locator = True
        form = ConnectionDataForm(*self.form_args, **self.form_kwargs)
        self.assertEqual(
            form.fields["device_locator"].widget.__class__.__name__, "HiddenInput"
        )

    def test_device_locator_not_hidden(self):
        TestTelemetryAPIClient.hide_device_locator = False
        form = ConnectionDataForm(*self.form_args, **self.form_kwargs)
        self.assertEqual(
            form.fields["device_locator"].widget.__class__.__name__, "TextInput"
        )

    def test_data_timezone_hidden(self):
        TestTelemetryAPIClient.hide_data_timezone = True
        form = ConnectionDataForm(*self.form_args, **self.form_kwargs)
        widget_class_name = form.fields["data_timezone"].widget.__class__.__name__
        self.assertEqual(widget_class_name, "HiddenInput")

    def test_data_timezone_hidden_value(self):
        TestTelemetryAPIClient.hide_data_timezone = True
        form = ConnectionDataForm(*self.form_args, **self.form_kwargs)
        self.assertEqual(form.fields["data_timezone"].widget.attrs["value"], "UTC")

    def test_data_timezone_not_hidden(self):
        TestTelemetryAPIClient.hide_data_timezone = False
        form = ConnectionDataForm(*self.form_args, **self.form_kwargs)
        widget_class_name = form.fields["data_timezone"].widget.__class__.__name__
        self.assertEqual(widget_class_name, "Select")


class ChooseStationFormTestCase(TestCase):
    def setUp(self):
        TestTelemetryAPIClient.reset_mocks()
        self._setup_mock_get_stations()
        self.form = ChooseStationForm(
            initial={
                "username": "hello@world.com",
                "password": "topsecretapikey",
                "device_locator": "http://1.2.3.4",
            },
            driver=TestTelemetryAPIClient,
            station="irrelevant",
        )

    def _setup_mock_get_stations(self):
        TestTelemetryAPIClient.get_stations.return_value = {
            "148A": "Hobbiton station",
            "149C": "Rivendell station",
        }

    def test_uses_username(self):
        telemetry = TestTelemetryAPIClient.__init__.call_args.args[0]
        self.assertEqual(telemetry.username, "hello@world.com")

    def test_uses_password(self):
        telemetry = TestTelemetryAPIClient.__init__.call_args.args[0]
        self.assertEqual(telemetry.password, "topsecretapikey")

    def test_uses_device_locator(self):
        telemetry = TestTelemetryAPIClient.__init__.call_args.args[0]
        self.assertEqual(telemetry.device_locator, "http://1.2.3.4")

    def test_calls_connect(self):
        self.form.is_valid()
        TestTelemetryAPIClient.connect.assert_called_once()

    def test_calls_disconnect(self):
        self.form.is_valid()
        TestTelemetryAPIClient.disconnect.assert_called_once()

    def test_populated_choices(self):
        self.assertEqual(
            self.form.fields["remote_station_id"].choices,
            [("148A", "Hobbiton station (148A)"), ("149C", "Rivendell station (149C)")],
        )


class ChooseSensorFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.station = baker.make(Station)
        cls.tsg1 = baker.make(TimeseriesGroup, gentity=cls.station, name="hello1")
        cls.tsg2 = baker.make(TimeseriesGroup, gentity=cls.station, name="hello2")
        cls.tsg3 = baker.make(TimeseriesGroup, gentity=cls.station, name="hello3")

    def setUp(self):
        TestTelemetryAPIClient.reset_mocks()
        self._setup_mock_get_sensors()
        self.form = ChooseSensorForm(
            initial={
                "username": "hello@world.com",
                "password": "topsecretapikey",
                "device_locator": "http://1.2.3.4",
                "station_id": self.station.id,
                "remote_station_id": "169C",
            },
            driver=TestTelemetryAPIClient,
            station=self.station,
        )

    def _setup_mock_get_sensors(self):
        TestTelemetryAPIClient.get_sensors.return_value = {
            "251": "Temperature sensor",
            "362": "Humidity sensor",
        }

    def test_calls_connect(self):
        self.form.is_valid()
        TestTelemetryAPIClient.connect.assert_called_once()

    def test_calls_disconnect(self):
        self.form.is_valid()
        TestTelemetryAPIClient.disconnect.assert_called_once()

    def test_uses_username(self):
        telemetry = TestTelemetryAPIClient.__init__.call_args.args[0]
        self.assertEqual(telemetry.username, "hello@world.com")

    def test_uses_password(self):
        telemetry = TestTelemetryAPIClient.__init__.call_args.args[0]
        self.assertEqual(telemetry.password, "topsecretapikey")

    def test_uses_device_locator(self):
        telemetry = TestTelemetryAPIClient.__init__.call_args.args[0]
        self.assertEqual(telemetry.device_locator, "http://1.2.3.4")

    def test_uses_appropriate_remote_station_id(self):
        telemetry = TestTelemetryAPIClient.__init__.call_args.args[0]
        self.assertEqual(telemetry.remote_station_id, "169C")

    def test_created_two_fields(self):
        self.assertEqual(len(self.form.fields), 2)

    def test_labels(self):
        self.assertEqual(
            self.form.fields["sensor_362"].label,
            "To which Enhydris time series does sensor "
            '"Humidity sensor" (362) correspond?',
        )

    def test_choices(self):
        self.assertEqual(
            self.form.fields["sensor_362"].choices,
            [
                ("", "Ignore this sensor"),
                (self.tsg1.id, f"hello1 ({self.tsg1.id})"),
                (self.tsg2.id, f"hello2 ({self.tsg2.id})"),
                (self.tsg3.id, f"hello3 ({self.tsg3.id})"),
            ],
        )

    def test_required(self):
        self.assertFalse(self.form.fields["sensor_362"].required)
