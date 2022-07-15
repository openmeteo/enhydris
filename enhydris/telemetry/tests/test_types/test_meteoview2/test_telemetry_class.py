import json
from io import StringIO
from unittest.mock import MagicMock, patch

from django.test import TestCase

from model_mommy import mommy

from enhydris.models import Station, Timeseries, TimeseriesGroup
from enhydris.telemetry.models import Telemetry as TelemetryModel
from enhydris.telemetry.types.meteoview2 import Telemetry


class TelemetryAttributesTestCase(TestCase):
    def test_name(self):
        self.assertEqual(Telemetry.name, "Metrica MeteoView2")

    def test_wizard_steps(self):
        self.assertEqual(len(Telemetry.wizard_steps), 3)


class FetchTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.station = mommy.make(Station)
        cls.timeseries_group = mommy.make(
            TimeseriesGroup,
            id=42,
            gentity=cls.station,
            variable__descr="Temperature",
            time_zone__code="EET",
            time_zone__utc_offset=200,
            precision=1,
        )
        cls.telemetry = mommy.make(
            TelemetryModel,
            station=cls.station,
            type="meteoview2",
            data_time_zone="Europe/Athens",
            fetch_interval_minutes=10,
            fetch_offset_minutes=2,
            fetch_offset_time_zone="Asia/Vladivostok",
            configuration={
                "station_id": cls.station.id,
                "email": "someemail@email.com",
                "api_key": "topsecret",
                "sensor_257": "42",
                "sensor_258": None,  # This ensures it will not try to fetch it
            },
        )

    def setUp(self):
        self.mock_request = self._get_mock_request()
        self.telemetry.fetch()

    def _get_mock_request(self):
        patcher = patch("enhydris.telemetry.types.meteoview2.requests.request")
        mock_request = patcher.start()
        self.addCleanup(patcher.stop)
        mock_request.side_effect = [
            MagicMock(  # Response for login
                **{"json.return_value": {"code": "200", "token": "topsecretapitoken"}}
            ),
            MagicMock(  # Response for measurements
                **{
                    "json.return_value": {
                        "code": "200",
                        "measurements": [
                            {
                                "total_values": 1,
                                "values": [
                                    {
                                        "year": "1990",
                                        "month": "0",
                                        "day": "1",
                                        "hour": "0",
                                        "minute": "0",
                                        "mvalue": "42",
                                    }
                                ],
                            }
                        ],
                    }
                }
            ),
        ]
        return mock_request

    def test_logs_on(self):
        login_request = self.mock_request.mock_calls[0]
        self.assertEqual(
            login_request.args, ("POST", "https://meteoview2.gr/api/token")
        )
        self.assertEqual(
            login_request.kwargs,
            {
                "headers": {"content-type": "application/json"},
                "data": json.dumps(
                    {"email": "someemail@email.com", "key": "topsecret"}
                ),
            },
        )

    def test_fetches_sensor_257(self):
        fetch_request = self.mock_request.mock_calls[1]
        self.assertEqual(
            fetch_request.args, ("POST", "https://meteoview2.gr/api/measurements")
        )
        self.assertEqual(
            fetch_request.kwargs["data"],
            json.dumps(
                {
                    "sensor": ["257"],
                    "datefrom": "1990-01-01",
                    "timefrom": "00:00",
                    "dateto": "1990-06-30",
                }
            ),
        )

    def test_appends_data_to_database(self):
        timeseries = Timeseries.objects.get(
            timeseries_group=self.timeseries_group, type=Timeseries.INITIAL
        )
        data = StringIO()
        timeseries.get_data().write(data)
        self.assertEqual(data.getvalue().strip(), "1990-01-01 00:00,42.0,")
