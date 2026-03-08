import datetime as dt
from io import StringIO
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import translation

from model_bakery import baker

from enhydris import models
from enhydris.tests import TimeseriesDataMixin


class VariableTestCase(TestCase):
    def test_str(self):
        gact = self._create_variable("Temperature", "Θερμοκρασία")
        self.assertEqual(str(gact), "Temperature")
        with translation.override("el"):
            self.assertEqual(str(gact), "Θερμοκρασία")

    def test_manager_includes_objects_with_missing_translations(self):
        variable = models.Variable.objects.create()
        variable.translations.create(language_code="en", descr="hello")
        self.assertEqual(str(variable), "hello")
        with translation.override("el"):
            models.Variable.objects.get(id=variable.pk)  # Shouldn't raise anything

    def test_sort(self):
        self._create_variable("Temperature", "Θερμοκρασία")
        self._create_variable("Humidity", "Υγρασία")
        self.assertEqual(
            [v.descr for v in models.Variable.objects.all()],
            ["Humidity", "Temperature"],
        )
        with translation.override("el"):
            self.assertEqual(
                [v.descr for v in models.Variable.objects.all()],
                ["Θερμοκρασία", "Υγρασία"],
            )

    def _create_variable(self, english_name: str, greek_name: str):
        variable = models.Variable.objects.create()
        models.VariableTranslation.objects.create(
            variable=variable, language_code="el", descr=greek_name
        )
        models.VariableTranslation.objects.create(
            variable=variable, language_code="en", descr=english_name
        )
        return variable

    @override_settings(
        ENHYDRIS_USERS_CAN_ADD_CONTENT=True,
        LANGUAGE_CODE="en",
        LANGUAGES={("en", "English"), ("el", "Ελληνικά")},
    )
    def test_translation_bug(self):
        # The admin must render even when active language has no translation.
        User.objects.create_user(
            username="alice", password="topsecret", is_active=True, is_staff=True
        )
        self.client.login(username="alice", password="topsecret")
        variable = models.Variable.objects.create()
        variable.translations.create(language_code="en", descr="pH")
        response = self.client.get(
            "/admin/enhydris/station/add/", HTTP_ACCEPT_LANGUAGE="el"
        )
        self.assertEqual(response.status_code, 200)


class UnitOfMeasurementTestCase(TestCase):
    def test_str(self):
        unit = baker.make(models.UnitOfMeasurement, symbol="mm")
        self.assertEqual(str(unit), "mm")

    def test_str_when_symbol_is_empty(self):
        unit = baker.make(models.UnitOfMeasurement, symbol="")
        self.assertEqual(str(unit), str(unit.pk))


class TimeseriesGroupGetNameTestCase(TestCase):
    def setUp(self):
        self.timeseries_group = baker.make(models.TimeseriesGroup, name="")
        self.timeseries_group.variable.translations.create(
            language_code="en", descr="Temperature"
        )

    def test_get_name_when_name_is_blank(self):
        self.assertEqual(self.timeseries_group.get_name(), "Temperature")

    def test_get_name_when_name_is_not_blank(self):
        self.timeseries_group.name = "Temperature from sensor 1"
        self.assertEqual(self.timeseries_group.get_name(), "Temperature from sensor 1")

    def test_get_name_when_translations_are_inactive(self):
        with translation.override(None):
            self.assertEqual(self.timeseries_group.get_name(), "Temperature")


class TimeseriesGroupDefaultTimeseriesTestCase(TestCase):
    def setUp(self):
        self.timeseries_group = baker.make(models.TimeseriesGroup, name="")
        self.initial_timeseries = self._make_timeseries(models.Timeseries.INITIAL)
        self.checked_timeseries = self._make_timeseries(models.Timeseries.CHECKED)
        self.regularized_timeseries = self._make_timeseries(
            models.Timeseries.REGULARIZED
        )

    def _make_timeseries(self, type: int):
        return baker.make(
            models.Timeseries, timeseries_group=self.timeseries_group, type=type
        )

    def test_returns_regularized(self):
        self.assertEqual(
            self.timeseries_group.default_timeseries, self.regularized_timeseries
        )

    def test_returns_checked(self):
        self.regularized_timeseries.delete()
        self.assertEqual(
            self.timeseries_group.default_timeseries, self.checked_timeseries
        )

    def test_returns_initial(self):
        self.regularized_timeseries.delete()
        self.checked_timeseries.delete()
        self.assertEqual(
            self.timeseries_group.default_timeseries, self.initial_timeseries
        )

    def test_returns_none(self):
        self.regularized_timeseries.delete()
        self.checked_timeseries.delete()
        self.initial_timeseries.delete()
        self.assertIsNone(self.timeseries_group.default_timeseries)

    def test_caching(self):
        with self.assertNumQueries(1):
            self.timeseries_group.default_timeseries
        with self.assertNumQueries(0):
            self.timeseries_group.default_timeseries

    def test_num_queries(self):
        with self.assertNumQueries(2):
            # The following should cause two queries.
            group = models.TimeseriesGroup.objects.prefetch_related(
                "timeseries_set"
            ).get()
            # The following should cause no queries since the time series have
            # been prefetched.
            group.default_timeseries


class TimeseriesGroupStartAndEndDateTestCase(TimeseriesDataMixin, TestCase):
    def setUp(self):
        self.create_timeseries()

    def test_start_date(self):
        self.assertEqual(
            self.timeseries_group.start_date,
            dt.datetime(2017, 11, 23, 17, 23, tzinfo=ZoneInfo(self.timezone)),
        )

    def test_start_date_cache(self):
        # Make sure to retrieve the `default_timeseries` first.
        self.timeseries_group.default_timeseries

        with self.assertNumQueries(1):
            self.timeseries_group.start_date

        timeseries_group = models.TimeseriesGroup.objects.get(
            id=self.timeseries_group.pk
        )
        with self.assertNumQueries(0):
            timeseries_group.start_date

    def test_end_date(self):
        self.assertEqual(
            self.timeseries_group.end_date,
            dt.datetime(2018, 11, 25, 1, 0, tzinfo=ZoneInfo(self.timezone)),
        )

    def test_end_date_cache(self):
        # Make sure to retrieve the `default_timeseries` first.
        self.timeseries_group.default_timeseries

        with self.assertNumQueries(1):
            self.timeseries_group.end_date

        timeseries_group = models.TimeseriesGroup.objects.get(
            id=self.timeseries_group.pk
        )
        with self.assertNumQueries(0):
            timeseries_group.end_date

    def test_start_date_when_timeseries_is_empty(self):
        self.timeseries.set_data(StringIO(""))
        self.assertIsNone(self.timeseries_group.start_date)

    def test_end_date_when_timeseries_is_empty(self):
        self.timeseries.set_data(StringIO(""))
        self.assertIsNone(self.timeseries_group.end_date)

    def test_start_date_when_timeseries_does_not_exist(self):
        self.timeseries.delete()
        self.assertIsNone(self.timeseries_group.start_date)

    def test_end_date_when_timeseries_does_not_exist(self):
        self.timeseries.delete()
        self.assertIsNone(self.timeseries_group.end_date)


class TimestepTestCase(TestCase):
    def setUp(self):
        self.timeseries = baker.make(models.Timeseries)

    def set_time_step(self, time_step: str):
        self.timeseries.time_step = time_step
        self.timeseries.save()

    def test_min(self):
        self.set_time_step("27min")
        self.assertEqual(models.Timeseries.objects.get().time_step, "27min")

    def test_hour(self):
        self.set_time_step("3H")
        self.assertEqual(models.Timeseries.objects.get().time_step, "3H")

    def test_day(self):
        self.set_time_step("3D")
        self.assertEqual(models.Timeseries.objects.get().time_step, "3D")

    def test_month(self):
        self.set_time_step("3M")
        self.assertEqual(models.Timeseries.objects.get().time_step, "3M")

    def test_3Y(self):
        self.set_time_step("3Y")
        self.assertEqual(models.Timeseries.objects.get().time_step, "3Y")

    def test_Y(self):
        self.set_time_step("Y")
        self.assertEqual(models.Timeseries.objects.get().time_step, "Y")

    def test_garbage(self):
        with self.assertRaisesRegex(ValueError, '"hello" is not a valid time step'):
            self.set_time_step("hello")

    def test_wrong_number(self):
        with self.assertRaisesRegex(ValueError, '"FM" is not a valid time step'):
            self.set_time_step("FM")

    def test_wrong_unit(self):
        with self.assertRaisesRegex(ValueError, '"3B" is not a valid time step'):
            self.set_time_step("3B")
