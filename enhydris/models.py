from datetime import timedelta, timezone
from io import StringIO
from itertools import islice

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.core.cache import cache
from django.core.files.storage import FileSystemStorage
from django.db import IntegrityError, connection
from django.db.models import FilteredRelation, Q
from django.db.models.functions import Coalesce
from django.db.models.signals import post_save
from django.utils._os import abspathu
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

import numpy as np
from htimeseries import HTimeseries
from parler.managers import TranslatableManager
from parler.models import TranslatableModel, TranslatedFields
from parler.utils import get_active_language_choices


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


#
# Lookups
#


class Lookup(models.Model):
    last_modified = models.DateTimeField(default=now, null=True, editable=False)
    descr = models.CharField(max_length=200, blank=True)

    class Meta:
        abstract = True
        ordering = ("descr",)

    def __str__(self):
        return self.descr


#
# Lentity and descendants
#


def post_save_person_or_organization(sender, **kwargs):
    """Create and save ordering_string upon saving a person or organization.

    When we want to sort a list of lentities that has both people and organizations,
    we need a common sorting field. We calculate and save this sorting field upon
    saving the person or organization.
    """
    instance = kwargs["instance"]
    try:
        string = instance.name
    except AttributeError:
        string = "{} {}".format(instance.last_name, instance.first_name)
    lentity = instance.lentity_ptr
    lentity.ordering_string = string
    super(Lentity, lentity).save()


class Lentity(models.Model):
    last_modified = models.DateTimeField(default=now, null=True, editable=False)
    remarks = models.TextField(blank=True)
    ordering_string = models.CharField(
        max_length=255, null=True, blank=True, editable=False
    )

    class Meta:
        verbose_name_plural = "Lentities"
        ordering = ("ordering_string",)

    def __str__(self):
        return self.ordering_string or str(self.pk)


class Person(Lentity):
    last_name = models.CharField(max_length=100, blank=True)
    first_name = models.CharField(max_length=100, blank=True)
    middle_names = models.CharField(max_length=100, blank=True)
    initials = models.CharField(max_length=20, blank=True)
    f_dependencies = ["Lentity"]

    class Meta:
        ordering = ("last_name", "first_name")

    def __str__(self):
        return self.last_name + " " + self.initials


post_save.connect(post_save_person_or_organization, sender=Person)


class Organization(Lentity):
    name = models.CharField(max_length=200, blank=True)
    acronym = models.CharField(max_length=50, blank=True)
    f_dependencies = ["Lentity"]

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.acronym if self.acronym else self.name


post_save.connect(post_save_person_or_organization, sender=Organization)


#
# Gentity and direct descendants
#


class Gentity(models.Model):
    last_modified = models.DateTimeField(default=now, null=True, editable=False)
    name = models.CharField(max_length=200, blank=True)
    code = models.CharField(max_length=50, blank=True)
    remarks = models.TextField(blank=True)
    geom = models.GeometryField()

    class Meta:
        verbose_name_plural = "Gentities"
        ordering = ("name",)

    def __str__(self):
        return self.name or self.code or str(self.id)


class Gpoint(Gentity):
    original_srid = models.IntegerField(null=True, blank=True)
    altitude = models.FloatField(null=True, blank=True)
    f_dependencies = ["Gentity"]

    def original_abscissa(self):
        if self.original_srid:
            (x, y) = self.geom.transform(self.original_srid, clone=True)
            return round(x, 2) if abs(x) > 180 and abs(y) > 90 else x
        else:
            return self.geom.x

    def original_ordinate(self):
        if self.original_srid:
            (x, y) = self.geom.transform(self.original_srid, clone=True)
            return round(y, 2) if abs(x) > 180 and abs(y) > 90 else y
        else:
            return self.geom.y


class GareaCategory(Lookup):
    class Meta:
        verbose_name = "Garea categories"
        verbose_name_plural = "Garea categories"


class Garea(Gentity):
    category = models.ForeignKey(GareaCategory, on_delete=models.CASCADE)
    f_dependencies = ["Gentity"]


#
# Gentity-related models
#


class GentityFile(models.Model):
    last_modified = models.DateTimeField(default=now, null=True, editable=False)
    gentity = models.ForeignKey(Gentity, on_delete=models.CASCADE)
    date = models.DateField(blank=True, null=True)
    content = models.FileField(upload_to="gentityfile")
    descr = models.CharField(max_length=100)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ("descr",)
        verbose_name = _("File")
        verbose_name_plural = _("Files")

    def __str__(self):
        return self.descr or str(self.id)

    @property
    def related_station(self):
        try:
            return Station.objects.get(id=self.gentity.id)
        except Station.DoesNotExist:
            return None


class EventType(Lookup):
    pass


class GentityEvent(models.Model):
    last_modified = models.DateTimeField(default=now, null=True, editable=False)
    gentity = models.ForeignKey(Gentity, on_delete=models.CASCADE)
    date = models.DateField()
    type = models.ForeignKey(EventType, on_delete=models.CASCADE)
    user = models.CharField(blank=True, max_length=64)
    report = models.TextField(blank=True)

    class Meta:
        ordering = ["-date"]
        verbose_name = _("Log entry")
        verbose_name_plural = _("Log entries")

    def __str__(self):
        return str(self.date) + " " + self.type.__str__()

    @property
    def related_station(self):
        try:
            return Station.objects.get(id=self.gentity.id)
        except Station.DoesNotExist:
            return None


#
# Station and its related models
#


class Station(Gpoint):
    owner = models.ForeignKey(
        Lentity, related_name="owned_stations", on_delete=models.CASCADE
    )
    is_automatic = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    overseer = models.CharField(max_length=30, blank=True)
    copyright_holder = models.TextField()
    copyright_years = models.CharField(max_length=10)
    # The following two fields are only useful when USERS_CAN_ADD_CONTENT
    # is set.
    creator = models.ForeignKey(
        User,
        null=True,
        blank=True,
        related_name="created_stations",
        on_delete=models.CASCADE,
    )
    maintainers = models.ManyToManyField(
        User, blank=True, related_name="maintaining_stations"
    )

    f_dependencies = ["Gpoint"]

    @property
    def last_update_naive(self):
        result = self.last_update
        if result is not None:
            result = result.replace(tzinfo=None)
        return result

    @property
    def last_update(self):
        timeseries = Timeseries.objects.filter(timeseries_group__gentity_id=self.id)
        result = None
        for t in timeseries:
            t_end_date = t.end_date
            if t_end_date is None:
                continue
            if result is None or t_end_date > result:
                result = t_end_date
        return result


#
# Time series and related models
#


class VariableManager(TranslatableManager):
    def get_queryset(self):
        langs = get_active_language_choices()
        lang1 = langs[0]
        lang2 = langs[1] if len(langs) > 1 else "nonexistent"
        return (
            super()
            .get_queryset()
            .annotate(
                translation1=FilteredRelation(
                    "translations", condition=Q(translations__language_code=lang1)
                )
            )
            .annotate(
                translation2=FilteredRelation(
                    "translations", condition=Q(translations__language_code=lang2)
                )
            )
            .annotate(descr=Coalesce("translation1__descr", "translation2__descr"))
            .order_by("descr")
        )


class Variable(TranslatableModel):
    last_modified = models.DateTimeField(default=now, null=True, editable=False)
    translations = TranslatedFields(descr=models.CharField(max_length=200, blank=True))

    objects = VariableManager()

    def __str__(self):
        # For an explanation of this, see
        # enhydris.tests.test_models.VariableTestCase.test_translation_bug()
        result = self.descr
        if result is None:
            return self.translations.first().descr
        return result


class UnitOfMeasurement(Lookup):
    symbol = models.CharField(max_length=50)
    variables = models.ManyToManyField(Variable)

    def __str__(self):
        if self.symbol:
            return self.symbol
        return str(self.id)

    class Meta:
        ordering = ["symbol"]


class TimeZone(models.Model):
    last_modified = models.DateTimeField(default=now, null=True, editable=False)
    code = models.CharField(max_length=50)
    utc_offset = models.SmallIntegerField()

    @property
    def as_tzinfo(self):
        return timezone(timedelta(minutes=self.utc_offset), self.code)

    def __str__(self):
        return f"{self.code} (UTC{self.offset_string})"

    @property
    def offset_string(self):
        hours = (abs(self.utc_offset) // 60) * (-1 if self.utc_offset < 0 else 1)
        minutes = abs(self.utc_offset % 60)
        return f"{hours:+03}{minutes:02}"

    class Meta:
        ordering = ("utc_offset",)


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
        self.location = abspathu(settings.ENHYDRIS_TIMESERIES_DATA_DIR)
        return super().path(name)


class TimeseriesGroup(models.Model):
    last_modified = models.DateTimeField(default=now, null=True, editable=False)
    gentity = models.ForeignKey(Gentity, on_delete=models.CASCADE)
    variable = models.ForeignKey(Variable, on_delete=models.CASCADE)
    unit_of_measurement = models.ForeignKey(UnitOfMeasurement, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=200,
        blank=True,
        help_text=_(
            "In most cases, you want to leave this blank, and the name of the time "
            'series group will be the name of the variable, such as "Temperature". '
            "However, if you have two groups with the same variable (e.g. if you have "
            "two temperature sensors), specify a name to tell them apart."
        ),
    )
    hidden = models.BooleanField(null=False, blank=False, default=False)
    precision = models.SmallIntegerField(
        help_text=_(
            "The number of decimal digits to which the values of the time series "
            "will be rounded. It's usually positive, but it can be zero or negative; "
            "for example, for humidity it is usually zero; for wind direction in "
            "degrees, depending on the sensor, you might want to specify "
            "precision -1, which means the value will be 10, or 20, or 30, etc. This "
            "only affects the rounding of values when the time series is retrieved; "
            "values are always stored with all the decimal digits provided."
        )
    )
    time_zone = models.ForeignKey(TimeZone, on_delete=models.CASCADE)
    remarks = models.TextField(blank=True)

    def get_name(self):
        if self.name:
            return self.name
        try:
            return self.variable.descr
        except ValueError:
            # Sometimes the current language is set to null; this happens particularly
            # when the Django admin is recording what changes happened to an object (see
            # django.contrib.admin.utils.construct_change_message). In that case,
            # django-parler raises a ValueError exception when we attempt to access
            # self.variable.descr. Not sure whether this is a Django problem or a
            # django-parler problem. Working around by returning the group id.
            return f"Timeseries group {self.id}"

    def __str__(self):
        return self.get_name()

    @cached_property
    def default_timeseries(self):
        return (
            self._get_timeseries(Timeseries.REGULARIZED)
            or self._get_timeseries(Timeseries.CHECKED)
            or self._get_timeseries(Timeseries.RAW)
            or self._get_timeseries(Timeseries.PROCESSED)
        )

    def _get_timeseries(self, type):
        # We don't just do self.timeseries_set.get(type=type) because sometimes we have
        # the timeseries prefetched and this would cause another query.
        for timeseries in self.timeseries_set.all():
            if timeseries.type == type:
                return timeseries

    @property
    def start_date(self):
        if self.default_timeseries:
            return self.default_timeseries.start_date

    @property
    def end_date(self):
        if self.default_timeseries:
            return self.default_timeseries.end_date

    @property
    def start_date_naive(self):
        result = self.start_date
        if result is not None:
            return result.replace(tzinfo=None)

    @property
    def end_date_naive(self):
        result = self.end_date
        if result is not None:
            return result.replace(tzinfo=None)


class Timeseries(models.Model):
    RAW = 100
    PROCESSED = 150
    CHECKED = 200
    REGULARIZED = 300
    AGGREGATED = 400
    TIMESERIES_TYPES = (
        (RAW, _("Raw")),
        (PROCESSED, _("Processed")),
        (CHECKED, _("Checked")),
        (REGULARIZED, _("Regularized")),
        (AGGREGATED, _("Aggregated")),
    )
    last_modified = models.DateTimeField(default=now, null=True, editable=False)
    timeseries_group = models.ForeignKey(TimeseriesGroup, on_delete=models.CASCADE)
    type = models.PositiveSmallIntegerField(choices=TIMESERIES_TYPES)
    time_step = models.CharField(
        max_length=7,
        blank=True,
        help_text=_(
            'E.g. "10min", "H" (hourly), "D" (daily), "M" (monthly), "Y" (yearly). '
            "More specifically, it's an optional number plus a unit, with no space in "
            "between. The units available are min, H, D, M, Y. Leave empty if the time "
            "series is irregular."
        ),
    )

    class Meta:
        verbose_name = "Time series"
        verbose_name_plural = "Time series"
        ordering = ("type",)
        unique_together = ["timeseries_group", "type", "time_step"]
        constraints = [
            models.UniqueConstraint(
                fields=["timeseries_group"],
                condition=models.Q(type__in=(100, 150)),
                name="only_one_raw_or_processed_timeseries_per_group",
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
        try:
            return self.timeseriesrecord_set.earliest().timestamp.astimezone(
                self.timeseries_group.time_zone.as_tzinfo
            )
        except TimeseriesRecord.DoesNotExist:
            return None

    @property
    def end_date(self):
        try:
            return self.timeseriesrecord_set.latest().timestamp.astimezone(
                self.timeseries_group.time_zone.as_tzinfo
            )
        except TimeseriesRecord.DoesNotExist:
            return None

    @property
    def start_date_naive(self):
        try:
            return (
                self.timeseriesrecord_set.earliest()
                .timestamp.astimezone(self.timeseries_group.time_zone.as_tzinfo)
                .replace(tzinfo=None)
            )
        except TimeseriesRecord.DoesNotExist:
            return None

    @property
    def end_date_naive(self):
        try:
            return (
                self.timeseriesrecord_set.latest()
                .timestamp.astimezone(self.timeseries_group.time_zone.as_tzinfo)
                .replace(tzinfo=None)
            )
        except TimeseriesRecord.DoesNotExist:
            return None

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
                        || ',' || value || ',' || flags,
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

    def __str__(self):
        result = self.get_type_display()
        if self.type == self.AGGREGATED:
            result = f"{result} ({self.time_step})"
        return result

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        check_time_step(self.time_step)
        super(Timeseries, self).save(force_insert, force_update, *args, **kwargs)
        cache.delete(f"timeseries_data_{self.id}")


class TimeseriesRecord(models.Model):
    # Ugly primary key hack.
    # Django does not allow composite primary keys, whereas timescaledb can't work
    # without them. Our composite primary key in this case is (timeseries, timestamp).
    # What we do is set managed=False, so that Django won't create the table itself;
    # we create it with migrations.RunSQL(). We also set "primary_key=True" in one of
    # the fields. While technically this is wrong, it fools Django into not expecting
    # an "id" field to exist, and it doesn't affect querying functionality.
    timeseries = models.ForeignKey(Timeseries, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(primary_key=True)
    value = models.FloatField(blank=True, null=True)
    flags = models.CharField(max_length=237, blank=True)

    class Meta:
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
