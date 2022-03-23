import datetime as dt
import os.path
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings

from enhydris import models, tasks
from enhydris.tests import TestTimeseriesMixin


class TestSaveTimeseriesDataMixin(TestTimeseriesMixin):
    def _prepare_data_file(self, data):
        self.tmpdir = tempfile.mkdtemp()
        self.datafilename = os.path.join(self.tmpdir, "datafile")
        with open(self.datafilename, "wb") as f:
            f.write(data)

    def _delete_data_dir(self):
        shutil.rmtree(self.tmpdir)


class TimeseriesAppendTestCase(TestSaveTimeseriesDataMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._create_test_timeseries(data="2019-01-01 00:30,25,\n")
        User.objects.create_user(
            username="alice", password="topsecret", email="alice@example.com"
        )

    def setUp(self):
        self._prepare_data_file(data=b"2019-04-09 13:36,0,\n")
        tasks.save_timeseries_data(
            id=self.timeseries.id,
            replace_or_append="APPEND",
            datafilename=self.datafilename,
            username="alice",
        )

    def tearDown(self):
        self._delete_data_dir()

    def test_data_length(self):
        self.assertEqual(len(self.timeseries.get_data().data), 2)

    def test_first_record(self):
        self.assertEqual(
            self.timeseries.get_data().data.index[0], dt.datetime(2019, 1, 1, 0, 30)
        )

    def test_second_record(self):
        self.assertEqual(
            self.timeseries.get_data().data.index[1], dt.datetime(2019, 4, 9, 13, 36)
        )


class TimeseriesReplaceTestCase(TestSaveTimeseriesDataMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._create_test_timeseries(data="2019-01-01 00:30,25,\n")
        User.objects.create_user(
            username="alice", password="topsecret", email="alice@example.com"
        )

    def setUp(self):
        self._prepare_data_file(b"2005-12-01 18:35,7,\n2019-04-09 13:36,0,\n")
        tasks.save_timeseries_data(
            id=self.timeseries.id,
            replace_or_append="REPLACE",
            datafilename=self.datafilename,
            username="alice",
        )

    def tearDown(self):
        self._delete_data_dir()

    def test_data_length(self):
        self.assertEqual(len(self.timeseries.get_data().data), 2)

    def test_first_record(self):
        self.assertEqual(
            self.timeseries.get_data().data.index[0], dt.datetime(2005, 12, 1, 18, 35)
        )

    def test_second_record(self):
        self.assertEqual(
            self.timeseries.get_data().data.index[1], dt.datetime(2019, 4, 9, 13, 36)
        )


class TimeseriesPrecisionTestCase(TestSaveTimeseriesDataMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._create_test_timeseries(data="2019-01-01 00:30,25,\n")
        User.objects.create_user(
            username="alice", password="topsecret", email="alice@example.com"
        )

    def setUp(self):
        self._prepare_data_file(b"Precision=2\n\n2019-08-18 12:39,0.12345678901234,\n")
        tasks.save_timeseries_data(
            id=self.timeseries.id,
            replace_or_append="REPLACE",
            datafilename=self.datafilename,
            username="alice",
        )

    def tearDown(self):
        self._delete_data_dir()

    def test_saves_data_with_full_precision(self):
        # Although the time series has a specified precision of 2, we want it to store
        # all the decimal digits to avoid losing data when the user makes an error when
        # entering the precision.
        self.assertAlmostEqual(
            models.Timeseries.objects.first().timeseriesrecord_set.first().value,
            0.12345678901234,
        )

    def test_appends_data_with_full_precision(self):
        self._delete_data_dir()
        self._prepare_data_file(b"Precision=2\n\n2019-08-19 12:39,3.14159065358979,\n")
        tasks.save_timeseries_data(
            id=self.timeseries.id,
            replace_or_append="APPEND",
            datafilename=self.datafilename,
            username="alice",
        )
        self.assertAlmostEqual(
            models.Timeseries.objects.first().timeseriesrecord_set.last().value,
            3.14159065358979,
        )


class TimeseriesFileWithUnicodeHeadersTestCase(TestSaveTimeseriesDataMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._create_test_timeseries()
        User.objects.create_user(
            username="alice", password="topsecret", email="alice@example.com"
        )

    def setUp(self):
        self._prepare_data_file(
            "Station=Πάπιγκο\n\n2019-04-09 13:36,0,\n".encode("utf-8")
        )
        tasks.save_timeseries_data(
            id=self.timeseries.id,
            replace_or_append="REPLACE",
            datafilename=self.datafilename,
            username="alice",
        )

    def tearDown(self):
        self._delete_data_dir()

    def test_data_length(self):
        self.assertEqual(len(self.timeseries.get_data().data), 1)

    def test_first_record(self):
        self.assertEqual(
            self.timeseries.get_data().data.index[0], dt.datetime(2019, 4, 9, 13, 36)
        )


class DeletesDataFileTestCase(TestSaveTimeseriesDataMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._create_test_timeseries()
        User.objects.create_user(
            username="alice", password="topsecret", email="alice@example.com"
        )

    def setUp(self):
        self._prepare_data_file(b"2019-08-18 12:39,0.12345678901234,\n")
        tasks.save_timeseries_data(
            id=self.timeseries.id,
            replace_or_append="REPLACE",
            datafilename=self.datafilename,
            username="alice",
        )

    def tearDown(self):
        self._delete_data_dir()

    def test_deletes_data_file(self):
        self.assertFalse(os.path.exists(self.datafilename))


class NotificationTestCase(TestSaveTimeseriesDataMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._create_test_timeseries()
        User.objects.create_user(
            username="alice", password="topsecret", email="alice@example.com"
        )

    @override_settings(DEFAULT_FROM_EMAIL="hello@world.com")
    def setUp(self):
        self._prepare_data_file(b"2019-08-18 12:39,0.12345678901234,\n")
        mail.outbox = []
        tasks.save_timeseries_data(
            id=self.timeseries.id,
            replace_or_append="REPLACE",
            datafilename=self.datafilename,
            username="alice",
        )

    def tearDown(self):
        self._delete_data_dir()

    def test_sends_email(self):
        self.assertEqual(len(mail.outbox), 1)

    def test_recipient(self):
        self.assertEqual(mail.outbox[0].to, ["alice@example.com"])

    def test_sender(self):
        self.assertEqual(mail.outbox[0].from_email, "hello@world.com")

    def test_subject(self):
        self.assertEqual(
            mail.outbox[0].subject,
            'Time series "Celduin - Daily temperature - Initial" '
            "was imported successfully",
        )

    def test_body(self):
        self.assertEqual(
            mail.outbox[0].subject,
            'Time series "Celduin - Daily temperature - Initial" '
            "was imported successfully",
        )


class FailureTestCase(TestSaveTimeseriesDataMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._create_test_timeseries()
        User.objects.create_user(
            username="alice", password="topsecret", email="alice@example.com"
        )

    @override_settings(DEFAULT_FROM_EMAIL="hello@world.com")
    def setUp(self):
        mail.outbox = []
        std = tasks.SaveTimeseriesData()
        std.read_arguments(
            id=self.timeseries.id,
            replace_or_append="REPLACE",
            datafilename="/nonexistent_file",
            username="alice",
        )
        std.on_failure()

    def test_sends_email(self):
        self.assertEqual(len(mail.outbox), 1)

    def test_recipient(self):
        self.assertEqual(mail.outbox[0].to, ["alice@example.com"])

    def test_sender(self):
        self.assertEqual(mail.outbox[0].from_email, "hello@world.com")

    def test_subject(self):
        self.assertEqual(
            mail.outbox[0].subject,
            'Importing time series "Celduin - Daily temperature - Initial" failed',
        )
