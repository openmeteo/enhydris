import datetime as dt
from io import StringIO
from unittest import mock
from zoneinfo import ZoneInfo

from django.core.cache import cache
from django.db import IntegrityError
from django.db.models.signals import post_save
from django.test import TestCase

import pandas as pd
import pytz
from htimeseries import HTimeseries
from model_bakery import baker

from enhydris import models
from enhydris.tests import ClearCacheMixin, TestTimeseriesMixin


def get_tzinfo(tzname):
    # We use pytz rather than zoneinfo here, because apparently pandas still
    # occasionally uses pytz, and in this case it has used pytz, and in some Python
    # versions the comparison of whether the two time zones are identical fails if
    # one is pytz and the other is zoneinfo, even if they are the same timezone.
    return pytz.timezone(tzname)


class TimeseriesTestCase(TestCase):
    def test_create(self):
        timeseries_group = baker.make(models.TimeseriesGroup)
        timeseries = models.Timeseries(
            type=models.Timeseries.AGGREGATED, timeseries_group=timeseries_group
        )
        timeseries.save()
        self.assertEqual(
            models.Timeseries.objects.first().type, models.Timeseries.AGGREGATED
        )

    def test_update(self):
        baker.make(models.Timeseries, type=models.Timeseries.INITIAL)
        timeseries = models.Timeseries.objects.first()
        timeseries.type = models.Timeseries.AGGREGATED
        timeseries.save()
        self.assertEqual(
            models.Timeseries.objects.first().type, models.Timeseries.AGGREGATED
        )

    def test_delete(self):
        baker.make(models.Timeseries)
        timeseries = models.Timeseries.objects.first()
        timeseries.delete()
        self.assertEqual(models.Timeseries.objects.count(), 0)

    def test_str_initial(self):
        self._test_str(type=models.Timeseries.INITIAL, result="Initial")

    def test_str_checked(self):
        self._test_str(type=models.Timeseries.CHECKED, result="Checked")

    def test_str_regularized(self):
        self._test_str(type=models.Timeseries.REGULARIZED, result="Regularized")

    def test_str_with_name(self):
        self._test_str(
            type=models.Timeseries.INITIAL,
            name="hello",
            result="Initial (hello)",
        )

    def test_str_aggregated(self):
        self._test_str(
            type=models.Timeseries.AGGREGATED,
            name="Mean",
            result="Aggregated (H Mean)",
        )

    def _make_timeseries(self, timeseries_group, type, name=""):
        return baker.make(
            models.Timeseries,
            timeseries_group=timeseries_group,
            type=type,
            time_step="H",
            name=name,
        )

    def _test_str(self, type, result, name=""):
        timeseries_group = baker.make(models.TimeseriesGroup, name="Temperature")
        timeseries = self._make_timeseries(timeseries_group, type, name=name)
        self.assertEqual(str(timeseries), result)

    def test_only_one_initial_per_group(self):
        timeseries_group = baker.make(models.TimeseriesGroup, name="Temperature")
        self._make_timeseries(timeseries_group, models.Timeseries.INITIAL)
        with self.assertRaises(IntegrityError):
            models.Timeseries(
                timeseries_group=timeseries_group,
                type=models.Timeseries.INITIAL,
                time_step="D",
            ).save()

    def test_only_one_checked_per_group(self):
        timeseries_group = baker.make(models.TimeseriesGroup, name="Temperature")
        self._make_timeseries(timeseries_group, models.Timeseries.CHECKED)
        with self.assertRaises(IntegrityError):
            models.Timeseries(
                timeseries_group=timeseries_group,
                type=models.Timeseries.CHECKED,
                time_step="D",
            ).save()

    def test_only_one_regularized_per_group(self):
        timeseries_group = baker.make(models.TimeseriesGroup, name="Temperature")
        self._make_timeseries(timeseries_group, models.Timeseries.REGULARIZED)
        with self.assertRaises(IntegrityError):
            models.Timeseries(
                timeseries_group=timeseries_group,
                type=models.Timeseries.REGULARIZED,
                time_step="D",
            ).save()

    def test_uniqueness(self):
        timeseries_group = baker.make(models.TimeseriesGroup, name="Temperature")
        self._make_timeseries(timeseries_group, models.Timeseries.AGGREGATED)
        with self.assertRaises(IntegrityError):
            models.Timeseries(
                timeseries_group=timeseries_group,
                type=models.Timeseries.AGGREGATED,
                time_step="H",
            ).save()

    def test_many_aggregated_per_group(self):
        timeseries_group = baker.make(models.TimeseriesGroup, name="Temperature")
        self._make_timeseries(timeseries_group, models.Timeseries.AGGREGATED)
        models.Timeseries(
            timeseries_group=timeseries_group,
            type=models.Timeseries.AGGREGATED,
            time_step="D",
        ).save()


def make_timeseries(*, start_date, end_date, **kwargs):
    """Make a test timeseries, setting start_date and end_date.
    This is essentially the same as baker.make(models.Timeseries, **kwargs), except
    that it also creates two records with the specified dates.
    """
    result = baker.make(models.Timeseries, **kwargs)
    result.timeseriesrecord_set.create(timestamp=start_date, value=0, flags="")
    result.timeseriesrecord_set.create(timestamp=end_date, value=0, flags="")
    return result


class TimeseriesDatesTestCase(ClearCacheMixin, TestCase):
    def setUp(self):
        self.timeseries = make_timeseries(
            timeseries_group__precision=2,
            start_date=dt.datetime(2018, 11, 15, 16, 0, tzinfo=dt.timezone.utc),
            end_date=dt.datetime(2018, 11, 17, 23, 0, tzinfo=dt.timezone.utc),
            timeseries_group__gentity__display_timezone="Etc/GMT-2",
        )

    def test_start_date(self):
        self.assertEqual(
            self.timeseries.start_date,
            dt.datetime(
                2018,
                11,
                15,
                18,
                0,
                tzinfo=ZoneInfo("Etc/GMT-2"),
            ),
        )

    def test_start_date_tzinfo(self):
        self.assertEqual(self.timeseries.start_date.tzinfo, ZoneInfo("Etc/GMT-2"))

    def test_start_date_cache(self):
        with self.assertNumQueries(1):
            self.timeseries.start_date

        timeseries = models.Timeseries.objects.get(id=self.timeseries.id)
        with self.assertNumQueries(0):
            timeseries.start_date

    def test_end_date(self):
        self.assertEqual(
            self.timeseries.end_date,
            dt.datetime(
                2018,
                11,
                18,
                1,
                0,
                tzinfo=ZoneInfo("Etc/GMT-2"),
            ),
        )

    def test_end_date_tzinfo(self):
        self.assertEqual(self.timeseries.end_date.tzinfo, ZoneInfo("Etc/GMT-2"))

    def test_end_date_cache(self):
        with self.assertNumQueries(1):
            self.timeseries.end_date

        timeseries = models.Timeseries.objects.get(id=self.timeseries.id)
        with self.assertNumQueries(0):
            timeseries.end_date


class DataTestCase(TestTimeseriesMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._create_test_timeseries("2017-11-23 17:23,1,\n2018-11-25 01:00,2,\n")
        tzinfo = get_tzinfo("Etc/GMT-2")
        cls.expected_result = pd.DataFrame(
            data={"value": [1.0, 2.0], "flags": ["", ""]},
            columns=["value", "flags"],
            index=[
                dt.datetime(2017, 11, 23, 17, 23, tzinfo=tzinfo),
                dt.datetime(2018, 11, 25, 1, 0, tzinfo=tzinfo),
            ],
        )
        cls.expected_result.index.name = "date"


class TimeseriesGetDataTestCase(DataTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.data = cls.timeseries.get_data()

    def test_abscissa(self):
        self.assertAlmostEqual(self.data.location["abscissa"], 245648.96, places=2)

    def test_ordinate(self):
        self.assertAlmostEqual(self.data.location["ordinate"], 4331165.20, places=2)

    def test_srid(self):
        self.assertAlmostEqual(self.data.location["srid"], 2100)

    def test_altitude(self):
        self.assertAlmostEqual(self.data.location["altitude"], 219)

    def test_time_step(self):
        self.assertEqual(self.data.time_step, "H")

    def test_unit(self):
        self.assertEqual(self.data.unit, "mm")

    def test_title(self):
        self.assertEqual(self.data.title, "Daily temperature")

    def test_timezone(self):
        self.assertEqual(self.data.timezone, "Etc/GMT-2 (UTC+0200)")

    def test_negative_timezone(self):
        self.timeseries.timeseries_group.gentity.display_timezone = "Etc/GMT+2"
        data = self.timeseries.get_data()
        self.assertEqual(data.timezone, "Etc/GMT+2 (UTC-0200)")

    def test_timezone_with_large_offset(self):
        self.timeseries.timeseries_group.gentity.display_timezone = "Etc/GMT-10"
        data = self.timeseries.get_data()
        self.assertEqual(data.timezone, "Etc/GMT-10 (UTC+1000)")

    def test_timezone_etc_gmt(self):
        self.timeseries.timeseries_group.gentity.display_timezone = "Etc/GMT"
        data = self.timeseries.get_data()
        self.assertEqual(data.timezone, "Etc/GMT (UTC+0000)")

    def test_timezone_utc(self):
        data = self.timeseries.get_data(timezone="UTC")
        self.assertEqual(data.timezone, "UTC (UTC+0000)")

    def test_variable(self):
        self.assertEqual(self.data.variable, "Temperature")

    def test_precision(self):
        self.assertEqual(self.data.precision, 1)

    def test_comment(self):
        self.assertEqual(self.data.comment, "Celduin\n\nThis timeseries group rocks")

    def test_location_is_none(self):
        self.timeseries.timeseries_group.gentity.geom = None
        data = self.timeseries.get_data()
        self.assertIsNone(data.location)

    def test_data(self):
        pd.testing.assert_frame_equal(self.data.data, self.expected_result)


class TimeseriesGetDataWithCloseTimestampsTestCase(DataTestCase):
    """Test get_data when two timestamps are within the same minute.

    While having successive timestamps within the same minute, such as 18:42:00 and
    18:42:10, is not yet fully supported, sometimes the database has such cases
    (primarily because of telemetric system bugs). We test that get_data can handle
    them.
    """

    def setUp(self):
        tzinfo = get_tzinfo("Etc/GMT")
        self.data = pd.DataFrame(
            data={"value": [1.0, 2.0], "flags": ["", ""]},
            columns=["value", "flags"],
            index=[
                dt.datetime(2024, 7, 17, 18, 42, 0, tzinfo=tzinfo),
                dt.datetime(2024, 7, 17, 18, 42, 10, tzinfo=tzinfo),
            ],
        )
        self.data.index.name = "date"
        self.timeseries.set_data(self.data)

    def test_get_data(self):
        data = self.timeseries.get_data(timezone="Etc/GMT")
        pd.testing.assert_frame_equal(data.data, self.data)


class TimeseriesGetDataInDifferentTimezoneTestCase(DataTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.data = cls.timeseries.get_data(timezone="Etc/GMT")

    def test_data(self):
        tzinfo = get_tzinfo("Etc/GMT")
        expected_result = pd.DataFrame(
            data={"value": [1.0, 2.0], "flags": ["", ""]},
            columns=["value", "flags"],
            index=[
                dt.datetime(2017, 11, 23, 15, 23, tzinfo=tzinfo),
                dt.datetime(2018, 11, 24, 23, 0, tzinfo=tzinfo),
            ],
        )
        expected_result.index.name = "date"
        pd.testing.assert_frame_equal(self.data.data, expected_result)

    def test_metadata(self):
        self.assertEqual(self.data.timezone, "Etc/GMT (UTC+0000)")


class TimeseriesGetDataWithNullTestCase(TestTimeseriesMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._create_test_timeseries("2017-11-23 17:23,,\n2018-11-25 01:00,2,\n")
        tzinfo = get_tzinfo("Etc/GMT-2")
        cls.expected_result = pd.DataFrame(
            data={"value": [float("NaN"), 2.0], "flags": ["", ""]},
            columns=["value", "flags"],
            index=[
                dt.datetime(2017, 11, 23, 17, 23, tzinfo=tzinfo),
                dt.datetime(2018, 11, 25, 1, 0, tzinfo=tzinfo),
            ],
        )
        cls.expected_result.index.name = "date"
        cls.data = cls.timeseries.get_data()

    def test_data(self):
        pd.testing.assert_frame_equal(self.data.data, self.expected_result)


class TimeseriesGetDataEmptyTestCase(TestTimeseriesMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._create_test_timeseries("")
        cls.data = cls.timeseries.get_data()

    def test_data(self):
        self.assertTrue(self.data.data.empty)


class TimeseriesGetDataWithStartAndEndDateTestCase(DataTestCase):
    def _check(self, start_index=None, end_index=None):
        """Check self.htimeseries.data against the initial timeseries sliced from
        start_index to end_index.
        """
        tzinfo = get_tzinfo("Etc/GMT-2")
        full_result = pd.DataFrame(
            data={"value": [1.0, 2.0], "flags": ["", ""]},
            columns=["value", "flags"],
            index=[
                dt.datetime(2017, 11, 23, 17, 23, tzinfo=tzinfo),
                dt.datetime(2018, 11, 25, 1, 0, tzinfo=tzinfo),
            ],
        )
        full_result.index.name = "date"
        expected_result = full_result.iloc[start_index:end_index]
        pd.testing.assert_frame_equal(self.ahtimeseries.data, expected_result)

    def test_with_start_date_just_before_start_of_timeseries(self):
        start_date = dt.datetime(2017, 11, 23, 17, 22, tzinfo=ZoneInfo("Etc/GMT-2"))
        self.ahtimeseries = self.timeseries.get_data(start_date=start_date)
        self._check()

    def test_with_start_date_on_start_of_timeseries(self):
        start_date = dt.datetime(2017, 11, 23, 17, 23, tzinfo=ZoneInfo("Etc/GMT-2"))
        self.ahtimeseries = self.timeseries.get_data(start_date=start_date)
        self._check()

    def test_with_start_date_just_after_start_of_timeseries(self):
        start_date = dt.datetime(2017, 11, 23, 17, 24, tzinfo=ZoneInfo("Etc/GMT-2"))
        self.ahtimeseries = self.timeseries.get_data(start_date=start_date)
        self._check(start_index=1)

    def test_with_end_date_just_after_end_of_timeseries(self):
        end_date = dt.datetime(2018, 11, 25, 1, 1, tzinfo=ZoneInfo("Etc/GMT-2"))
        self.ahtimeseries = self.timeseries.get_data(end_date=end_date)
        self._check()

    def test_with_end_date_on_end_of_timeseries(self):
        end_date = dt.datetime(2018, 11, 25, 1, 0, tzinfo=ZoneInfo("Etc/GMT-2"))
        self.ahtimeseries = self.timeseries.get_data(end_date=end_date)
        self._check()

    def test_with_end_date_just_before_end_of_timeseries(self):
        end_date = dt.datetime(2018, 11, 25, 0, 59, tzinfo=ZoneInfo("Etc/GMT-2"))
        self.ahtimeseries = self.timeseries.get_data(end_date=end_date)
        self._check(end_index=1)


class TimeseriesGetDataCacheTestCase(DataTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.original_expected_result = cls.expected_result

    def setUp(self):
        cache.clear()

        # Make sure we've accessed gpoint already, otherwise it screws up the number of
        # queries later
        self.timeseries.timeseries_group.gentity.gpoint.altitude

        # Ensure we've cached start_date and end_date
        self.timeseries.start_date
        self.timeseries.end_date

    def test_cache(self):
        self.expected_result = self.original_expected_result

        self._get_data_and_check_num_queries(1, start_date=None, end_date=None)
        self._get_data_and_check_num_queries(0, start_date=None, end_date=None)

        # Check cache invalidation
        self.timeseries.save()
        self._get_data_and_check_num_queries(1, start_date=None, end_date=None)

    def test_refetches_if_does_not_include_everything_from_start_date(self):
        start_date_1 = dt.datetime(2017, 12, 1, 1, 0, 0, tzinfo=dt.timezone.utc)
        self.expected_result = self.original_expected_result.iloc[1:]
        self._get_data_and_check_num_queries(1, start_date=start_date_1, end_date=None)

        start_date_2 = dt.datetime(2017, 11, 1, 1, 0, 0, tzinfo=dt.timezone.utc)
        self.expected_result = self.original_expected_result
        self._get_data_and_check_num_queries(1, start_date=start_date_2, end_date=None)

        # Try again with start_date_1; this time we should have everything in cache
        self.expected_result = self.original_expected_result.iloc[1:]
        self._get_data_and_check_num_queries(0, start_date=start_date_1, end_date=None)

    def test_refetches_if_does_not_include_everything_to_end_date(self):
        end_date_1 = dt.datetime(2018, 10, 1, 1, 0, 0, tzinfo=dt.timezone.utc)
        self.expected_result = self.original_expected_result.iloc[:-1]
        self._get_data_and_check_num_queries(1, start_date=None, end_date=end_date_1)

        end_date_2 = dt.datetime(2018, 12, 1, 1, 0, 0, tzinfo=dt.timezone.utc)
        self.expected_result = self.original_expected_result
        self._get_data_and_check_num_queries(1, start_date=None, end_date=end_date_2)

        # Try again with end_date_1; this time we should have everything in cache
        self.expected_result = self.original_expected_result.iloc[:-1]
        self._get_data_and_check_num_queries(0, start_date=None, end_date=end_date_1)

    def test_with_empty_data(self):
        empty = HTimeseries().data
        self.timeseries.set_data(empty)

        try:
            self.timeseries.get_data()  # This will cache the empty result
            self.timeseries.get_data()  # This should return the cached empty result
            # No further tests. We aren't so interested in whether it will use the
            # cached result but on whether it will show an error because of attempting
            # to make a comparison like start_date > some_value, where start_date is
            # None. Since we reached this point, it didn't attempt to do anything like
            # this.
        finally:
            self.timeseries.set_data(self.original_expected_result)

    def _get_data_and_check_num_queries(self, num_queries, *, start_date, end_date):
        with self.assertNumQueries(num_queries):
            data = self.timeseries.get_data(start_date=start_date, end_date=end_date)
        pd.testing.assert_frame_equal(data.data, self.expected_result)

    def test_cached_empty_dataframe(self):
        """Test the case where an empty dataframe was previously cached"""

        cache.clear()

        # Get (and thus cache) the time series, starting from a timestamp more recent
        # than the end date (that is, cache an empty dataframe).
        start_date = self.timeseries.end_date + dt.timedelta(minutes=1)
        self.timeseries.get_data(start_date=start_date)

        # Then ensure that getting the time series works
        data = self.timeseries.get_data(start_date=self.timeseries.end_date)
        self.assertEqual(len(data.data), 1)

    @mock.patch("enhydris.models.timeseries.Timeseries._invalidate_cached_data")
    def test_race_condition(self, m):
        # Populate cache
        self._get_data_and_check_num_queries(1, start_date=None, end_date=None)

        # Pretend there's a race condition. We delete the time series data, but
        # because we've mocked _invalidate_cached_data, the cache will not be deleted.
        # However, we manually delete the cached end date. This simulates the case
        # where another thread or process deletes the data (and invalidates the
        # cache) between examining the start date and end date.
        self.timeseries.set_data(HTimeseries())
        cache.delete(f"timeseries_end_date_{self.timeseries.id}")

        # Try getting the data again and see that it works. There are two queries now;
        # one is for the end date.
        with self.assertNumQueries(2):
            data = self.timeseries.get_data(start_date=None, end_date=None)
        self.assertEqual(len(data.data), 0)


class TimeseriesSetDataTestCase(TestTimeseriesMixin, TestCase):
    def setUp(self):
        self._create_test_timeseries()

    def test_call_with_file_object(self):
        self.returned_length = self.timeseries.set_data(
            StringIO("2017-11-23 17:23,1,\n" "2018-11-25 01:00,2,\n"),
            default_timezone="Etc/GMT-2",
        )
        self._check_results()

    def test_call_with_dataframe(self):
        self.returned_length = self.timeseries.set_data(self._get_dataframe())
        self._check_results()

    def test_call_with_htimeseries(self):
        self.returned_length = self.timeseries.set_data(
            HTimeseries(self._get_dataframe()), default_timezone="Etc/GMT-2"
        )
        self._check_results()

    def _get_dataframe(self):
        tzinfo = ZoneInfo("Etc/GMT-2")
        result = pd.DataFrame(
            data={"value": [1.0, 2.0], "flags": ["", ""]},
            columns=["value", "flags"],
            index=[
                dt.datetime(2017, 11, 23, 17, 23, tzinfo=tzinfo),
                dt.datetime(2018, 11, 25, 1, 0, tzinfo=tzinfo),
            ],
        )
        result.index.name = "date"
        return result

    def _check_results(self):
        tzinfo = ZoneInfo("Etc/GMT-2")
        self.assertEqual(self.returned_length, 2)
        self.assertEqual(
            list(self.timeseries.timeseriesrecord_set.values()),
            [
                {
                    "timeseries_id": self.timeseries.id,
                    "timestamp": dt.datetime(2017, 11, 23, 17, 23, tzinfo=tzinfo),
                    "value": 1.0,
                    "flags": "",
                },
                {
                    "timeseries_id": self.timeseries.id,
                    "timestamp": dt.datetime(2018, 11, 25, 1, 0, tzinfo=tzinfo),
                    "value": 2.0,
                    "flags": "",
                },
            ],
        )


class TimeseriesAppendDataTestCase(TestTimeseriesMixin, TestCase):
    def setUp(self):
        self._create_test_timeseries("2016-01-01 00:00,42,\n")

    def test_call_with_file_object(self):
        returned_length = self.timeseries.append_data(
            StringIO("2017-11-23 17:23,1,\n" "2018-11-25 01:00,2,\n"),
            default_timezone="Etc/GMT-2",
        )
        self.assertEqual(returned_length, 2)
        self._assert_wrote_data()

    def test_call_with_dataframe(self):
        returned_length = self.timeseries.append_data(
            self._get_dataframe(), default_timezone="Etc/GMT-2"
        )
        self.assertEqual(returned_length, 2)
        self._assert_wrote_data()

    def test_call_with_htimeseries(self):
        returned_length = self.timeseries.append_data(
            HTimeseries(self._get_dataframe()), default_timezone="Etc/GMT-2"
        )
        self.assertEqual(returned_length, 2)
        self._assert_wrote_data()

    def _get_dataframe(self):
        tzinfo = ZoneInfo("Etc/GMT-2")
        result = pd.DataFrame(
            data={"value": [1.0, 2.0], "flags": ["", ""]},
            columns=["value", "flags"],
            index=[
                dt.datetime(2017, 11, 23, 17, 23, tzinfo=tzinfo),
                dt.datetime(2018, 11, 25, 1, 0, tzinfo=tzinfo),
            ],
        )
        result.index.name = "date"
        return result

    def _assert_wrote_data(self):
        tzinfo = get_tzinfo("Etc/GMT-2")
        expected_result = pd.DataFrame(
            data={"value": [42.0, 1.0, 2.0], "flags": ["", "", ""]},
            columns=["value", "flags"],
            index=[
                dt.datetime(2016, 1, 1, 0, 0, tzinfo=tzinfo),
                dt.datetime(2017, 11, 23, 17, 23, tzinfo=tzinfo),
                dt.datetime(2018, 11, 25, 1, 0, tzinfo=tzinfo),
            ],
        )
        expected_result.index.name = "date"
        pd.testing.assert_frame_equal(self.timeseries.get_data().data, expected_result)


class TimeseriesAppendDataToEmptyTimeseriesTestCase(TestTimeseriesMixin, TestCase):
    def setUp(self):
        self._create_test_timeseries()

    def test_call_with_dataframe(self):
        returned_length = self.timeseries.append_data(
            self._get_dataframe(), default_timezone="Etc/GMT-2"
        )
        self.assertEqual(returned_length, 2)
        self._assert_wrote_data()

    def _get_dataframe(self):
        tzinfo = get_tzinfo("Etc/GMT-2")
        result = pd.DataFrame(
            data={"value": [1.0, 2.0], "flags": ["", ""]},
            columns=["value", "flags"],
            index=[
                dt.datetime(2017, 11, 23, 17, 23, tzinfo=tzinfo),
                dt.datetime(2018, 11, 25, 1, 0, tzinfo=tzinfo),
            ],
        )
        result.index.name = "date"
        return result

    def _assert_wrote_data(self):
        pd.testing.assert_frame_equal(
            self.timeseries.get_data().data, self._get_dataframe()
        )


class TimeseriesAppendErrorTestCase(TestTimeseriesMixin, TestCase):
    def test_does_not_update_if_data_to_append_are_not_later(self):
        self._create_test_timeseries("2018-01-01 00:00,42,\n")
        with self.assertRaises(IntegrityError):
            self.timeseries.append_data(
                StringIO("2017-11-23 17:23,1,\n2018-11-25 01:00,2,\n"),
                default_timezone="Etc/GMT-2",
            )


class TimeseriesGetLastRecordAsStringTestCase(TestTimeseriesMixin, TestCase):
    def test_when_record_exists(self):
        self._create_test_timeseries("2017-11-23 17:23,1,\n2018-11-25 01:00,2,\n")
        self.assertEqual(
            self.timeseries.get_last_record_as_string(), "2018-11-25 01:00,2.0,"
        )

    def test_when_record_does_not_exist(self):
        self._create_test_timeseries()
        self.assertEqual(self.timeseries.get_last_record_as_string(), "")

    def test_with_timezone(self):
        self._create_test_timeseries("2017-11-23 17:23,1,\n2018-11-25 01:00,2,\n")
        self.assertEqual(
            self.timeseries.get_last_record_as_string(timezone="Etc/GMT-5"),
            "2018-11-25 04:00,2.0,",
        )


class TimeseriesExecutesTriggersUponAddingRecordsTestCase(DataTestCase):
    def setUp(self):
        self.trigger = mock.MagicMock()
        post_save.connect(self.trigger, sender="enhydris.Timeseries")

    def tearDown(self):
        post_save.disconnect(self.trigger, sender="enhydris.Timeseries")

    def test_calls_trigger_upon_setting_data(self):
        self.timeseries.set_data(
            StringIO("2020-10-26 09:34,18,\n"), default_timezone="Etc/GMT-2"
        )
        self.trigger.assert_called()

    def test_calls_trigger_upon_appending_data(self):
        self.timeseries.append_data(
            StringIO("2020-10-26 09:34,18,\n"), default_timezone="Etc/GMT-2"
        )
        self.trigger.assert_called()


class TimeseriesRecordTestCase(TestTimeseriesMixin, TestCase):
    def test_str(self):
        self._create_test_timeseries("2017-11-23 17:23,3.14159,\n")
        record = models.TimeseriesRecord.objects.first()
        self.assertAlmostEqual(record.value, 3.14159)
        self.assertEqual(str(record), "2017-11-23 17:23,3.1,")

    def test_str_when_no_value(self):
        self._create_test_timeseries("2017-11-23 17:23,,\n")
        record = models.TimeseriesRecord.objects.first()
        record.save()
        self.assertEqual(str(record), "2017-11-23 17:23,,")

    def test_str_with_timezone(self):
        self._create_test_timeseries("2017-11-23 17:23,3.14,\n")
        record = models.TimeseriesRecord.objects.first()
        record.save()
        self.assertEqual(record.__str__(timezone="Etc/GMT-5"), "2017-11-23 20:23,3.1,")


class TimeseriesRecordBulkInsertTestCase(TestTimeseriesMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._create_test_timeseries()
        ahtimeseries = HTimeseries(
            StringIO("2020-09-08 20:00,15.7,,\n2020-09-08 21:00,,\n"),
            default_tzinfo=ZoneInfo("Etc/GMT-2"),
        )
        models.TimeseriesRecord.bulk_insert(cls.timeseries, ahtimeseries)
        cls.timeseries_records = models.TimeseriesRecord.objects.all()

    def test_first_value(self):
        self.assertAlmostEqual(self.timeseries_records[0].value, 15.7)

    def test_empty_value(self):
        self.assertIsNone(self.timeseries_records[1].value)


class TimeseriesDatesCacheInvalidationTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.station = baker.make(models.Station, name="Celduin")
        self.timeseries_group = baker.make(models.TimeseriesGroup, gentity=self.station)
        self.timeseries = baker.make(
            models.Timeseries,
            timeseries_group=self.timeseries_group,
            type=models.Timeseries.INITIAL,
        )

    def test_station_last_update_cache_invalidation(self):
        with self.assertNumQueries(2):
            self.station.last_update

        # Check cache invalidation
        self.timeseries.save()
        with self.assertNumQueries(2):
            self.station.last_update

    def test_timeseries_group_start_date_cache_invalidation(self):
        self.timeseries_group.default_timeseries
        with self.assertNumQueries(1):
            self.timeseries_group.start_date

        # Check cache invalidation
        self.timeseries.save()
        self.timeseries_group.default_timeseries
        with self.assertNumQueries(1):
            self.timeseries_group.start_date

    def test_timeseries_group_end_date_cache_invalidation(self):
        # Make sure to retrieve the `default_timeseries` first.
        self.timeseries_group.default_timeseries

        with self.assertNumQueries(1):
            self.timeseries_group.end_date

        # Check cache invalidation
        self.timeseries.save()
        self.timeseries_group.default_timeseries
        with self.assertNumQueries(1):
            self.timeseries_group.end_date

    def test_timeseries_start_date_cache_invalidation(self):
        with self.assertNumQueries(1):
            self.timeseries.start_date

        # Check cache invalidation
        self.timeseries.save()
        with self.assertNumQueries(1):
            self.timeseries.start_date

    def test_timeseries_end_date_cache_invalidation(self):
        with self.assertNumQueries(1):
            self.timeseries.end_date

        # Check cache invalidation
        self.timeseries.save()
        with self.assertNumQueries(1):
            self.timeseries.end_date
