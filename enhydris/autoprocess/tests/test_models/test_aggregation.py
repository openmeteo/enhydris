import datetime as dt
from unittest import mock

from django.db import IntegrityError
from django.test import TestCase

import numpy as np
import pandas as pd
from haggregate import RegularizationMode as RM
from htimeseries import HTimeseries
from model_bakery import baker

from enhydris.autoprocess.models import Aggregation
from enhydris.models import Station, Timeseries, TimeseriesGroup, Variable


class AggregationTestCase(TestCase):
    def setUp(self):
        self.station = baker.make(Station)
        variable = baker.make(Variable, descr="Irrelevant")
        self.timeseries_group = baker.make(
            TimeseriesGroup, gentity=self.station, variable=variable
        )

    def test_create(self):
        aggregation = Aggregation(
            timeseries_group=self.timeseries_group, method="sum", max_missing=0
        )
        aggregation.save()
        self.assertEqual(Aggregation.objects.count(), 1)

    def _baker_make_aggregation(self, method="sum"):
        return baker.make(
            Aggregation,
            timeseries_group=self.timeseries_group,
            target_time_step="1h",
            method=method,
        )

    def test_update(self):
        self._baker_make_aggregation()
        aggregation = Aggregation.objects.first()
        aggregation.method = "max"
        aggregation.save()
        self.assertEqual(aggregation.method, "max")

    def test_delete(self):
        self._baker_make_aggregation()
        aggregation = Aggregation.objects.first()
        aggregation.delete()
        self.assertEqual(Aggregation.objects.count(), 0)

    def test_str(self):
        aggregation = self._baker_make_aggregation()
        self.assertEqual(
            str(aggregation), "Aggregation for {}".format(self.timeseries_group)
        )

    def test_no_extra_queries_for_str(self):
        self._baker_make_aggregation()
        with self.assertNumQueries(1):
            str(Aggregation.objects.first())

    def test_wrong_resulting_timestamp_offset_1(self):
        aggregation = self._baker_make_aggregation()
        aggregation.resulting_timestamp_offset = "hello"
        with self.assertRaises(IntegrityError):
            aggregation.save()

    def test_wrong_resulting_timestamp_offset_2(self):
        aggregation = self._baker_make_aggregation()
        aggregation.resulting_timestamp_offset = "-"
        with self.assertRaises(IntegrityError):
            aggregation.save()

    def test_wrong_resulting_timestamp_offset_3(self):
        aggregation = self._baker_make_aggregation()
        aggregation.resulting_timestamp_offset = "15"
        with self.assertRaises(IntegrityError):
            aggregation.save()

    def test_wrong_resulting_timestamp_offset_4(self):
        aggregation = self._baker_make_aggregation()
        aggregation.resulting_timestamp_offset = "-min"
        with self.assertRaises(IntegrityError):
            aggregation.save()

    def test_positive_time_step_without_number(self):
        aggregation = self._baker_make_aggregation()
        aggregation.resulting_timestamp_offset = "min"
        aggregation.save()

    def test_positive_time_step_with_number(self):
        aggregation = self._baker_make_aggregation()
        aggregation.resulting_timestamp_offset = "15min"
        aggregation.save()

    def test_negative_time_step(self):
        aggregation = self._baker_make_aggregation()
        aggregation.resulting_timestamp_offset = "-1min"
        aggregation.save()

    def test_source_timeseries_when_initial_already_exists(self):
        self._make_timeseries(id=42, type=Timeseries.INITIAL)
        self._make_timeseries(id=41, type=Timeseries.AGGREGATED)
        aggregation = baker.make(
            Aggregation, timeseries_group=self.timeseries_group, target_time_step="1h"
        )
        self.assertEqual(aggregation.source_timeseries.id, 42)

    def _make_timeseries(self, id, type, name=""):
        return baker.make(
            Timeseries,
            id=id,
            timeseries_group=self.timeseries_group,
            type=type,
            time_step="1h",
            name=name,
        )

    def test_automatically_creates_source_timeseries(self):
        aggregation = baker.make(
            Aggregation, timeseries_group=self.timeseries_group, target_time_step="1h"
        )
        self.assertFalse(Timeseries.objects.exists())
        aggregation.source_timeseries.id
        self.assertTrue(Timeseries.objects.exists())

    def test_target_timeseries(self):
        self._make_timeseries(id=42, type=Timeseries.INITIAL)
        self._make_timeseries(id=41, type=Timeseries.AGGREGATED, name="Mean")
        aggregation = baker.make(
            Aggregation,
            timeseries_group=self.timeseries_group,
            target_time_step="1h",
            method="mean",
        )
        self.assertEqual(aggregation.target_timeseries.id, 41)

    def test_automatically_creates_target_timeseries(self):
        aggregation = self._baker_make_aggregation()
        self.assertFalse(Timeseries.objects.exists())
        aggregation.target_timeseries.id
        self.assertTrue(Timeseries.objects.exists())

    def test_creates_different_timeseries_for_different_methods(self):
        aggregation1 = self._baker_make_aggregation(method="mean")
        aggregation2 = self._baker_make_aggregation(method="max")
        self.assertFalse(Timeseries.objects.exists())
        aggregation1.target_timeseries.id
        self.assertEqual(Timeseries.objects.count(), 2)
        aggregation2.target_timeseries.id
        self.assertEqual(Timeseries.objects.count(), 3)
        names = {x.name for x in Timeseries.objects.filter(type=Timeseries.AGGREGATED)}
        self.assertEqual(names, {"Mean", "Max"})

    def test_checks_target_time_step(self):
        aggregation = Aggregation(
            timeseries_group=self.timeseries_group, target_time_step="1a"
        )
        with self.assertRaisesRegex(ValueError, '"1a" is not a valid time step'):
            aggregation.save()


class AggregationProcessTimeseriesTestCase(TestCase):
    _index = [
        dt.datetime(2019, 5, 21, 10, 00, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 10, 10, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 10, 21, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 10, 31, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 10, 40, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 10, 50, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 11, 00, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 11, 10, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 11, 20, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 11, 30, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 11, 40, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 11, 50, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 12, 00, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 12, 10, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 12, 20, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 12, 30, tzinfo=dt.timezone.utc),
        dt.datetime(2019, 5, 21, 12, 40, tzinfo=dt.timezone.utc),
    ]
    _values = [2, 3, 5, 7, 11, 13, 17, 19, np.nan, 29, 31, 37, 41, 43, 47, 53, 59]

    source_timeseries = pd.DataFrame(
        data={"value": _values, "flags": 17 * [""]},
        columns=["value", "flags"],
        index=_index,
    )

    expected_result_for_max_missing_zero = pd.DataFrame(
        data={"value": [56.0], "flags": [""]},
        columns=["value", "flags"],
        index=[dt.datetime(2019, 5, 21, 10, 59, tzinfo=dt.timezone.utc)],
    )

    expected_result_for_max_missing_one = pd.DataFrame(
        data={"value": [56.0, 157.0], "flags": ["", "MISS"]},
        columns=["value", "flags"],
        index=[
            dt.datetime(2019, 5, 21, 10, 59, tzinfo=dt.timezone.utc),
            dt.datetime(2019, 5, 21, 11, 59, tzinfo=dt.timezone.utc),
        ],
    )

    expected_result_for_max_missing_five = pd.DataFrame(
        data={"value": [2.0, 56.0, 157.0], "flags": ["MISS", "", "MISS"]},
        columns=["value", "flags"],
        index=[
            dt.datetime(2019, 5, 21, 9, 59, tzinfo=dt.timezone.utc),
            dt.datetime(2019, 5, 21, 10, 59, tzinfo=dt.timezone.utc),
            dt.datetime(2019, 5, 21, 11, 59, tzinfo=dt.timezone.utc),
        ],
    )

    def _execute(self, max_missing):
        station = baker.make(Station)
        self.aggregation = baker.make(
            Aggregation,
            timeseries_group__gentity=station,
            timeseries_group__variable__descr="Hello",
            target_time_step="1h",
            method="sum",
            max_missing=max_missing,
            resulting_timestamp_offset="1min",
        )
        self.aggregation._htimeseries = HTimeseries(self.source_timeseries)
        self.aggregation._htimeseries.time_step = "10min"
        return self.aggregation.process_timeseries().data

    def test_execute_for_max_missing_zero(self):
        result = self._execute(max_missing=0)
        self.assert_frame_equal(result, self.expected_result_for_max_missing_zero)

    def test_execute_for_max_missing_one(self):
        result = self._execute(max_missing=1)
        self.assert_frame_equal(result, self.expected_result_for_max_missing_one)

    def test_execute_for_max_missing_five(self):
        result = self._execute(max_missing=5)
        self.assert_frame_equal(result, self.expected_result_for_max_missing_five)

    def test_execute_when_target_timeseries_is_already_complete(self):
        self._execute(max_missing=5)
        # Now the target time series is complete. Executing a second time should do
        # nothing. (We need to get the aggregation from the db rather than using
        # self.aggregation, to ensure aggregation.htimeseries is created anew.)
        aggregation = Aggregation.objects.first()
        result = aggregation.process_timeseries().data
        self.assertTrue(result.empty)

    def test_execute_for_max_missing_too_high(self):
        result = self._execute(max_missing=10000)
        self.assert_frame_equal(result, self.expected_result_for_max_missing_five)

    def assert_frame_equal(self, result, expected_result):
        """Check that DataFrames are equal, ignoring index name and frequency.

        Sometimes the result's index name is "date", sometimes it's empty. Sometimes the
        result's index frequency is "h", sometimes it's None. It must be due to
        different dependency versions. Since the index name and frequency aren't what
        we're trying to test here, we just ignore them.
        """
        expected_result.index.name = result.index.name
        expected_result.index.freq = result.index.freq
        pd.testing.assert_frame_equal(result, expected_result)


class AggregationProcessTimeseriesWhenNoTimeStepTestCase(TestCase):
    """Check what's done when the source time series has no time step.

    We can't regularize (and therefore aggregate) unless the source time series has a
    time step. We check that in such a case we behave gracefully.
    """

    @classmethod
    def setUpTestData(cls):
        station = baker.make(Station)
        timeseries_group = baker.make(
            TimeseriesGroup, gentity=station, variable__descr="hello"
        )
        cls.aggregation = baker.make(
            Aggregation,
            timeseries_group=timeseries_group,
            target_time_step="1h",
            method="sum",
            max_missing=3,
            resulting_timestamp_offset="",
        )

    def setUp(self):
        source_timeseries = pd.DataFrame(
            data={"value": [42], "flags": [""]},
            columns=["value", "flags"],
            index=[dt.datetime(2019, 5, 21, 11, 20, tzinfo=dt.timezone.utc)],
        )
        self.aggregation._htimeseries = HTimeseries(source_timeseries)
        self.aggregation._htimeseries.time_step = ""

    @mock.patch("enhydris.autoprocess.models.logging")
    def test_no_exception(self, logging_mock):
        self.aggregation.process_timeseries()
        logging_mock.getLogger.return_value.error.assert_called_once_with(
            "The time step is malformed or is specified in months. Only time steps "
            "specified in minutes, hours or days are supported."
        )


@mock.patch("enhydris.autoprocess.models.Aggregation._aggregate_time_series")
@mock.patch("enhydris.autoprocess.models.regularize")
class AggregationRegularizationModeTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        station = baker.make(Station)
        timeseries_group = baker.make(
            TimeseriesGroup, gentity=station, variable__descr="hello"
        )
        cls.aggregation = baker.make(
            Aggregation,
            timeseries_group=timeseries_group,
            target_time_step="1h",
            method="sum",
            max_missing=3,
            resulting_timestamp_offset="",
        )
        source_timeseries = pd.DataFrame(
            data={"value": [42], "flags": [""]},
            columns=["value", "flags"],
            index=[dt.datetime(2019, 5, 21, 11, 20, tzinfo=dt.timezone.utc)],
        )
        cls.aggregation._htimeseries = HTimeseries(source_timeseries)
        cls.aggregation._htimeseries.time_step = "10min"

    def test_sum(self, mock_regularize, mock_haggregate):
        self.aggregation.method = "sum"
        self.aggregation.process_timeseries()
        self.assertEqual(mock_regularize.call_args.kwargs["mode"], RM.INTERVAL)

    def test_mean(self, mock_regularize, mock_haggregate):
        self.aggregation.method = "mean"
        self.aggregation.process_timeseries()
        self.assertEqual(mock_regularize.call_args.kwargs["mode"], RM.INSTANTANEOUS)

    def test_min(self, mock_regularize, mock_haggregate):
        self.aggregation.method = "min"
        self.aggregation.process_timeseries()
        self.assertEqual(mock_regularize.call_args.kwargs["mode"], RM.INTERVAL)

    def test_max(self, mock_regularize, mock_haggregate):
        self.aggregation.method = "max"
        self.aggregation.process_timeseries()
        self.assertEqual(mock_regularize.call_args.kwargs["mode"], RM.INTERVAL)
