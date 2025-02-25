import datetime as dt
from unittest import mock

from django.db import transaction
from django.test import TestCase, TransactionTestCase

import pandas as pd
from model_bakery import baker

from enhydris.autoprocess import tasks
from enhydris.autoprocess.models import AutoProcess, Checks, RangeCheck
from enhydris.models import Station, Timeseries, TimeseriesGroup
from enhydris.tests import ClearCacheMixin
from enhydris.tests.test_models.test_timeseries import get_tzinfo


class AutoProcessTestCase(TestCase):
    def setUp(self):
        self.station = baker.make(Station)
        self.timeseries_group1 = baker.make(TimeseriesGroup, gentity=self.station)
        self.timeseries_group2 = baker.make(TimeseriesGroup, gentity=self.station)

        self.original_execute_auto_process = tasks.execute_auto_process
        tasks.execute_auto_process = mock.MagicMock()

    def tearDown(self):
        tasks.execute_auto_process = self.original_execute_auto_process

    def test_create(self):
        auto_process = Checks(timeseries_group=self.timeseries_group1)
        auto_process.save()
        self.assertEqual(AutoProcess.objects.count(), 1)

    def test_update(self):
        baker.make(Checks, timeseries_group=self.timeseries_group1)
        auto_process = AutoProcess.objects.first()
        auto_process.timeseries_group = self.timeseries_group2
        auto_process.save()
        self.assertEqual(auto_process.timeseries_group.id, self.timeseries_group2.id)

    def test_delete(self):
        baker.make(Checks, timeseries_group=self.timeseries_group1)
        auto_process = AutoProcess.objects.first()
        auto_process.delete()
        self.assertEqual(AutoProcess.objects.count(), 0)


class AutoProcessSaveTestCase(TransactionTestCase):
    # Setting available_apps activates TRUNCATE ... CASCADE, which is necessary because
    # enhydris.TimeseriesRecord is unmanaged, TransactionTestCase doesn't attempt to
    # truncate it, and PostgreSQL complains it can't truncate enhydris_timeseries
    # without truncating enhydris_timeseriesrecord at the same time.
    available_apps = ["django.contrib.sites", "enhydris", "enhydris.autoprocess"]

    def setUp(self):
        with transaction.atomic():
            self.timeseries_group = baker.make(TimeseriesGroup)
        self.original_execute_auto_process = tasks.execute_auto_process
        tasks.execute_auto_process = mock.MagicMock()

    def test_save_triggers_auto_process(self):
        with transaction.atomic():
            auto_process = baker.make(Checks, timeseries_group=self.timeseries_group)
            auto_process.save()
        tasks.execute_auto_process.delay.assert_any_call(auto_process.id)

    def test_auto_process_is_not_triggered_before_commit(self):
        with transaction.atomic():
            auto_process = baker.make(Checks, timeseries_group=self.timeseries_group)
            auto_process.save()
            tasks.execute_auto_process.delay.assert_not_called()


@mock.patch(
    "enhydris.autoprocess.models.Checks.process_timeseries",
    side_effect=lambda self: self.htimeseries,
    autospec=True,
)
class AutoProcessExecuteTestCase(ClearCacheMixin, TestCase):
    def setUp(self):
        station = baker.make(Station, display_timezone="Etc/GMT-2")
        self.timeseries_group = baker.make(
            TimeseriesGroup,
            gentity=station,
            variable__descr="irrelevant",
        )
        self.checks = baker.make(Checks, timeseries_group=self.timeseries_group)
        self.range_check = baker.make(RangeCheck, checks=self.checks)

    def test_called_once(self, m):
        self.checks.execute()
        self.assertEqual(len(m.mock_calls), 1)

    def test_called_with_empty_content(self, m):
        self.checks.execute()
        self.assertEqual(len(self.checks.htimeseries.data), 0)

    def test_critical_error(self, m):
        m.side_effect = ValueError("hello")
        msg = (
            f"^ValueError while executing AutoProcess with id={self.checks.id}: hello$"
        )
        with self.assertRaisesRegex(RuntimeError, msg):
            self.checks.execute()


class AutoProcessExecuteDealsOnlyWithNewerTimeseriesPartTestCase(TestCase):
    @mock.patch(
        "enhydris.autoprocess.models.Checks.process_timeseries",
        side_effect=lambda self: self.htimeseries,
        autospec=True,
    )
    def setUp(self, m):
        self.mock_process_timeseries = m
        station = baker.make(Station, display_timezone="Etc/GMT-2")
        self.timeseries_group = baker.make(
            TimeseriesGroup,
            gentity=station,
            variable__descr="h",
        )
        self.source_timeseries = baker.make(
            Timeseries, timeseries_group=self.timeseries_group, type=Timeseries.INITIAL
        )
        self.source_timeseries.set_data(
            pd.DataFrame(
                data={"value": [1.0, 2.0, 3.0, 4.0], "flags": ["", "", "", ""]},
                columns=["value", "flags"],
                index=[
                    dt.datetime(2019, 5, 21, 17, 0, tzinfo=get_tzinfo("Etc/GMT-2")),
                    dt.datetime(2019, 5, 21, 17, 10, tzinfo=get_tzinfo("Etc/GMT-2")),
                    dt.datetime(2019, 5, 21, 17, 20, tzinfo=get_tzinfo("Etc/GMT-2")),
                    dt.datetime(2019, 5, 21, 17, 30, tzinfo=get_tzinfo("Etc/GMT-2")),
                ],
            )
        )
        self.target_timeseries = baker.make(
            Timeseries, timeseries_group=self.timeseries_group, type=Timeseries.CHECKED
        )
        self.target_timeseries.set_data(
            pd.DataFrame(
                data={"value": [1.0, 2.0], "flags": ["", ""]},
                columns=["value", "flags"],
                index=[
                    dt.datetime(2019, 5, 21, 17, 0, tzinfo=get_tzinfo("Etc/GMT-2")),
                    dt.datetime(2019, 5, 21, 17, 10, tzinfo=get_tzinfo("Etc/GMT-2")),
                ],
            ),
            default_timezone="Etc/GMT-2",
        )
        self.checks = baker.make(Checks, timeseries_group=self.timeseries_group)
        self.range_check = baker.make(RangeCheck, checks=self.checks)
        self.checks.execute()

    def test_called_once(self):
        self.assertEqual(len(self.mock_process_timeseries.mock_calls), 1)

    def test_called_with_the_newer_part_of_the_timeseries(self):
        expected_arg = pd.DataFrame(
            data={"value": [3.0, 4.0], "flags": ["", ""]},
            columns=["value", "flags"],
            index=[
                dt.datetime(2019, 5, 21, 17, 20, tzinfo=get_tzinfo("Etc/GMT-2")),
                dt.datetime(2019, 5, 21, 17, 30, tzinfo=get_tzinfo("Etc/GMT-2")),
            ],
        )
        expected_arg.index.name = "date"
        pd.testing.assert_frame_equal(self.checks.htimeseries.data, expected_arg)

    def test_appended_the_data(self):
        expected_result = pd.DataFrame(
            data={"value": [1.0, 2.0, 3.0, 4.0], "flags": ["", "", "", ""]},
            columns=["value", "flags"],
            index=[
                dt.datetime(2019, 5, 21, 17, 0, tzinfo=get_tzinfo("Etc/GMT-2")),
                dt.datetime(2019, 5, 21, 17, 10, tzinfo=get_tzinfo("Etc/GMT-2")),
                dt.datetime(2019, 5, 21, 17, 20, tzinfo=get_tzinfo("Etc/GMT-2")),
                dt.datetime(2019, 5, 21, 17, 30, tzinfo=get_tzinfo("Etc/GMT-2")),
            ],
        )
        expected_result.index.name = "date"
        pd.testing.assert_frame_equal(
            self.target_timeseries.get_data().data, expected_result
        )
