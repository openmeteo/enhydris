import datetime as dt
from io import StringIO
from itertools import islice
from os.path import abspath
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.gis.db import models
from django.core.cache import cache
from django.core.files.storage import FileSystemStorage
from django.db import IntegrityError, connection
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

import numpy as np
from htimeseries import HTimeseries

from .gentity import Station
from .timeseries_group import TimeseriesGroup


def check_time_step(time_step):
    if not time_step:
        return
    else:
        _check_nonempty_time_step(time_step)


def _check_nonempty_time_step(time_step):
    number, unit = _parse_time_step(time_step)
    if unit not in ("min", "H", "D", "M", "Y", "h"):
        raise ValueError('"{}" is not a valid time step'.format(time_step))


def _parse_time_step(time_step):
    first_nondigit_pos = 0
    length = len(time_step)
    while first_nondigit_pos < length and time_step[first_nondigit_pos].isdigit():
        first_nondigit_pos += 1
    number = time_step[:first_nondigit_pos]
    unit = time_step[first_nondigit_pos:]
    return number, unit


class TimeseriesStorage(FileSystemStorage):
    """Stores timeseries data files in settings.ENHYDRIS_TIMESERIES_DATA_DIR.

    TimeseriesStorage() is essentially the same as
    FileSystemStorage(location=settings.ENHYDRIS_TIMESERIES_DATA_DIR)), with
    the difference that it checks the value of ENHYDRIS_TIMESERIES_DATA_DIR
    each time it does something. This allows the setting to be overridden
    in unit tests with override_settings(). If using FileSystemStorage,
    it would not be overriddable, because "location" would be set when
    models.py is read and that would be it.
    """

    def path(self, name):
        self.location = abspath(settings.ENHYDRIS_TIMESERIES_DATA_DIR)
        return super().path(name)


class DataNotInCache(Exception):
    pass


def get_default_publicly_available():
    return settings.ENHYDRIS_DEFAULT_PUBLICLY_AVAILABLE


class Timeseries(models.Model):
    INITIAL = 100
    CHECKED = 200
    REGULARIZED = 300
    AGGREGATED = 400
    TIMESERIES_TYPES = (
        (INITIAL, _("Initial")),
        (CHECKED, _("Checked")),
        (REGULARIZED, _("Regularized")),
        (AGGREGATED, _("Aggregated")),
    )

    last_modified = models.DateTimeField(default=now, null=True, editable=False)
    timeseries_group = models.ForeignKey(TimeseriesGroup, on_delete=models.CASCADE)
    type = models.PositiveSmallIntegerField(
        choices=TIMESERIES_TYPES, verbose_name=_("Type")
    )
    time_step = models.CharField(
        max_length=7,
        blank=True,
        help_text=_(
            'E.g. "10min", "H" (hourly), "D" (daily), "M" (monthly), "Y" (yearly). '
            "More specifically, it's an optional number plus a unit, with no space in "
            "between. The units available are min, H, D, M, Y. Leave empty if the time "
            "series is irregular."
        ),
        verbose_name=_("Time step"),
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text=_(
            "You can leave this empty, unless you have many time series for this group "
            "with the same type and time step (for example, if you have a time series "
            "aggregated on the mean and another aggregated on the max value)."
        ),
        verbose_name=_("Name"),
    )
    publicly_available = models.BooleanField(
        default=get_default_publicly_available,
        verbose_name=_("Publicly available"),
        help_text=_(
            "Whether users who have not logged on have permission to download the time "
            "series data."
        ),
    )

    class Meta:
        verbose_name = pgettext_lazy("Singular", "Time series")
        verbose_name_plural = pgettext_lazy("Plural", "Time series")
        ordering = ("type",)
        unique_together = ["timeseries_group", "type", "time_step", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["timeseries_group"],
                condition=models.Q(type=100),
                name="only_one_initial_timeseries_per_group",
            ),
            models.UniqueConstraint(
                fields=["timeseries_group"],
                condition=models.Q(type=200),
                name="only_one_checked_timeseries_per_group",
            ),
            models.UniqueConstraint(
                fields=["timeseries_group"],
                condition=models.Q(type=300),
                name="only_one_regularized_timeseries_per_group",
            ),
        ]

    @property
    def start_date(self):
        def get_start_date():
            try:
                return self.timeseriesrecord_set.earliest().timestamp.astimezone(
                    ZoneInfo(self.timeseries_group.gentity.display_timezone)
                )
            except (TimeseriesRecord.DoesNotExist, ValueError):
                # The ValueError above is for the case where the Timeseries object does
                # not have a primary key yet (has not been saved), which causes a
                # problem in Django>=4.
                return None

        return cache.get_or_set(f"timeseries_start_date_{self.id}", get_start_date)

    @property
    def end_date(self):
        def get_end_date():
            try:
                return self.timeseriesrecord_set.latest().timestamp.astimezone(
                    ZoneInfo(self.timeseries_group.gentity.display_timezone)
                )
            except (TimeseriesRecord.DoesNotExist, ValueError):
                # The ValueError above is for the case where the Timeseries object does
                # not have a primary key yet (has not been saved), which causes a
                # problem in Django>=4.
                return None

        return cache.get_or_set(f"timeseries_end_date_{self.id}", get_end_date)

    def _set_extra_timeseries_properties(self, ahtimeseries, timezone):
        if self.timeseries_group.gentity.geom:
            location = {
                "abscissa": self.timeseries_group.gentity.gpoint.original_abscissa(),
                "ordinate": self.timeseries_group.gentity.gpoint.original_ordinate(),
                "srid": self.timeseries_group.gentity.gpoint.original_srid,
                "altitude": self.timeseries_group.gentity.gpoint.altitude,
            }
        else:
            location = None
        ahtimeseries.time_step = self.time_step
        ahtimeseries.unit = self.timeseries_group.unit_of_measurement.symbol
        ahtimeseries.title = self.timeseries_group.get_name()
        ahtimeseries.timezone = self._format_timezone(timezone)
        ahtimeseries.variable = self.timeseries_group.variable.descr
        ahtimeseries.precision = self.timeseries_group.precision
        ahtimeseries.location = location
        ahtimeseries.comment = (
            f"{self.timeseries_group.gentity.name}\n\n{self.timeseries_group.remarks}"
        )

    def _format_timezone(self, timezone):
        offset = self._get_timezone_offset(timezone)
        return f"{timezone} (UTC{offset})"

    def _get_timezone_offset(self, timezone):
        assert timezone == "UTC" or (
            timezone.startswith("Etc/GMT") and len(timezone) in (7, 9, 10)
        )
        if timezone in ("Etc/GMT", "UTC"):
            return "+0000"
        sign = "-" if timezone[7] == "+" else "+"
        if len(timezone) == 9:
            return f"{sign}0{timezone[8]}00"
        else:
            return f"{sign}{timezone[8:]}00"

    def get_data(self, start_date=None, end_date=None, timezone=None):
        start_date = start_date or dt.datetime(1678, 1, 1, 0, 0, tzinfo=dt.timezone.utc)
        end_date = end_date or dt.datetime(2261, 12, 31, 23, 59, tzinfo=dt.timezone.utc)
        try:
            data = self._get_data_from_cache(start_date, end_date)
        except DataNotInCache:
            data = self._retrieve_and_cache_data(start_date, end_date)
        timezone = timezone or self.timeseries_group.gentity.display_timezone
        if not data.empty:
            data.index = data.index.tz_convert(timezone)
        result = HTimeseries(data)
        self._set_extra_timeseries_properties(result, timezone)
        return result

    def _get_data_from_cache(self, start_date, end_date):
        data = cache.get(f"timeseries_data_{self.id}")
        if data is None or data.empty:
            raise DataNotInCache()
        if self.start_date is None:
            return data  # Data should be empty in that case; just return it
        try:
            start_date = max(start_date, self.start_date).astimezone(data.index.tzinfo)
            end_date = min(end_date, self.end_date).astimezone(data.index.tzinfo)
        except TypeError:
            # A TypeError will occur if self.start_date or self.end_date above is none.
            # This should normally not happen, because self.start_date had already
            # been checked immediately before, and self.end_date is not none whenever
            # self.start_date is not none. However there's a race condition where
            # another thread or process could have updated the time series (and
            # invalidated the cache) in between these statements.
            raise DataNotInCache()
        if data.index.min() > start_date or data.index.max() < end_date:
            raise DataNotInCache()
        return data.loc[start_date:end_date]

    def _retrieve_and_cache_data(self, start_date, end_date):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT STRING_AGG(
                    TO_CHAR(timestamp AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS')
                        || ','
                        || CASE WHEN value is NULL THEN DOUBLE PRECISION 'NaN'
                           ELSE value END
                        || ','
                        || flags,
                    E'\n'
                    ORDER BY timestamp
                ) || E'\n'
                FROM enhydris_timeseriesrecord
                WHERE timeseries_id=%s AND timestamp >= %s AND timestamp <= %s
                """,
                [self.id, start_date, end_date],
            )
            result_string = StringIO(cursor.fetchone()[0])
        data = HTimeseries(result_string, default_tzinfo=dt.timezone.utc).data
        cache.set(f"timeseries_data_{self.id}", data)
        return data

    def set_data(self, data, default_timezone=None):
        self.timeseriesrecord_set.all().delete()
        return self.append_data(data, default_timezone)

    def append_data(self, data, default_timezone=None):
        ahtimeseries = self._get_htimeseries_from_data(data, default_timezone)
        self._check_new_data_is_newer(ahtimeseries)
        result = TimeseriesRecord.bulk_insert(self, ahtimeseries)
        self.save()
        return result

    def _check_new_data_is_newer(self, ahtimeseries):
        if not len(ahtimeseries.data):
            return 0
        new_data_start_date = ahtimeseries.data.index[0]
        if self.end_date is not None and self.end_date >= new_data_start_date:
            raise IntegrityError(
                (
                    "Cannot append time series: "
                    "its first record ({}) has a date earlier than the last "
                    "record ({}) of the timeseries to append to."
                ).format(new_data_start_date, self.end_date)
            )

    def _get_htimeseries_from_data(self, data, default_timezone):
        default_tzinfo = default_timezone and ZoneInfo(default_timezone) or None
        if isinstance(data, HTimeseries):
            return data
        else:
            return HTimeseries(data, default_tzinfo=default_tzinfo)

    def get_last_record_as_string(self, timezone=None):
        try:
            return self.timeseriesrecord_set.latest().__str__(timezone=timezone)
        except TimeseriesRecord.DoesNotExist:
            return ""

    @property
    def related_station(self):
        try:
            return Station.objects.get(id=self.timeseries_group.gentity.id)
        except Station.DoesNotExist:
            return None

    def _invalidate_cached_data(self):
        """
        Invalidate cached data for related model instances.

        Invalidate cached values of:
         - timeseries_data from `get_data` method
         - last_update of related `Station` model instance.
         - start_date, end_date, of the related `TimeSeriesGroup` model instance.
         - start_date`, end_date of the current `Timeseries` model instance.
        """
        cached_property_names = [
            f"timeseries_data_{self.id}",
            f"timeseries_start_date_{self.id}",
            f"timeseries_end_date_{self.id}",
            f"timeseries_group_start_date_{self.timeseries_group.id}",
            f"timeseries_group_end_date_{self.timeseries_group.id}",
        ]
        if self.related_station:
            cached_property_names += [
                f"station_last_update_{self.related_station.id}",
            ]
        cache.delete_many(cached_property_names)

    def __str__(self):
        type = self.get_type_display()
        explanation = ""
        if self.type == self.AGGREGATED:
            explanation = f" ({self.time_step} {self.name})"
        elif self.name:
            explanation = f" ({self.name})"
        return f"{type}{explanation}"

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        check_time_step(self.time_step)
        super(Timeseries, self).save(force_insert, force_update, *args, **kwargs)
        self._invalidate_cached_data()


class TimeseriesRecord(models.Model):
    # Ugly primary key hack - FIX ME in Django 5.2.
    # Django does not allow composite primary keys, whereas timescaledb can't work
    # without them. Our composite primary key in this case is (timeseries, timestamp).
    # What we do is set managed=False, so that Django won't create the table itself;
    # we create it with migrations.RunSQL(). We also set "primary_key=True" in one of
    # the fields. While technically this is wrong, it fools Django into not expecting
    # an "id" field to exist, and it doesn't affect querying functionality (except in
    # one case in autoprocess.models.Aggregation._get_start_date(), see comment there).
    timeseries = models.ForeignKey(Timeseries, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(primary_key=True, verbose_name=_("Timestamp"))
    value = models.FloatField(blank=True, null=True, verbose_name=_("Value"))
    flags = models.CharField(max_length=237, blank=True, verbose_name=_("Flags"))

    class Meta:
        verbose_name = _("Time series record")
        verbose_name_plural = _("Time series records")
        managed = False
        get_latest_by = "timestamp"

    @classmethod
    def bulk_insert(cls, timeseries, htimeseries):
        record_generator = (
            TimeseriesRecord(
                timeseries_id=timeseries.id,
                timestamp=t.Index,
                value=None if np.isnan(t.value) else t.value,
                flags=t.flags,
            )
            for t in htimeseries.data.itertuples()
        )
        batch_size = 1000
        count = 0
        while True:
            batch = list(islice(record_generator, batch_size))
            if not batch:
                break
            cls.objects.bulk_create(batch, batch_size)
            count += len(batch)
        return count

    def __str__(self, timezone=None):
        if timezone is None:
            timezone = self.timeseries.timeseries_group.gentity.display_timezone
        tzinfo = ZoneInfo(timezone)
        precision = self.timeseries.timeseries_group.precision
        datestr = self.timestamp.astimezone(tzinfo).strftime("%Y-%m-%d %H:%M")
        value = "" if self.value is None else f"{self.value:.{precision}f}"
        return f"{datestr},{value},{self.flags}"
