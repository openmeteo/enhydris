import datetime as dt
from unittest import mock

from django.db import DataError
from django.test import TestCase

import numpy as np
import pandas as pd
from htimeseries import HTimeseries
from model_bakery import baker
from rocc import Threshold

from enhydris.autoprocess.models import (
    Checks,
    RangeCheck,
    RateOfChangeCheck,
    RateOfChangeThreshold,
)
from enhydris.models import Station, Timeseries, TimeseriesGroup


class ChecksTestCase(TestCase):
    def test_create(self):
        timeseries_group = baker.make(TimeseriesGroup)
        checks = Checks(timeseries_group=timeseries_group)
        checks.save()
        self.assertEqual(Checks.objects.count(), 1)

    def test_update(self):
        timeseries_group1 = baker.make(TimeseriesGroup, id=42)
        timeseries_group2 = baker.make(TimeseriesGroup, id=43)
        checks = baker.make(Checks, timeseries_group=timeseries_group1)
        checks.timeseries_group = timeseries_group2
        checks.save()
        self.assertEqual(Checks.objects.first().timeseries_group.id, 43)

    def test_delete(self):
        checks = baker.make(Checks)
        checks.delete()
        self.assertEqual(Checks.objects.count(), 0)

    def test_str(self):
        checks = baker.make(Checks, timeseries_group__name="Temperature")
        self.assertEqual(str(checks), "Checks for Temperature")

    def test_source_timeseries(self):
        self.timeseries_group = baker.make(TimeseriesGroup)
        self._make_timeseries(id=42, type=Timeseries.INITIAL)
        self._make_timeseries(id=41, type=Timeseries.CHECKED)
        checks = baker.make(Checks, timeseries_group=self.timeseries_group)
        self.assertEqual(checks.source_timeseries.id, 42)

    def _make_timeseries(self, id, type):
        return baker.make(
            Timeseries, id=id, timeseries_group=self.timeseries_group, type=type
        )

    def test_automatically_creates_source_timeseries(self):
        timeseries_group = baker.make(TimeseriesGroup)
        checks = baker.make(Checks, timeseries_group=timeseries_group)
        self.assertFalse(Timeseries.objects.exists())
        checks.source_timeseries.id
        self.assertTrue(Timeseries.objects.exists())

    def test_target_timeseries(self):
        self.timeseries_group = baker.make(TimeseriesGroup)
        self._make_timeseries(id=42, type=Timeseries.INITIAL)
        self._make_timeseries(id=41, type=Timeseries.CHECKED)
        checks = baker.make(Checks, timeseries_group=self.timeseries_group)
        self.assertEqual(checks.target_timeseries.id, 41)

    def test_automatically_creates_target_timeseries(self):
        timeseries_group = baker.make(TimeseriesGroup)
        checks = baker.make(Checks, timeseries_group=timeseries_group)
        self.assertFalse(Timeseries.objects.exists())
        checks.target_timeseries.id
        self.assertTrue(Timeseries.objects.exists())

    @mock.patch("enhydris.autoprocess.models.RangeCheck.check_timeseries")
    @mock.patch("enhydris.models.Timeseries.append_data")
    def test_runs_range_check(self, m1, m2):
        station = baker.make(Station, display_timezone="Etc/GMT")
        range_check = baker.make(
            RangeCheck,
            checks__timeseries_group__gentity=station,
            checks__timeseries_group__variable__descr="Temperature",
        )
        range_check.checks.execute()
        m2.assert_called_once()

    def test_no_extra_queries_for_str(self):
        baker.make(Checks, timeseries_group__variable__descr="Temperature")
        with self.assertNumQueries(1):
            str(Checks.objects.first())


class ChecksAutoDeletionTestCase(TestCase):
    def setUp(self):
        self.checks = baker.make(Checks, timeseries_group__variable__descr="pH")
        self.range_check = baker.make(RangeCheck, checks=self.checks)
        self.roc_check = baker.make(RateOfChangeCheck, checks=self.checks)

    def test_checks_is_not_deleted_if_range_check_is_deleted(self):
        self.range_check.delete()
        self.assertTrue(Checks.objects.exists())

    def test_checks_is_not_deleted_if_roc_check_is_deleted(self):
        self.roc_check.delete()
        self.assertTrue(Checks.objects.exists())

    def test_checks_is_deleted_if_both_checks_are_deleted_with_roc_last(self):
        self.range_check.delete()
        self.roc_check.delete()
        self.assertFalse(Checks.objects.exists())

    def test_checks_is_deleted_if_both_checks_are_deleted_with_range_last(self):
        self.roc_check.delete()
        self.range_check.delete()
        self.assertFalse(Checks.objects.exists())


class RangeCheckTestCase(TestCase):
    def _baker_make_range_check(self):
        return baker.make(
            RangeCheck, checks__timeseries_group__name="pH", upper_bound=55.0
        )

    def test_create(self):
        checks = baker.make(Checks)
        range_check = RangeCheck(checks=checks, upper_bound=42.7, lower_bound=-5.2)
        range_check.save()
        self.assertEqual(RangeCheck.objects.count(), 1)

    def test_update(self):
        self._baker_make_range_check()
        range_check = RangeCheck.objects.first()
        range_check.upper_bound = 1831.7
        range_check.save()
        self.assertAlmostEqual(range_check.upper_bound, 1831.7)

    def test_delete(self):
        self._baker_make_range_check()
        range_check = RangeCheck.objects.first()
        range_check.delete()
        self.assertEqual(RangeCheck.objects.count(), 0)

    def test_str(self):
        range_check = self._baker_make_range_check()
        self.assertEqual(str(range_check), "Range check for pH")

    def test_no_extra_queries_for_str(self):
        self._baker_make_range_check()
        with self.assertNumQueries(1):
            str(RangeCheck.objects.first())


class RangeCheckProcessTimeseriesTestCase(TestCase):
    _index = [
        dt.datetime(2019, 5, 21, 10, 20, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 10, 30, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 10, 40, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 10, 50, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 11, 00, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 11, 10, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 11, 20, tzinfo=dt.timezone.utc),
    ]

    source_timeseries = pd.DataFrame(
        data={
            "value": [1.5, 2.9, 3.1, np.nan, 3.8, 4.9, 7.2],
            "flags": ["", "", "", "", "FLAG1", "FLAG2", "FLAG3"],
        },
        columns=["value", "flags"],
        index=_index,
    )

    expected_result = pd.DataFrame(
        data={
            "value": [np.nan, 2.9, 3.1, np.nan, 3.8, 4.9, np.nan],
            "flags": [
                "RANGE",
                "SUSPECT",
                "",
                "",
                "FLAG1",
                "FLAG2 SUSPECT",
                "FLAG3 RANGE",
            ],
        },
        columns=["value", "flags"],
        index=_index,
    )

    def test_execute(self):
        self.range_check = baker.make(
            RangeCheck,
            lower_bound=2,
            upper_bound=5,
            soft_lower_bound=3,
            soft_upper_bound=4,
        )
        self.range_check.checks._htimeseries = HTimeseries(self.source_timeseries)
        result = self.range_check.checks.process_timeseries()
        pd.testing.assert_frame_equal(result, self.expected_result)


class RateOfChangeCheckTestCase(TestCase):
    def _baker_make_rate_of_change_check(self):
        return baker.make(
            RateOfChangeCheck, checks__timeseries_group__name="pH", symmetric=True
        )

    def test_create_roc_check(self):
        checks = baker.make(Checks)
        roc_check = RateOfChangeCheck(checks=checks, symmetric=True)
        roc_check.save()
        self.assertEqual(RateOfChangeCheck.objects.count(), 1)

    def test_create_thresholds(self):
        roc_check = self._baker_make_rate_of_change_check()
        threshold = RateOfChangeThreshold(
            rate_of_change_check=roc_check, delta_t="10min", allowed_diff=25.0
        )
        threshold.save()
        self.assertEqual(RateOfChangeThreshold.objects.count(), 1)

    def test_raises_data_error_if_invalid_delta_t(self):
        roc_check = self._baker_make_rate_of_change_check()
        threshold = RateOfChangeThreshold(
            rate_of_change_check=roc_check, delta_t="garbag", allowed_diff=25.0
        )
        msg = '"garbag" is not a valid delta_t'
        with self.assertRaisesRegex(DataError, msg):
            threshold.save()

    def test_garbage_delta_t_is_invalid(self):
        self.assertFalse(RateOfChangeThreshold.is_delta_t_valid("garbge"))

    def test_zero_delta_t_is_invalid(self):
        self.assertFalse(RateOfChangeThreshold.is_delta_t_valid("0min"))

    def test_delta_t_with_invalid_unit_of_measurement_is_invalid(self):
        self.assertFalse(RateOfChangeThreshold.is_delta_t_valid("2garbg"))

    def test_delta_t_with_minutes(self):
        self.assertTrue(RateOfChangeThreshold.is_delta_t_valid("1min"))

    def test_delta_t_with_hours(self):
        self.assertTrue(RateOfChangeThreshold.is_delta_t_valid("2h"))

    def test_delta_t_with_days(self):
        self.assertTrue(RateOfChangeThreshold.is_delta_t_valid("3D"))

    def test_str(self):
        roc_check = self._baker_make_rate_of_change_check()
        self.assertEqual(str(roc_check), "Time consistency check for pH")

    def test_no_extra_queries_for_str(self):
        self._baker_make_rate_of_change_check()
        with self.assertNumQueries(1):
            str(RateOfChangeCheck.objects.first())


class RateOfChangeCheckThresholdsTestCase(TestCase):
    def setUp(self):
        self.rocc = baker.make(
            RateOfChangeCheck, checks__timeseries_group__name="pH", symmetric=True
        )

    def test_get_thresholds_as_text(self):
        baker.make(
            RateOfChangeThreshold,
            rate_of_change_check=self.rocc,
            delta_t="10min",
            allowed_diff=25.0,
        )
        baker.make(
            RateOfChangeThreshold,
            rate_of_change_check=self.rocc,
            delta_t="1h",
            allowed_diff=35.0,
        )
        self.assertEqual(self.rocc.get_thresholds_as_text(), "10min\t25.0\n1h\t35.0\n")

    def test_set_thresholds(self):
        self.rocc.set_thresholds("10min\t25.0\n1h\t35.0\n")
        self.assertEqual(
            self.rocc.thresholds, [Threshold("10min", 25.0), Threshold("1h", 35.0)]
        )

    def test_set_thresholds_when_some_already_exist(self):
        self.rocc.set_thresholds("5min\t25.0\n2h\t35.0\n")
        self.rocc.set_thresholds("10min\t25.0\n1h\t35.0\n")
        self.assertEqual(
            self.rocc.thresholds, [Threshold("10min", 25.0), Threshold("1h", 35.0)]
        )


class RateOfChangeCheckProcessTimeseriesTestCase(TestCase):
    _index = [
        dt.datetime(2019, 5, 21, 10, 20, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 10, 30, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 10, 40, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 10, 50, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 11, 00, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 11, 10, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 11, 20, tzinfo=dt.timezone.utc),
    ]

    source_timeseries = pd.DataFrame(
        data={
            "value": [1.5, 8.9, 3.1, np.nan, 3.8, 11.9, 7.2],
            "flags": ["", "", "", "", "FLAG1", "FLAG2", "FLAG3"],
        },
        columns=["value", "flags"],
        index=_index,
    )

    expected_result = pd.DataFrame(
        data={
            "value": [1.5, np.nan, 3.1, np.nan, 3.8, np.nan, 7.2],
            "flags": ["", "TEMPORAL", "", "", "FLAG1", "FLAG2 TEMPORAL", "FLAG3"],
        },
        columns=["value", "flags"],
        index=_index,
    )

    def test_execute(self):
        self.roc_check = baker.make(RateOfChangeCheck)
        baker.make(
            RateOfChangeThreshold,
            rate_of_change_check=self.roc_check,
            delta_t="10min",
            allowed_diff=7.0,
        )
        self.roc_check.checks._htimeseries = HTimeseries(self.source_timeseries)
        result = self.roc_check.checks.process_timeseries()
        pd.testing.assert_frame_equal(result, self.expected_result)
