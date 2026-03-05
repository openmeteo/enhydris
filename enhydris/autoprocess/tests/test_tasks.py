from io import StringIO
from unittest import mock

from django.test import TestCase

from model_bakery import baker

from enhydris.autoprocess.models import Checks
from enhydris.autoprocess.tasks import execute_auto_process


class ExecuteAutoProcessTaskTestCase(TestCase):
    @mock.patch("enhydris.autoprocess.models.tasks.execute_auto_process")
    def setUp(self, m):
        self.auto_process = baker.make(Checks)
        self.target_timeseries = self.auto_process.target_timeseries
        self.target_timeseries.insert_or_append_data(
            StringIO("2020-01-01 00:00,10,\n"), default_timezone="UTC"
        )

    @mock.patch("enhydris.autoprocess.models.Checks.execute")
    def test_calls_execute_with_recalculate_true(self, m):
        execute_auto_process(self.auto_process.id, has_non_append_modifications=True)
        m.assert_called_once_with(recalculate=True)

    @mock.patch("enhydris.autoprocess.models.Checks.execute")
    def test_calls_execute_with_recalculate_false(self, m):
        execute_auto_process(self.auto_process.id, has_non_append_modifications=False)
        m.assert_called_once_with(recalculate=False)
