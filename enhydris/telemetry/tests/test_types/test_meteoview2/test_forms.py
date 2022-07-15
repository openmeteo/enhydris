import json
from unittest.mock import MagicMock, patch

from django.test import TestCase

import requests
from model_mommy import mommy

from enhydris.models import Station, TimeseriesGroup
from enhydris.telemetry.types.meteoview2 import (
    ChooseSensorForm,
    ChooseStationForm,
    LoginDataForm,
)


@patch("enhydris.telemetry.types.meteoview2.requests.request")
class LoginDataFormTestCase(TestCase):
    def setUp(self):
        email = "hello@world.com"
        api_key = "topsecretkey"
        self.form = LoginDataForm({"email": email, "api_key": api_key})

    def test_makes_request(self, mock_request):
        self.form.is_valid()
        mock_request.assert_called_once_with(
            "POST",
            "https://meteoview2.gr/api/token",
            headers={"content-type": "application/json"},
            data=json.dumps({"email": "hello@world.com", "key": "topsecretkey"}),
        )

    def test_valid(self, mock_request):
        mock_request.return_value.json.return_value = {
            "code": "200",
            "token": "topsecretapitoken",
        }
        self.assertTrue(self.form.is_valid())

    def test_invalid(self, mock_request):
        mock_request.return_value.raise_for_status.side_effect = (
            requests.RequestException("hello")
        )
        self.assertFalse(self.form.is_valid())

    def test_error_message(self, mock_request):
        mock_request.return_value.raise_for_status.side_effect = (
            requests.RequestException("hello")
        )
        self.assertEqual(
            self.form.errors["__all__"][0],
            "Could not login to meteoview; the error was: hello",
        )


class ChooseStationFormTestCase(TestCase):
    def setUp(self):
        self.mock_request = self._get_mock_request()
        self.form = ChooseStationForm(
            initial={"email": "hello@world.com", "api_key": "topsecretapikey"}
        )

    def _get_mock_request(self):
        patcher = patch("enhydris.telemetry.types.meteoview2.requests.request")
        mock_request = patcher.start()
        self.addCleanup(patcher.stop)
        mock_request.side_effect = [
            MagicMock(  # Response for login()
                **{"json.return_value": {"code": "200", "token": "topsecretapitoken"}}
            ),
            MagicMock(  # Response for get_stations()
                **{
                    "json.return_value": {
                        "code": "200",
                        "stations": {
                            "hobbiton": {"code": "148A", "title": "Hobbiton station"},
                            "rivendell": {"code": "149C", "title": "Rivendell station"},
                        },
                    }
                }
            ),
        ]
        return mock_request

    def test_made_two_requests(self):
        self.assertEqual(self.mock_request.call_count, 2)

    def test_populated_choices(self):
        self.assertEqual(
            self.form.fields["station"].choices,
            [("148A", "Hobbiton station (148A)"), ("149C", "Rivendell station (149C)")],
        )


class ChooseSensorFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.station = mommy.make(Station)
        cls.tsg1 = mommy.make(TimeseriesGroup, gentity=cls.station, name="hello1")
        cls.tsg2 = mommy.make(TimeseriesGroup, gentity=cls.station, name="hello2")
        cls.tsg3 = mommy.make(TimeseriesGroup, gentity=cls.station, name="hello3")

    def setUp(self):
        self.mock_request = self._get_mock_request()
        self.form = ChooseSensorForm(
            initial={
                "email": "hello@world.com",
                "api_key": "topsecretapikey",
                "station_id": self.station.id,
                "station": "169C",
            }
        )

    def _get_mock_request(self):
        patcher = patch("enhydris.telemetry.types.meteoview2.requests.request")
        mock_request = patcher.start()
        self.addCleanup(patcher.stop)
        mock_request.side_effect = [
            MagicMock(  # Response for login()
                **{"json.return_value": {"code": "200", "token": "topsecretapitoken"}}
            ),
            MagicMock(  # Response for get_sensors()
                **{
                    "json.return_value": {
                        "code": "200",
                        "sensors": [
                            {"id": "251", "title": "Temperature sensor"},
                            {"id": "362", "title": "Humidity sensor"},
                        ],
                    }
                }
            ),
        ]
        return mock_request

    def test_made_two_requests(self):
        self.assertEqual(self.mock_request.call_count, 2)

    def test_requested_sensors_for_appropriate_station_code(self):
        self.mock_request.assert_called_with(
            "POST",
            "https://meteoview2.gr/api/sensors",
            headers={
                "content-type": "application/json",
                "Authorization": "Bearer topsecretapitoken",
            },
            data=json.dumps({"station_code": "169C"}),
        )

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
