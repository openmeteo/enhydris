from __future__ import annotations

import copy
import datetime as dt
import logging
from io import StringIO
from typing import Any, Protocol, cast
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.cache import cache
from django.core.management import call_command
from django.test.utils import override_settings
from django.utils.log import DEFAULT_LOGGING, configure_logging

import django_selenium_clean  # type: ignore[import-untyped]
import pandas as pd
from htimeseries import HTimeseries
from model_bakery import baker

from enhydris import models


class ClearCacheMixin:
    settings_overrider: override_settings

    @classmethod
    def setUpClass(cls, *args: Any, **kwargs: Any):
        super().setUpClass(*args, **kwargs)  # type: ignore[misc]
        cls.settings_overrider = override_settings(
            CACHES={
                "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
            }
        )
        cls.settings_overrider.__enter__()
        cache.clear()

    @classmethod
    def tearDownClass(cls, *args: Any, **kwargs: Any):
        cls.settings_overrider.__exit__(None, None, None)
        super().tearDownClass(*args, **kwargs)  # type: ignore[misc]


class TestTimeseriesMixin(ClearCacheMixin):
    station: models.Station
    timeseries_group: models.TimeseriesGroup
    timeseries: models.Timeseries

    @classmethod
    def _create_test_timeseries(
        cls, data: str = "", publicly_available: bool | None = None
    ) -> None:
        cls.station = baker.make(
            models.Station,
            name="Celduin",
            geom=Point(x=21.06071, y=39.09518, srid=4326),
            altitude=219,
            display_timezone="Etc/GMT-2",
        )
        cls.timeseries_group = baker.make(
            models.TimeseriesGroup,
            name="Daily temperature",
            gentity=cls.station,
            unit_of_measurement__symbol="mm",
            precision=1,
            remarks="This timeseries group rocks",
        )
        cls.timeseries_group.variable.translations.create(
            language_code="en", descr="Temperature"
        )
        more_kwargs: dict[str, Any] = {}
        if publicly_available is not None:
            more_kwargs["publicly_available"] = publicly_available
        cls.timeseries = cast(
            models.Timeseries,
            baker.make(
                models.Timeseries,
                timeseries_group=cls.timeseries_group,
                type=models.Timeseries.INITIAL,
                time_step="H",
                **more_kwargs,
            ),
        )
        cls.timeseries.set_data(StringIO(data), default_timezone="Etc/GMT-2")


class TimeseriesDataMixin(ClearCacheMixin):
    timezone: str
    tzinfo: ZoneInfo
    htimeseries: HTimeseries
    station: models.Station
    variable: models.Variable
    timeseries_group: models.TimeseriesGroup
    timeseries: models.Timeseries

    @classmethod
    def create_timeseries(cls, publicly_available: bool | None = None) -> None:
        cls.timezone = "Etc/GMT-2"
        cls.tzinfo = ZoneInfo(cls.timezone)
        cls.htimeseries = HTimeseries()
        cls.htimeseries.data = pd.DataFrame(
            index=[
                dt.datetime(2017, 11, 23, 17, 23, tzinfo=cls.tzinfo),
                dt.datetime(2018, 11, 25, 1, 0, tzinfo=cls.tzinfo),
            ],
            data={"value": [1.0, 2.0], "flags": ["", ""]},
            columns=["value", "flags"],
        )
        cls.station = baker.make(
            models.Station,
            name="Komboti",
            geom=Point(x=21.00000, y=39.00000, srid=4326),
            display_timezone=cls.timezone,
        )
        cls.variable = models.Variable.objects.create()
        cls.variable.translations.create(language_code="en", descr="Beauty")
        cls.timeseries_group = baker.make(
            models.TimeseriesGroup,
            gentity=cls.station,
            precision=2,
            variable=cls.variable,
            unit_of_measurement__symbol="beauton",
        )
        more_kwargs: dict[str, Any] = {}
        if publicly_available is not None:
            more_kwargs["publicly_available"] = publicly_available
        cls.timeseries = cast(
            models.Timeseries,
            baker.make(
                models.Timeseries,
                type=models.Timeseries.INITIAL,
                timeseries_group=cls.timeseries_group,
                **more_kwargs,
            ),
        )
        cls.timeseries.set_data(cls.htimeseries.data, default_timezone=cls.timezone)


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
        for db_name in self._databases_names(include_mirrors=False):  # type: ignore
            call_command(
                "flush",
                verbosity=0,
                interactive=False,
                database=db_name,
                reset_sequences=False,
                allow_cascade=True,
                inhibit_post_migrate=False,
            )


class _HasTearDown(Protocol):
    def tearDown(self) -> None: ...


class OverrideLoggingMixin:
    saved_root_handlers: list[logging.Handler]

    def tearDown(self) -> None:
        cast(_HasTearDown, super()).tearDown()
        self._revert_logging_config()

    def _override_logging_config(self):
        """Override logging.

        We need to do this to avoid the test output being polluted with log messages.
        We can't just @override_settings, we also need to call configure_logging().
        """
        log_config = copy.deepcopy(DEFAULT_LOGGING)
        log_config["handlers"]["console"]["class"] = "logging.NullHandler"
        log_config["loggers"]["root"] = {"handlers": ["console"]}
        self.saved_root_handlers = logging.getLogger().root.handlers
        configure_logging(settings.LOGGING_CONFIG, log_config)

    def _revert_logging_config(self):
        if hasattr(self, "saved_root_handlers"):
            log_config = copy.deepcopy(DEFAULT_LOGGING)
            log_config["loggers"]["root"] = {"handlers": self.saved_root_handlers}
            configure_logging(settings.LOGGING_CONFIG, log_config)
