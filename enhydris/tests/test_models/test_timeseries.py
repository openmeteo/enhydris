import datetime as dt
from io import StringIO
from unittest import mock

from django.core.cache import cache
from django.db import IntegrityError
from django.db.models.signals import post_save
from django.test import TestCase

import pandas as pd
from htimeseries import HTimeseries
from model_mommy import mommy

from enhydris import models
from enhydris.tests import ClearCacheMixin, TestTimeseriesMixin


class TimeseriesTestCase(TestCase):
    def test_create(self):
        timeseries_group = mommy.make(models.TimeseriesGroup)
        timeseries = models.Timeseries(
            type=models.Timeseries.AGGREGATED, timeseries_group=timeseries_group
        )
        timeseries.save()
        self.assertEqual(
            models.Timeseries.objects.first().type, models.Timeseries.AGGREGATED
        )

    def test_update(self):
        mommy.make(models.Timeseries, type=models.Timeseries.INITIAL)
        timeseries = models.Timeseries.objects.first()
        timeseries.type = models.Timeseries.AGGREGATED
        timeseries.save()
        self.assertEqual(
            models.Timeseries.objects.first().type, models.Timeseries.AGGREGATED
        )

    def test_delete(self):
        mommy.make(models.Timeseries)
        timeseries = models.Timeseries.objects.first()
        timeseries.delete()
        self.assertEqual(models.Timeseries.objects.count(), 0)

    def test_str_initial(self):
        self._test_str(type=models.Timeseries.INITIAL, result="Initial")

    def test_str_checked(self):
        self._test_str(type=models.Timeseries.CHECKED, result="Checked")

    def test_str_regularized(self):
        self._test_str(type=models.Timeseries.REGULARIZED, result="Regularized")

    def test_str_aggregated(self):
        self._test_str(type=models.Timeseries.AGGREGATED, result="Aggregated (H)")

    def _make_timeseries(self, timeseries_group, type):
        return mommy.make(
            models.Timeseries,
            timeseries_group=timeseries_group,
            type=type,
            time_step="H",
        )

    def _test_str(self, type, result):
        timeseries_group = mommy.make(models.TimeseriesGroup, name="Temperature")
        timeseries = self._make_timeseries(timeseries_group, type)
        self.assertEqual(str(timeseries), result)

    def test_only_one_initial_per_group(self):
        timeseries_group = mommy.make(models.TimeseriesGroup, name="Temperature")
        self._make_timeseries(timeseries_group, models.Timeseries.INITIAL)
        with self.assertRaises(IntegrityError):
            models.Timeseries(
                timeseries_group=timeseries_group,
                type=models.Timeseries.INITIAL,
                time_step="D",
            ).save()

    def test_only_one_checked_per_group(self):
        timeseries_group = mommy.make(models.TimeseriesGroup, name="Temperature")
        self._make_timeseries(timeseries_group, models.Timeseries.CHECKED)
        with self.assertRaises(IntegrityError):
            models.Timeseries(
                timeseries_group=timeseries_group,
                type=models.Timeseries.CHECKED,
                time_step="D",
            ).save()

    def test_only_one_regularized_per_group(self):
        timeseries_group = mommy.make(models.TimeseriesGroup, name="Temperature")
        self._make_timeseries(timeseries_group, models.Timeseries.REGULARIZED)
        with self.assertRaises(IntegrityError):
            models.Timeseries(
                timeseries_group=timeseries_group,
                type=models.Timeseries.REGULARIZED,
                time_step="D",
            ).save()

    def test_uniqueness(self):
        timeseries_group = mommy.make(models.TimeseriesGroup, name="Temperature")
        self._make_timeseries(timeseries_group, models.Timeseries.AGGREGATED)
        with self.assertRaises(IntegrityError):
            models.Timeseries(
                timeseries_group=timeseries_group,
                type=models.Timeseries.AGGREGATED,
                time_step="H",
            ).save()

    def test_many_aggregated_per_group(self):
        timeseries_group = mommy.make(models.TimeseriesGroup, name="Temperature")
        self._make_timeseries(timeseries_group, models.Timeseries.AGGREGATED)
        models.Timeseries(
            timeseries_group=timeseries_group,
            type=models.Timeseries.AGGREGATED,
            time_step="D",
        ).save()


def make_timeseries(*, start_date, end_date, **kwargs):
    """Make a test timeseries, setting start_date and end_date.
    This is essentially the same as mommy.make(models.Timeseries, **kwargs), except
    that it also creates two records with the specified dates.
    """
    result = mommy.make(models.Timeseries, **kwargs)
    result.timeseriesrecord_set.create(timestamp=start_date, value=0, flags="")
    result.timeseriesrecord_set.create(timestamp=end_date, value=0, flags="")
    return result


class TimeseriesDatesTestCase(ClearCacheMixin, TestCase):
    def setUp(self):
        self.timeseries = make_timeseries(
            timeseries_group__time_zone__utc_offset=120,
            timeseries_group__precision=2,
            start_date=dt.datetime(2018, 11, 15, 16, 0, tzinfo=dt.timezone.utc),
            end_date=dt.datetime(2018, 11, 17, 23, 0, tzinfo=dt.timezone.utc),
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
                tzinfo=self.timeseries.timeseries_group.time_zone.as_tzinfo,
            ),
        )

    def test_start_date_tzinfo(self):
        self.assertEqual(
            self.timeseries.start_date.tzinfo,
            self.timeseries.timeseries_group.time_zone.as_tzinfo,
        )

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
                tzinfo=self.timeseries.timeseries_group.time_zone.as_tzinfo,
            ),
        )

    def test_end_date_tzinfo(self):
        self.assertEqual(
            self.timeseries.end_date.tzinfo,
            self.timeseries.timeseries_group.time_zone.as_tzinfo,
        )

    def test_end_date_cache(self):
        with self.assertNumQueries(1):
            self.timeseries.end_date

        timeseries = models.Timeseries.objects.get(id=self.timeseries.id)
        with self.assertNumQueries(0):
            timeseries.end_date

    def test_start_date_naive(self):
        self.assertEqual(
            self.timeseries.start_date_naive, dt.datetime(2018, 11, 15, 18, 0)
        )

    def test_start_date_naive_cache(self):
        with self.assertNumQueries(1):
            self.timeseries.start_date_naive

        timeseries = models.Timeseries.objects.get(id=self.timeseries.id)
        with self.assertNumQueries(0):
            timeseries.start_date_naive

    def test_end_date_naive(self):
        self.assertEqual(
            self.timeseries.end_date_naive, dt.datetime(2018, 11, 18, 1, 0)
        )

    def test_end_date_naive_cache(self):
        with self.assertNumQueries(1):
            self.timeseries.end_date_naive

        timeseries = models.Timeseries.objects.get(id=self.timeseries.id)
        with self.assertNumQueries(0):
            timeseries.end_date_naive


class DataTestCase(TestTimeseriesMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._create_test_timeseries("2017-11-23 17:23,1,\n2018-11-25 01:00,2,\n")
        cls.expected_result = pd.DataFrame(
            data={"value": [1.0, 2.0], "flags": ["", ""]},
            columns=["value", "flags"],
            index=[dt.datetime(2017, 11, 23, 17, 23), dt.datetime(2018, 11, 25, 1, 0)],
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
        self.assertEqual(self.data.timezone, "IST (UTC+0530)")

    def test_negative_timezone(self):
        self.timeseries.timeseries_group.time_zone.code = "NST"
        self.timeseries.timeseries_group.time_zone.utc_offset = -210
        data = self.timeseries.get_data()
        self.assertEqual(data.timezone, "NST (UTC-0330)")

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


class TimeseriesGetDataWithNullTestCase(TestTimeseriesMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._create_test_timeseries("2017-11-23 17:23,,\n2018-11-25 01:00,2,\n")
        cls.expected_result = pd.DataFrame(
            data={"value": [float("NaN"), 2.0], "flags": ["", ""]},
            columns=["value", "flags"],
            index=[dt.datetime(2017, 11, 23, 17, 23), dt.datetime(2018, 11, 25, 1, 0)],
        )
        cls.expected_result.index.name = "date"
        cls.data = cls.timeseries.get_data()

    def test_data(self):
        pd.testing.assert_frame_equal(self.data.data, self.expected_result)


class TimeseriesGetDataWithStartAndEndDateTestCase(DataTestCase):
    def _check(self, start_index=None, end_index=None):
        """Check self.htimeseries.data against the initial timeseries sliced from
        start_index to end_index.
        """
        full_result = pd.DataFrame(
            data={"value": [1.0, 2.0], "flags": ["", ""]},
            columns=["value", "flags"],
            index=[dt.datetime(2017, 11, 23, 17, 23), dt.datetime(2018, 11, 25, 1, 0)],
        )
        full_result.index.name = "date"
        expected_result = full_result.iloc[start_index:end_index]
        pd.testing.assert_frame_equal(self.ahtimeseries.data, expected_result)

    def test_with_start_date_just_before_start_of_timeseries(self):
        tzinfo = self.timeseries.timeseries_group.time_zone.as_tzinfo
        start_date = dt.datetime(2017, 11, 23, 17, 22, tzinfo=tzinfo)
        self.ahtimeseries = self.timeseries.get_data(start_date=start_date)
        self._check()

    def test_with_start_date_on_start_of_timeseries(self):
        tzinfo = self.timeseries.timeseries_group.time_zone.as_tzinfo
        start_date = dt.datetime(2017, 11, 23, 17, 23, tzinfo=tzinfo)
        self.ahtimeseries = self.timeseries.get_data(start_date=start_date)
        self._check()

    def test_with_start_date_just_after_start_of_timeseries(self):
        tzinfo = self.timeseries.timeseries_group.time_zone.as_tzinfo
        start_date = dt.datetime(2017, 11, 23, 17, 24, tzinfo=tzinfo)
        self.ahtimeseries = self.timeseries.get_data(start_date=start_date)
        self._check(start_index=1)

    def test_with_end_date_just_after_end_of_timeseries(self):
        tzinfo = self.timeseries.timeseries_group.time_zone.as_tzinfo
        end_date = dt.datetime(2018, 11, 25, 1, 1, tzinfo=tzinfo)
        self.ahtimeseries = self.timeseries.get_data(end_date=end_date)
        self._check()

    def test_with_end_date_on_end_of_timeseries(self):
        tzinfo = self.timeseries.timeseries_group.time_zone.as_tzinfo
        end_date = dt.datetime(2018, 11, 25, 1, 0, tzinfo=tzinfo)
        self.ahtimeseries = self.timeseries.get_data(end_date=end_date)
        self._check()

    def test_with_end_date_just_before_end_of_timeseries(self):
        tzinfo = self.timeseries.timeseries_group.time_zone.as_tzinfo
        end_date = dt.datetime(2018, 11, 25, 0, 59, tzinfo=tzinfo)
        self.ahtimeseries = self.timeseries.get_data(end_date=end_date)
        self._check(end_index=1)


class TimeseriesGetDataCacheTestCase(DataTestCase):
    def test_cache(self):
        # Make sure we've accessed gpoint already, otherwise it screws up the number of
        # queries later
        self.timeseries.timeseries_group.gentity.gpoint.altitude

        self._get_data_and_check_num_queries(1)
        self._get_data_and_check_num_queries(0)

        # Check cache invalidation
        self.timeseries.save()
        self._get_data_and_check_num_queries(1)

    def _get_data_and_check_num_queries(self, num_queries):
        with self.assertNumQueries(num_queries):
            data = self.timeseries.get_data()
        pd.testing.assert_frame_equal(data.data, self.expected_result)


class TimeseriesSetDataTestCase(TestTimeseriesMixin, TestCase):
    def setUp(self):
        self._create_test_timeseries()

    def test_call_with_file_object(self):
        self.returned_length = self.timeseries.set_data(
            StringIO("2017-11-23 17:23,1,\n" "2018-11-25 01:00,2,\n")
        )
        self._check_results()

    def test_call_with_dataframe(self):
        self.returned_length = self.timeseries.set_data(self._get_dataframe())
        self._check_results()

    def test_call_with_htimeseries(self):
        self.returned_length = self.timeseries.set_data(
            HTimeseries(self._get_dataframe())
        )
        self._check_results()

    def _get_dataframe(self):
        result = pd.DataFrame(
            data={"value": [1.0, 2.0], "flags": ["", ""]},
            columns=["value", "flags"],
            index=[dt.datetime(2017, 11, 23, 17, 23), dt.datetime(2018, 11, 25, 1, 0)],
        )
        result.index.name = "date"
        return result

    def _check_results(self):
        self.assertEqual(self.returned_length, 2)
        self.assertEqual(
            list(self.timeseries.timeseriesrecord_set.values()),
            [
                {
                    "timeseries_id": self.timeseries.id,
                    "timestamp": dt.datetime(
                        2017,
                        11,
                        23,
                        17,
                        23,
                        tzinfo=models.TimeZone(code="IST", utc_offset=330).as_tzinfo,
                    ),
                    "value": 1.0,
                    "flags": "",
                },
                {
                    "timeseries_id": self.timeseries.id,
                    "timestamp": dt.datetime(
                        2018,
                        11,
                        25,
                        1,
                        0,
                        tzinfo=models.TimeZone(code="IST", utc_offset=330).as_tzinfo,
                    ),
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
            StringIO("2017-11-23 17:23,1,\n" "2018-11-25 01:00,2,\n")
        )
        self.assertEqual(returned_length, 2)
        self._assert_wrote_data()

    def test_call_with_dataframe(self):
        returned_length = self.timeseries.append_data(self._get_dataframe())
        self.assertEqual(returned_length, 2)
        self._assert_wrote_data()

    def test_call_with_htimeseries(self):
        returned_length = self.timeseries.append_data(
            HTimeseries(self._get_dataframe())
        )
        self.assertEqual(returned_length, 2)
        self._assert_wrote_data()

    def _get_dataframe(self):
        result = pd.DataFrame(
            data={"value": [1.0, 2.0], "flags": ["", ""]},
            columns=["value", "flags"],
            index=[dt.datetime(2017, 11, 23, 17, 23), dt.datetime(2018, 11, 25, 1, 0)],
        )
        result.index.name = "date"
        return result

    def _assert_wrote_data(self):
        expected_result = pd.DataFrame(
            data={"value": [42.0, 1.0, 2.0], "flags": ["", "", ""]},
            columns=["value", "flags"],
            index=[
                dt.datetime(2016, 1, 1, 0, 0),
                dt.datetime(2017, 11, 23, 17, 23),
                dt.datetime(2018, 11, 25, 1, 0),
            ],
        )
        expected_result.index.name = "date"
        pd.testing.assert_frame_equal(self.timeseries.get_data().data, expected_result)


class TimeseriesAppendDataToEmptyTimeseriesTestCase(TestTimeseriesMixin, TestCase):
    def setUp(self):
        self._create_test_timeseries()

    def test_call_with_dataframe(self):
        returned_length = self.timeseries.append_data(self._get_dataframe())
        self.assertEqual(returned_length, 2)
        self._assert_wrote_data()

    def _get_dataframe(self):
        result = pd.DataFrame(
            data={"value": [1.0, 2.0], "flags": ["", ""]},
            columns=["value", "flags"],
            index=[dt.datetime(2017, 11, 23, 17, 23), dt.datetime(2018, 11, 25, 1, 0)],
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
                StringIO("2017-11-23 17:23,1,\n2018-11-25 01:00,2,\n")
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


class TimeseriesExecutesTriggersUponAddingRecordsTestCase(DataTestCase):
    def setUp(self):
        self.trigger = mock.MagicMock()
        post_save.connect(self.trigger, sender="enhydris.Timeseries")

    def tearDown(self):
        post_save.disconnect(self.trigger, sender="enhydris.Timeseries")

    def test_calls_trigger_upon_setting_data(self):
        self.timeseries.set_data(StringIO("2020-10-26 09:34,18,\n"))
        self.trigger.assert_called()

    def test_calls_trigger_upon_appending_data(self):
        self.timeseries.append_data(StringIO("2020-10-26 09:34,18,\n"))
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


class TimeseriesRecordBulkInsertTestCase(TestTimeseriesMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._create_test_timeseries()
        ahtimeseries = HTimeseries(
            StringIO("2020-09-08 20:00,15.7,,\n2020-09-08 21:00,,\n")
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
        self.station = mommy.make(models.Station, name="Celduin")
        self.timeseries_group = mommy.make(models.TimeseriesGroup, gentity=self.station)
        self.timeseries = mommy.make(
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

    def test_station_last_update_naive_cache_invalidation(self):
        with self.assertNumQueries(2):
            self.station.last_update_naive

        # Check cache invalidation
        self.timeseries.save()
        with self.assertNumQueries(2):
            self.station.last_update_naive

    def test_timeseries_group_start_date_cache_invalidation(self):
        self.timeseries_group.default_timeseries
        with self.assertNumQueries(1):
            self.timeseries_group.start_date

        # Check cache invalidation
        self.timeseries.save()
        self.timeseries_group.default_timeseries
        with self.assertNumQueries(1):
            self.timeseries_group.start_date

    def test_timeseries_group_start_date_naive_cache_invalidation(self):
        # Make sure to retrieve the `default_timeseries` first.
        self.timeseries_group.default_timeseries

        with self.assertNumQueries(1):
            self.timeseries_group.start_date_naive

        # Check cache invalidation
        self.timeseries.save()
        self.timeseries_group.default_timeseries
        with self.assertNumQueries(1):
            self.timeseries_group.start_date_naive

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

    def test_timeseries_group_end_date_naive_cache_invalidation(self):
        # Make sure to retrieve the `default_timeseries` first.
        self.timeseries_group.default_timeseries

        with self.assertNumQueries(1):
            self.timeseries_group.end_date_naive

        # Check cache invalidation
        self.timeseries.save()
        self.timeseries_group.default_timeseries
        with self.assertNumQueries(1):
            self.timeseries_group.end_date_naive

    def test_timeseries_start_date_cache_invalidation(self):
        with self.assertNumQueries(1):
            self.timeseries.start_date

        # Check cache invalidation
        self.timeseries.save()
        with self.assertNumQueries(1):
            self.timeseries.start_date

    def test_timeseries_start_date_naive_cache_invalidation(self):
        with self.assertNumQueries(1):
            self.timeseries.start_date_naive

        # Check cache invalidation
        self.timeseries.save()
        with self.assertNumQueries(1):
            self.timeseries.start_date_naive

    def test_timeseries_end_date_cache_invalidation(self):
        with self.assertNumQueries(1):
            self.timeseries.end_date

        # Check cache invalidation
        self.timeseries.save()
        with self.assertNumQueries(1):
            self.timeseries.end_date

    def test_timeseries_end_date_naive_cache_invalidation(self):
        with self.assertNumQueries(1):
            self.timeseries.end_date_naive

        # Check cache invalidation
        self.timeseries.save()
        with self.assertNumQueries(1):
            self.timeseries.end_date_naive
