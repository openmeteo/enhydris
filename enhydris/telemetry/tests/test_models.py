import datetime as dt
import errno
import json
import os
import subprocess
from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from freezegun import freeze_time
from model_mommy import mommy

import enhydris
from enhydris.models import Station, Timeseries, TimeseriesGroup
from enhydris.telemetry.models import Telemetry, TelemetryLogMessage, fix_zone_name


class TelemetryFetchValidatorsTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.telemetry = Telemetry(
            station=mommy.make(Station),
            type="meteoview2",
            fetch_interval_minutes=10,
            fetch_offset_minutes=10,
            fetch_offset_time_zone="Europe/Athens",
            additional_config="{}",
        )

    def setUp(self):
        self.telemetry.fetch_interval_minutes = 10
        self.telemetry.fetch_offset_minutes = 0

    def test_fetch_interval_minutes_cannot_be_less_than_10(self):
        self.telemetry.fetch_interval_minutes = 10
        self.telemetry.clean_fields()  # 10 is OK

        self.telemetry.fetch_interval_minutes = 9
        with self.assertRaises(ValidationError):
            self.telemetry.clean_fields()

    def test_fetch_interval_minutes_cannot_be_more_than_1440(self):
        self.telemetry.fetch_interval_minutes = 1440
        self.telemetry.clean_fields()  # 1440 is OK

        self.telemetry.fetch_interval_minutes = 1441
        with self.assertRaises(ValidationError):
            self.telemetry.clean_fields()

    def test_fetch_offset_minutes_cannot_be_negative(self):
        self.telemetry.fetch_offset_minutes = 0
        self.telemetry.clean_fields()  # 0 is OK

        self.telemetry.fetch_offset_minutes = -1
        with self.assertRaises(ValidationError):
            self.telemetry.clean_fields()

    def test_fetch_offset_minutes_cannot_be_more_than_1339(self):
        self.telemetry.fetch_offset_minutes = 1338
        self.telemetry.clean_fields()  # 1339 is OK

        self.telemetry.fetch_offset_minutes = 1440
        with self.assertRaises(ValidationError):
            self.telemetry.clean_fields()


class TelemetryIsDueTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.telemetry = Telemetry(
            station=mommy.make(Station),
            type="meteoview2",
            fetch_interval_minutes=10,
            fetch_offset_minutes=10,
            fetch_offset_time_zone="Europe/Athens",
            additional_config="{}",
        )

    def _check(self, fetch_interval_minutes, fetch_offset_minutes, expected_result):
        self.telemetry.fetch_interval_minutes = fetch_interval_minutes
        self.telemetry.fetch_offset_minutes = fetch_offset_minutes
        self.assertEqual(self.telemetry.is_due, expected_result)

    @freeze_time("2021-11-30 02:05", tz_offset=0)
    def test_not_due(self):
        self._check(1440, 125, False)

    @freeze_time("2021-11-30 00:05", tz_offset=0)
    def test_is_due_1(self):
        self._check(1440, 125, True)

    @freeze_time("2021-11-30 00:05", tz_offset=0)
    def test_is_due_2(self):
        self._check(120, 5, True)

    @freeze_time("2021-11-30 22:05", tz_offset=0)
    def test_is_due_3(self):
        self._check(120, 5, True)


class FixZoneNameTestCase(TestCase):
    def test_gmt_plus(self):
        self.assertEqual(fix_zone_name("Etc/GMT+200"), "UTC-200")

    def test_gmt_minus(self):
        self.assertEqual(fix_zone_name("Etc/GMT-300"), "UTC+300")

    def test_other(self):
        self.assertEqual(fix_zone_name("EEST"), "EEST")


class TelemetryFetchTestCaseBase(TestCase):
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
            Telemetry,
            station=cls.station,
            type="meteoview2",
            data_time_zone="Europe/Athens",
            fetch_interval_minutes=10,
            fetch_offset_minutes=2,
            fetch_offset_time_zone="Asia/Vladivostok",
            username="someemail@email.com",
            password="topsecret",
            remote_station_id="42a",
            additional_config={},
        )
        cls.telemetry.sensor_set.create(
            sensor_id="257", timeseries_group=cls.timeseries_group
        )


class TelemetryFetchTestCase(TelemetryFetchTestCaseBase):
    # We could mock a TelemetryAPIClient here, but we choose to create a lower level
    # mock object, i.e. requests.request, and use an unmocked meteoview2 api client.
    # However, the functionality we check here is of models.py and not of the
    # meteoview2 api client, which is presumed to work correctly (and the specifics
    # of which are tested elsewhere).

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


class TelemetryFetchIgnoresTimeZoneTestCase(TelemetryFetchTestCaseBase):
    """Test that timeseries_end_date is always naive

    When records already exist in the timeseries before calling fetch(), the
    timeseries_end_date specified in get_measurement() is determined from the
    latest of these records. However, storage of timestamps in the database is
    always aware, so we need to convert it to naive before calling
    get_measurement(). This TestCases checks that this is done.

    Unfortunately, at the time of this writing, if this test fails, the error
    message is not easy to understand, because fetch() catches all exceptions and
    records them in the TelemetryLog.  So while debugging things related to this
    test it's a good idea to temporarily modify fetch() to raise exceptions.
    """

    def setUp(self):
        timeseries = Timeseries(
            timeseries_group_id=self.timeseries_group.id, type=Timeseries.INITIAL
        )
        timeseries.save()
        timeseries.append_data(StringIO("2022-06-14 08:00,42.1,\n"))

    @patch("enhydris.telemetry.types.meteoview2.requests.request")
    def test_ignores_time_zone(self, mock_request):
        self._set_mock_request_return_values(mock_request)
        self.telemetry.fetch()
        self.assertEqual(
            mock_request.call_args.kwargs,
            {
                "headers": {
                    "content-type": "application/json",
                    "Authorization": "Bearer topsecretapitoken",
                },
                "data": json.dumps(
                    {
                        "sensor": ["257"],
                        "datefrom": "2022-06-14",
                        "timefrom": "08:01",
                        "dateto": "2022-12-11",
                    }
                ),
            },
        )

    def _set_mock_request_return_values(self, mock_request):
        mock_request.side_effect = [
            MagicMock(  # Response for login
                **{"json.return_value": {"code": "200", "token": "topsecretapitoken"}}
            ),
            MagicMock(  # Response for measurements
                **{"json.return_value": "irrelevant"}
            ),
        ]


@patch("enhydris.telemetry.types.meteoview2.requests.request")
class TelemetryFetchDealsWithTooCloseTimestampsTestCase(TelemetryFetchTestCaseBase):
    """Test successive timestamps less than one minute apart

    Enhydris can't handle the case where two timestamps differ in seconds
    only; therefore if such a thing happens we ignore the second timestamp.

    Unfortunately, at the time of this writing, if this test fails, the error
    message is not easy to understand, because fetch() catches all exceptions and
    records them in the TelemetryLog.  So while debugging things related to this
    test it's a good idea to temporarily modify fetch() to raise exceptions.
    """

    def test_return_value(self, mock_request):
        self._set_request_result(mock_request)
        self.telemetry.fetch()
        result = StringIO()
        self.timeseries_group.default_timeseries.get_data().write(result)
        self.assertEqual(
            result.getvalue(),
            "2021-12-14 08:10,1.4,\r\n" "2021-12-14 08:20,1.4,\r\n",
        )

    def _set_request_result(self, mock_request):
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
                    }
                }
            ),
        ]


class TelemetryLogMessageTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.telemetry = mommy.make(Telemetry, additional_config={})

    def setUp(self):
        try:
            raise OSError(errno.ECONNRESET, "Connection reset")
        except ConnectionResetError:
            self.approx_error_time = dt.datetime.utcnow()
            TelemetryLogMessage.log(self.telemetry)

    def test_logged_one_record(self):
        self.assertEqual(TelemetryLogMessage.objects.count(), 1)

    def test_telemetry(self):
        self.assertEqual(
            TelemetryLogMessage.objects.first().telemetry_id, self.telemetry.id
        )

    def test_exception_name(self):
        self.assertEqual(
            TelemetryLogMessage.objects.first().exception_name, "ConnectionResetError"
        )

    def test_message(self):
        self.assertEqual(
            TelemetryLogMessage.objects.first().message,
            "[Errno 104] Connection reset",
        )

    def test_traceback(self):
        self.assertIn(__file__, TelemetryLogMessage.objects.first().traceback)

    def test_enhydris_version(self):
        self.assertEqual(
            TelemetryLogMessage.objects.first().enhydris_version, enhydris.__version__
        )

    def test_git_commit_id(self):
        actual_commit_id = (
            subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True)
            .stdout.decode()
            .strip()
        )
        self.assertEqual(
            TelemetryLogMessage.objects.first().enhydris_commit_id, actual_commit_id
        )

    def test_ordering(self):
        lm1 = TelemetryLogMessage.objects.first()
        lm1.timestamp = dt.datetime(1994, 1, 1, 0, 0, tzinfo=dt.timezone.utc)
        lm1.save()
        lm2 = TelemetryLogMessage.objects.create(
            telemetry=self.telemetry,
            message="hello",
            exception_name="Error",
            traceback="",
            enhydris_version="",
        )
        lm2.timestamp = dt.datetime(1995, 1, 1, 0, 0, tzinfo=dt.timezone.utc)
        lm2.save()

        # That last log message must come first because it has a later date
        self.assertEqual(TelemetryLogMessage.objects.first().message, "hello")

    def test_get_full_message(self):
        isotime = self.approx_error_time.isoformat(sep=" ", timespec="seconds")
        self.assertEqual(
            TelemetryLogMessage.objects.first().get_full_message(),
            f"{isotime} ConnectionResetError: [Errno 104] Connection reset",
        )

    def test_get_full_version_with_commit_id_present(self):
        obj = TelemetryLogMessage()
        obj.enhydris_version = "15.16.17"
        obj.enhydris_commit_id = "1234567890abcdef"
        self.assertEqual(obj.get_full_version(), "15.16.17 (1234567890)")

    def test_get_full_version_with_commit_id_absent(self):
        obj = TelemetryLogMessage()
        obj.enhydris_version = "15.16.17"
        obj.enhydris_commit_id = ""
        self.assertEqual(obj.get_full_version(), "15.16.17")


class TelemetryLogMessageGetEnhydrisCommitIdFromGitTestCase(TestCase):
    def setUp(self):
        self.saved_cwd = os.getcwd()
        try:
            del TelemetryLogMessage._saved_commit_id
        except AttributeError:
            pass

    def tearDown(self):
        os.chdir(self.saved_cwd)

    def test_returns_git_commit_id(self):
        actual_commit_id = (
            subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True)
            .stdout.decode()
            .strip()
        )
        os.chdir("/tmp")  # Don't assume we're in the Enhydris directory
        self.assertEqual(
            TelemetryLogMessage.get_enhydris_commit_id_from_git(), actual_commit_id
        )

    @patch("subprocess.run", side_effect=FileNotFoundError("foo"))
    def test_returns_empty_git_commit_on_problem(self, m):
        self.assertEqual(TelemetryLogMessage.get_enhydris_commit_id_from_git(), "")

    @patch("subprocess.run")
    def test_caches_git_commit_id(self, m):
        m.return_value.stdout.decode.return_value.strip.return_value = "hello"
        self.assertEqual(TelemetryLogMessage.get_enhydris_commit_id_from_git(), "hello")
        self.assertEqual(TelemetryLogMessage.get_enhydris_commit_id_from_git(), "hello")
        m.assert_called_once()

    @patch("subprocess.run", side_effect=FileNotFoundError("foo"))
    def test_caches_empty_git_commit_id(self, m):
        self.assertEqual(TelemetryLogMessage.get_enhydris_commit_id_from_git(), "")
        self.assertEqual(TelemetryLogMessage.get_enhydris_commit_id_from_git(), "")
        m.assert_called_once()


class TelemetryFetchErrorTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.telemetry = mommy.make(Telemetry, type="meteoview2", additional_config={})

    @patch("enhydris.telemetry.models.Telemetry._setup_api_client")
    def test_logs_error_on_fetch_error(self, m):
        m.side_effect = KeyError("foo")
        self.telemetry.fetch()
        self.assertEqual(TelemetryLogMessage.objects.count(), 1)
