from io import StringIO
from unittest import mock

from django.contrib.gis.geos import Point
from django.db import transaction
from django.test import TransactionTestCase

from model_bakery import baker

from enhydris.autoprocess.models import Checks
from enhydris.models import Station, Timeseries


class EnqueueAutoProcessTestCase(TransactionTestCase):
    # Setting available_apps activates TRUNCATE ... CASCADE, which is necessary because
    # enhydris.TimeseriesRecord is unmanaged, TransactionTestCase doesn't attempt to
    # truncate it, and PostgreSQL complains it can't truncate enhydris_timeseries
    # without truncating enhydris_timeseriesrecord at the same time.
    available_apps = ["django.contrib.sites", "enhydris", "enhydris.autoprocess"]

    # Creating autoprocesses triggers tasks, so we patch some things in order to not
    # pollute the celery queue while testing.
    @mock.patch("enhydris.autoprocess.models.tasks.execute_auto_process")
    @mock.patch("enhydris.autoprocess.apps.execute_auto_process")
    def setUp(self, m1, m2):
        self.station = baker.make(Station, geom=Point(x=21.06, y=39.09, srid=4326))
        self.auto_process = baker.make(
            Checks,
            timeseries_group__gentity=self.station,
            target_timeseries_group__gentity=self.station,
        )
        self.timeseries = baker.make(
            Timeseries,
            timeseries_group=self.auto_process.timeseries_group,
            type=Timeseries.INITIAL,
        )

    @mock.patch("enhydris.autoprocess.apps.execute_auto_process")
    def test_enqueues_auto_process(self, m):
        with transaction.atomic():
            self.timeseries.save()
        m.delay.assert_called_once_with(self.auto_process.id, False)

    @mock.patch("enhydris.autoprocess.apps.execute_auto_process")
    def test_auto_process_is_not_triggered_before_commit(self, m):
        with transaction.atomic():
            self.timeseries.save()
            m.delay.assert_not_called()

    @mock.patch("enhydris.autoprocess.apps.execute_auto_process")
    def test_inserting_data_enqueues_task_with_non_append_modifications_true(self, m):
        self.timeseries.insert_or_append_data(
            StringIO("2020-01-01 00:10,15,\n"),
            default_timezone="UTC",
            append_only=False,
        )
        m.delay.assert_called_once_with(self.auto_process.id, True)

    @mock.patch("enhydris.autoprocess.apps.execute_auto_process")
    def test_appending_data_enqueues_task_with_non_append_modifications_false(self, m):
        self.timeseries.insert_or_append_data(
            StringIO("2020-01-01 00:10,15,\n"),
            default_timezone="UTC",
            append_only=True,
        )
        m.delay.assert_called_once_with(self.auto_process.id, False)
