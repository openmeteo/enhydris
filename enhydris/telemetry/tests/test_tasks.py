from unittest.mock import PropertyMock, patch

from django.test import TestCase

from model_mommy import mommy

from enhydris.telemetry import tasks
from enhydris.telemetry.models import Telemetry


@patch("enhydris.telemetry.tasks.cache")
@patch("enhydris.telemetry.models.Telemetry.fetch")
class FetchTelemetryDataTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.telemetry = mommy.make(Telemetry)

    def test_adds_lock(self, mock_fetch, mock_cache):
        tasks.fetch_telemetry_data(self.telemetry.id)
        mock_cache.add.assert_called_once()
        args = mock_cache.add.call_args.args
        self.assertEqual(args[0], f"telemetry-{self.telemetry.id}")
        self.assertEqual(args[2], 360)

    def test_calls_telemetry_fetch(self, mock_fetch, mock_cache):
        tasks.fetch_telemetry_data(self.telemetry.id)
        mock_fetch.assert_called_once_with()

    def test_deletes_lock(self, mock_fetch, mock_cache):
        tasks.fetch_telemetry_data(self.telemetry.id)
        mock_cache.delete.assert_called_once_with(f"telemetry-{self.telemetry.id}")

    def test_deletes_lock_on_error(self, mock_fetch, mock_cache):
        mock_fetch.side_effect = RuntimeError("error")
        try:
            tasks.fetch_telemetry_data(self.telemetry.id)
        except RuntimeError:
            pass
        mock_cache.delete.assert_called_once_with(f"telemetry-{self.telemetry.id}")

    def test_does_not_fetch_if_locked(self, mock_fetch, mock_cache):
        mock_cache.add.return_value = False
        tasks.fetch_telemetry_data(self.telemetry.id)
        mock_fetch.assert_not_called()

    @patch("enhydris.telemetry.tasks.logger")
    def test_logs_error_if_locked(self, mock_logger, mock_fetch, mock_cache):
        mock_cache.add.return_value = False
        tasks.fetch_telemetry_data(self.telemetry.id)
        mock_logger.error.assert_called_once()


@patch("enhydris.telemetry.tasks.fetch_telemetry_data.delay")
class FetchAllTelemetryDataTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.telemetry1 = mommy.make(Telemetry)
        cls.telemetry2 = mommy.make(Telemetry)

    @patch("enhydris.telemetry.models.Telemetry.is_due", new_callable=PropertyMock)
    def test_calls_due_telemetry(self, mock_is_due, mock_fetch_telemetry_data):
        mock_is_due.return_value = True
        tasks.fetch_all_telemetry_data()
        self.assertEqual(mock_fetch_telemetry_data.call_count, 2)
        mock_fetch_telemetry_data.assert_any_call(self.telemetry1.id)
        mock_fetch_telemetry_data.assert_any_call(self.telemetry2.id)

    @patch("enhydris.telemetry.models.Telemetry.is_due", new_callable=PropertyMock)
    def test_not_calls_undue_telemetry(self, mock_is_due, mock_fetch_telemetry_data):
        mock_is_due.return_value = False
        tasks.fetch_all_telemetry_data()
        mock_fetch_telemetry_data.assert_not_called()
