import datetime as dt
from io import StringIO

from django.contrib.gis.geos import Point
from django.core.cache import cache
from django.core.management import call_command
from django.test.utils import override_settings

import django_selenium_clean
import pandas as pd
from htimeseries import HTimeseries
from model_mommy import mommy
from parler.utils.context import switch_language

from enhydris import models


class ClearCacheMixin:
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.settings_overrider = override_settings(
            CACHES={
                "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
            }
        )
        cls.settings_overrider.__enter__()
        cache.clear()

    @classmethod
    def tearDownClass(cls, *args, **kwargs):
        cls.settings_overrider.__exit__(exc_type=None, exc_value=None, traceback=None)
        super().tearDownClass(*args, **kwargs)


class TestTimeseriesMixin(ClearCacheMixin):
    @classmethod
    def _create_test_timeseries(cls, data=""):
        cls.station = mommy.make(
            models.Station,
            name="Celduin",
            original_srid=2100,
            geom=Point(x=21.06071, y=39.09518, srid=4326),
            altitude=219,
        )
        cls.timeseries_group = mommy.make(
            models.TimeseriesGroup,
            name="Daily temperature",
            gentity=cls.station,
            unit_of_measurement__symbol="mm",
            time_zone__code="IST",
            time_zone__utc_offset=330,
            variable__descr="Temperature",
            precision=1,
            remarks="This timeseries group rocks",
        )
        cls.timeseries = mommy.make(
            models.Timeseries,
            timeseries_group=cls.timeseries_group,
            type=models.Timeseries.INITIAL,
            time_step="H",
        )
        cls.timeseries.set_data(StringIO(data))


class TimeseriesDataMixin(ClearCacheMixin):
    def create_timeseries(self):
        self.htimeseries = HTimeseries()
        self.htimeseries.data = pd.DataFrame(
            index=[dt.datetime(2017, 11, 23, 17, 23), dt.datetime(2018, 11, 25, 1, 0)],
            data={"value": [1.0, 2.0], "flags": ["", ""]},
            columns=["value", "flags"],
        )
        self.station = mommy.make(
            models.Station,
            name="Komboti",
            geom=Point(x=21.00000, y=39.00000, srid=4326),
            original_srid=4326,
        )
        self.time_zone = mommy.make(models.TimeZone, code="EET", utc_offset=120)
        self.variable = models.Variable()
        with switch_language(self.variable, "en"):
            self.variable.descr = "Beauty"
            self.variable.save()
        self.timeseries_group = mommy.make(
            models.TimeseriesGroup,
            gentity=self.station,
            time_zone=self.time_zone,
            precision=2,
            variable=self.variable,
            unit_of_measurement__symbol="beauton",
        )
        self.timeseries = mommy.make(
            models.Timeseries,
            type=models.Timeseries.INITIAL,
            timeseries_group=self.timeseries_group,
        )
        self.timeseries.set_data(self.htimeseries.data)


class SeleniumTestCase(django_selenium_clean.SeleniumTestCase):
    """A change in SeleniumTestCase so that it succeeds in truncating.

    SeleniumTestCase inherits LiveServerTestCase, which inherits TransactionTestCase.
    In contrast to TestCase, which wraps tests in "atomic", TransactionTestCase
    truncates the database in the end by calling the "flush" management command. In our
    case, this fails with "ERROR: cannot truncate a table referenced in a foreign key
    constraint". The reason is that TimeseriesRecord is unmanaged, so "flush" doesn't
    truncate it, but "flush" truncates Timeseries, and TimeseriesRecord has a foreign
    key to Timeseries.

    To fix this, we override TransactionTestCase's _fixture_teardown(), ensuring it
    executes TRUNCATE with CASCADE.

    The same result might have been achieved by setting
    TransactionTestCase.available_apps, but this is a private API that is subject to
    change without notice, and, well, go figure.
    """

    def _fixture_teardown(self):
        for db_name in self._databases_names(include_mirrors=False):
            call_command(
                "flush",
                verbosity=0,
                interactive=False,
                database=db_name,
                reset_sequences=False,
                allow_cascade=True,
                inhibit_post_migrate=False,
            )
