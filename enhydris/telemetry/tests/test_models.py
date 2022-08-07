import datetime as dt
import errno
import os
import subprocess
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from freezegun import freeze_time
from model_mommy import mommy

import enhydris
from enhydris.models import Station
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
            configuration="{}",
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
            configuration="{}",
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


class TelemetryLogMessageTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.telemetry = mommy.make(Telemetry, configuration={})

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
        cls.telemetry = mommy.make(Telemetry, type="meteoview2", configuration={})

    @patch("enhydris.telemetry.types.meteoview2.Telemetry.fetch")
    def test_logs_error_on_fetch_error(self, m):
        m.side_effect = KeyError("foo")
        self.telemetry.fetch()
        self.assertEqual(TelemetryLogMessage.objects.count(), 1)
