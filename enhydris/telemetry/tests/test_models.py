from django.core.exceptions import ValidationError
from django.test import TestCase

from freezegun import freeze_time
from model_mommy import mommy

from enhydris.models import Station
from enhydris.telemetry.models import Telemetry, fix_zone_name


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
