from io import StringIO
from itertools import islice
from os.path import abspath

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
    if unit not in ("min", "H", "D", "M", "Y"):
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

    class Meta:
        verbose_name = pgettext_lazy("Singular", "Time series")
        verbose_name_plural = pgettext_lazy("Plural", "Time series")
        ordering = ("type",)
        unique_together = ["timeseries_group", "type", "time_step"]
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
                    self.timeseries_group.time_zone.as_tzinfo
                )
            except TimeseriesRecord.DoesNotExist:
                return None

        return cache.get_or_set(f"timeseries_start_date_{self.id}", get_start_date)

    @property
    def end_date(self):
        def get_end_date():
            try:
                return self.timeseriesrecord_set.latest().timestamp.astimezone(
                    self.timeseries_group.time_zone.as_tzinfo
                )
            except TimeseriesRecord.DoesNotExist:
                return None

        return cache.get_or_set(f"timeseries_end_date_{self.id}", get_end_date)

    @property
    def start_date_naive(self):
        def get_start_date_naive():
            try:
                return (
                    self.timeseriesrecord_set.earliest()
                    .timestamp.astimezone(self.timeseries_group.time_zone.as_tzinfo)
                    .replace(tzinfo=None)
                )
            except TimeseriesRecord.DoesNotExist:
                return None

        return cache.get_or_set(
            f"timeseries_start_date_naive_{self.id}", get_start_date_naive
        )

    @property
    def end_date_naive(self):
        def get_end_date_naive():
            try:
                return (
                    self.timeseriesrecord_set.latest()
                    .timestamp.astimezone(self.timeseries_group.time_zone.as_tzinfo)
                    .replace(tzinfo=None)
                )
            except TimeseriesRecord.DoesNotExist:
                return None

        return cache.get_or_set(
            f"timeseries_end_date_naive_{self.id}", get_end_date_naive
        )

    def _set_extra_timeseries_properties(self, ahtimeseries):
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
        sign = -1 if self.timeseries_group.time_zone.utc_offset < 0 else 1
        ahtimeseries.timezone = "{} (UTC{:+03d}{:02d})".format(
            self.timeseries_group.time_zone.code,
            abs(self.timeseries_group.time_zone.utc_offset) // 60 * sign,
            abs(self.timeseries_group.time_zone.utc_offset) % 60,
        )
        ahtimeseries.variable = self.timeseries_group.variable.descr
        ahtimeseries.precision = self.timeseries_group.precision
        ahtimeseries.location = location
        ahtimeseries.comment = (
            f"{self.timeseries_group.gentity.name}\n\n{self.timeseries_group.remarks}"
        )

    def get_data(self, start_date=None, end_date=None):
        data = cache.get_or_set(f"timeseries_data_{self.id}", self._get_all_data_as_pd)
        if start_date:
            start_date = start_date.astimezone(
                self.timeseries_group.time_zone.as_tzinfo
            )
            start_date = start_date.replace(tzinfo=None)
        if end_date:
            end_date = end_date.astimezone(self.timeseries_group.time_zone.as_tzinfo)
            end_date = end_date.replace(tzinfo=None)
        data = data.loc[start_date:end_date]
        result = HTimeseries(data)
        self._set_extra_timeseries_properties(result)
        return result

    def _get_all_data_as_pd(self):
        tzoffsetstring = self._get_tzoffsetstring_for_pg()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT STRING_AGG(
                    TO_CHAR(timestamp at time zone %s, 'YYYY-MM-DD HH24:MI')
                        || ','
                        || CASE WHEN value is NULL THEN DOUBLE PRECISION 'NaN'
                           ELSE value END
                        || ','
                        || flags,
                    E'\n'
                    ORDER BY timestamp
                ) || E'\n'
                FROM enhydris_timeseriesrecord
                WHERE timeseries_id=%s;
                """,
                [tzoffsetstring, self.id],
            )
            return HTimeseries(StringIO(cursor.fetchone()[0])).data

    def _get_tzoffsetstring_for_pg(self):
        # In tz offset supplied to PostgreSQL, use + for west of Greenwich because of
        # POSIX madness.
        tzoffsetstring = self.timeseries_group.time_zone.offset_string
        sign = "-" if tzoffsetstring[0] == "+" else "+"
        hours = tzoffsetstring[1:3]
        minutes = tzoffsetstring[3:]
        return f"{sign}{hours}:{minutes}"

    def set_data(self, data):
        self.timeseriesrecord_set.all().delete()
        return self.append_data(data)

    def append_data(self, data):
        ahtimeseries = self._get_htimeseries_from_data(data)
        self._check_new_data_is_newer(ahtimeseries)
        result = TimeseriesRecord.bulk_insert(self, ahtimeseries)
        self.save()
        return result

    def _check_new_data_is_newer(self, ahtimeseries):
        if not len(ahtimeseries.data):
            return 0
        new_data_start_date = ahtimeseries.data.index[0]
        if self.end_date is not None and self.end_date_naive >= new_data_start_date:
            raise IntegrityError(
                (
                    "Cannot append time series: "
                    "its first record ({}) has a date earlier than the last "
                    "record ({}) of the timeseries to append to."
                ).format(new_data_start_date, self.end_date_naive)
            )

    def _get_htimeseries_from_data(self, data):
        if isinstance(data, HTimeseries):
            return data
        else:
            return HTimeseries(data)

    def get_last_record_as_string(self):
        try:
            return str(self.timeseriesrecord_set.latest())
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
         - last_update, last_update_naive of related `Station` model instance.
         - start_date, start_date_naive, end_date, end_date_naive of
            the related `TimeSeriesGroup` model instance.
         - start_date`, start_date_naive, end_date, end_date_naive of
           the current `Timeseries` model instance.
        """
        cached_property_names = [
            f"timeseries_data_{self.id}",
            f"timeseries_start_date_{self.id}",
            f"timeseries_end_date_{self.id}",
            f"timeseries_start_date_naive_{self.id}",
            f"timeseries_end_date_naive_{self.id}",
            f"timeseries_group_start_date_{self.timeseries_group.id}",
            f"timeseries_group_end_date_{self.timeseries_group.id}",
            f"timeseries_group_start_date_naive_{self.timeseries_group.id}",
            f"timeseries_group_end_date_naive_{self.timeseries_group.id}",
        ]
        if self.related_station:
            cached_property_names += [
                f"station_last_update_{self.related_station.id}",
                f"station_last_update_naive_{self.related_station.id}",
            ]
        cache.delete_many(cached_property_names)

    def __str__(self):
        result = self.get_type_display()
        if self.type == self.AGGREGATED:
            result = f"{result} ({self.time_step})"
        return result

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        check_time_step(self.time_step)
        super(Timeseries, self).save(force_insert, force_update, *args, **kwargs)
        self._invalidate_cached_data()


class TimeseriesRecord(models.Model):
    # Ugly primary key hack.
    # Django does not allow composite primary keys, whereas timescaledb can't work
    # without them. Our composite primary key in this case is (timeseries, timestamp).
    # What we do is set managed=False, so that Django won't create the table itself;
    # we create it with migrations.RunSQL(). We also set "primary_key=True" in one of
    # the fields. While technically this is wrong, it fools Django into not expecting
    # an "id" field to exist, and it doesn't affect querying functionality.
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
        tzinfo = timeseries.timeseries_group.time_zone.as_tzinfo
        record_generator = (
            TimeseriesRecord(
                timeseries_id=timeseries.id,
                timestamp=t.Index.to_pydatetime().replace(tzinfo=tzinfo),
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

    def __str__(self):
        tzinfo = self.timeseries.timeseries_group.time_zone.as_tzinfo
        precision = self.timeseries.timeseries_group.precision
        datestr = self.timestamp.astimezone(tzinfo).strftime("%Y-%m-%d %H:%M")
        value = "" if self.value is None else f"{self.value:.{precision}f}"
        return f"{datestr},{value},{self.flags}"
