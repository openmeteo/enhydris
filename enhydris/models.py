from collections import OrderedDict
from datetime import timedelta, timezone

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.core.files.storage import FileSystemStorage
from django.db import IntegrityError
from django.db.models.signals import post_save
from django.utils._os import abspathu
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

import iso8601
import pandas as pd
import pd2hts
from simpletail import ropen

#
# Lookups
#


class Lookup(models.Model):
    last_modified = models.DateTimeField(default=now, null=True, editable=False)
    descr = models.CharField(max_length=200, blank=True)
    descr_alt = models.CharField(max_length=200, blank=True)

    class Meta:
        abstract = True
        ordering = ("descr",)

    def __str__(self):
        return self.descr or self.descr_alt


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
    remarks_alt = models.TextField(blank=True)
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
    last_name_alt = models.CharField(max_length=100, blank=True)
    first_name_alt = models.CharField(max_length=100, blank=True)
    middle_names_alt = models.CharField(max_length=100, blank=True)
    initials_alt = models.CharField(max_length=20, blank=True)
    f_dependencies = ["Lentity"]

    class Meta:
        ordering = ("last_name", "first_name")

    def __str__(self):
        return self.last_name + " " + self.initials


post_save.connect(post_save_person_or_organization, sender=Person)


class Organization(Lentity):
    name = models.CharField(max_length=200, blank=True)
    acronym = models.CharField(max_length=50, blank=True)
    name_alt = models.CharField(max_length=200, blank=True)
    acronym_alt = models.CharField(max_length=50, blank=True)
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
    water_basin = models.ForeignKey(
        "WaterBasin", null=True, blank=True, on_delete=models.CASCADE
    )
    water_division = models.ForeignKey(
        "WaterDivision", null=True, blank=True, on_delete=models.CASCADE
    )
    political_division = models.ForeignKey(
        "PoliticalDivision", null=True, blank=True, on_delete=models.CASCADE
    )
    name = models.CharField(max_length=200, blank=True)
    short_name = models.CharField(max_length=50, blank=True)
    remarks = models.TextField(blank=True)
    name_alt = models.CharField(max_length=200, blank=True)
    short_name_alt = models.CharField(max_length=50, blank=True)
    remarks_alt = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Gentities"
        ordering = ("name",)

    def __str__(self):
        return (
            self.short_name
            or self.short_name_alt
            or self.name
            or self.name_alt
            or str(self.id)
        )


class Gpoint(Gentity):
    srid = models.IntegerField(null=True, blank=True)
    approximate = models.BooleanField(default=False)
    altitude = models.FloatField(null=True, blank=True)
    asrid = models.IntegerField(null=True, blank=True)
    f_dependencies = ["Gentity"]
    point = models.PointField(null=True, blank=True)

    def original_abscissa(self):
        if self.point and self.srid:
            (x, y) = self.point.transform(self.srid, clone=True)
            return round(x, 2) if abs(x) > 180 and abs(y) > 90 else x
        elif self.point:
            return self.point.x
        else:
            return None

    def original_ordinate(self):
        if self.point and self.srid:
            (x, y) = self.point.transform(self.srid, clone=True)
            return round(y, 2) if abs(x) > 180 and abs(y) > 90 else y
        elif self.point:
            return self.point.y
        else:
            return None


class Gline(Gentity):
    gpoint1 = models.ForeignKey(
        Gpoint, null=True, blank=True, related_name="glines1", on_delete=models.CASCADE
    )
    gpoint2 = models.ForeignKey(
        Gpoint, null=True, blank=True, related_name="glines2", on_delete=models.CASCADE
    )
    length = models.FloatField(null=True, blank=True)
    f_dependecies = ["Gentity"]
    linestring = models.LineStringField(null=True, blank=True)


class Garea(Gentity):
    area = models.FloatField(null=True, blank=True)
    f_dependencies = ["Gentity"]
    mpoly = models.MultiPolygonField(null=True, blank=True)


#
# Gentity-related models
#


class PoliticalDivision(Garea):
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE)
    code = models.CharField(max_length=5, blank=True)

    f_dependencies = ["Garea"]

    def __str__(self):
        result = super().__str__()
        if self.parent:
            result = result + ", " + self.parent.__str__()
        return result


class WaterDivision(Garea):
    f_dependencies = ["Garea"]


class WaterBasin(Garea):
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE)
    f_dependencies = ["Garea"]


class GentityAltCodeType(Lookup):
    pass


class GentityAltCode(models.Model):
    last_modified = models.DateTimeField(default=now, null=True, editable=False)
    gentity = models.ForeignKey(Gentity, on_delete=models.CASCADE)
    type = models.ForeignKey(GentityAltCodeType, on_delete=models.CASCADE)
    value = models.CharField(max_length=100)

    class Meta:
        ordering = ("type__descr", "value")

    def __str__(self):
        return self.type.descr + " " + self.value

    @property
    def related_station(self):
        try:
            return Station.objects.get(id=self.gentity.id)
        except Station.DoesNotExist:
            return None


class FileType(Lookup):
    mime_type = models.CharField(max_length=64)

    def __str__(self):
        return self.mime_type or str(self.id)


class GentityFile(models.Model):
    last_modified = models.DateTimeField(default=now, null=True, editable=False)
    gentity = models.ForeignKey(Gentity, on_delete=models.CASCADE)
    date = models.DateField(blank=True, null=True)
    file_type = models.ForeignKey(FileType, on_delete=models.CASCADE)
    content = models.FileField(upload_to="gentityfile")
    descr = models.CharField(max_length=100)
    remarks = models.TextField(blank=True)
    descr_alt = models.CharField(max_length=100)
    remarks_alt = models.TextField(blank=True)

    class Meta:
        ordering = ("descr",)

    def __str__(self):
        return self.descr or self.descr_alt or str(self.id)

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
    user = models.CharField(max_length=64)
    report = models.TextField(blank=True)
    report_alt = models.TextField(blank=True)

    class Meta:
        ordering = ["-date"]

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


class StationType(Lookup):
    pass


class Station(Gpoint):
    owner = models.ForeignKey(
        Lentity, related_name="owned_stations", on_delete=models.CASCADE
    )
    stype = models.ManyToManyField(StationType, verbose_name="type")
    is_automatic = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    overseers = models.ManyToManyField(
        Person, through="Overseer", related_name="stations_overseen"
    )
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


class Overseer(models.Model):
    last_modified = models.DateTimeField(default=now, null=True, editable=False)
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    is_current = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ("start_date", "person__last_name", "person__first_name")

    def __str__(self):
        return str(self.person)


class InstrumentType(Lookup):
    pass


class Instrument(models.Model):
    last_modified = models.DateTimeField(default=now, null=True, editable=False)
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    type = models.ForeignKey(InstrumentType, on_delete=models.CASCADE)
    manufacturer = models.CharField(max_length=50, blank=True)
    model = models.CharField(max_length=50, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    name = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
    name_alt = models.CharField(max_length=100, blank=True)
    remarks_alt = models.TextField(blank=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name or str(self.id)


#
# Time series and related models
#


class Variable(Lookup):
    pass


class UnitOfMeasurement(Lookup):
    symbol = models.CharField(max_length=50)
    variables = models.ManyToManyField(Variable)

    def __str__(self):
        if self.symbol:
            return self.symbol
        return str(self.id)


class TimeZone(models.Model):
    last_modified = models.DateTimeField(default=now, null=True, editable=False)
    code = models.CharField(max_length=50)
    utc_offset = models.SmallIntegerField()

    @property
    def as_tzinfo(self):
        return timezone(timedelta(minutes=self.utc_offset), self.code)

    def __str__(self):
        return "%s (UTC%+03d%02d)" % (
            self.code,
            (abs(self.utc_offset) / 60) * (-1 if self.utc_offset < 0 else 1),
            abs(self.utc_offset % 60),
        )

    class Meta:
        ordering = ("utc_offset",)


class TimeStep(Lookup):
    length_minutes = models.PositiveIntegerField()
    length_months = models.PositiveSmallIntegerField()

    def __str__(self):
        """Return timestep descriptions in a human readable format.
        """
        components = OrderedDict(
            [
                ("year", self.length_months // 12),
                ("month", self.length_months % 12),
                ("day", self.length_minutes // 1440),
                ("hour", (self.length_minutes % 1440) // 60),
                ("minute", self.length_minutes % 60),
            ]
        )
        result = ""
        if self.descr:
            result = self.descr + " - "
        items = [
            "{} {}(s)".format(value, key) for key, value in components.items() if value
        ]
        result += ", ".join(items)
        if result:
            return result
        else:
            return "0 minutes, 0 months"

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if not bool(self.length_minutes) ^ bool(self.length_months):
            raise IntegrityError(
                _(
                    "{} is not a valid time step; exactly one of minutes and "
                    "months must be zero"
                ).format(self.__str__())
            )
        super(TimeStep, self).save(force_insert, force_update, *args, **kwargs)


class IntervalType(Lookup):
    value = models.CharField(max_length=50)


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


class Timeseries(models.Model):
    last_modified = models.DateTimeField(default=now, null=True, editable=False)
    gentity = models.ForeignKey(
        Gentity, related_name="timeseries", on_delete=models.CASCADE
    )
    variable = models.ForeignKey(Variable, on_delete=models.CASCADE)
    unit_of_measurement = models.ForeignKey(UnitOfMeasurement, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, blank=True)
    name_alt = models.CharField(max_length=200, blank=True, default="")
    hidden = models.BooleanField(null=False, blank=False, default=False)
    precision = models.SmallIntegerField(null=True, blank=True)
    time_zone = models.ForeignKey(TimeZone, on_delete=models.CASCADE)
    remarks = models.TextField(blank=True)
    remarks_alt = models.TextField(blank=True, default="")
    instrument = models.ForeignKey(
        Instrument, null=True, blank=True, on_delete=models.CASCADE
    )
    time_step = models.ForeignKey(
        TimeStep, null=True, blank=True, on_delete=models.CASCADE
    )
    interval_type = models.ForeignKey(
        IntervalType, null=True, blank=True, on_delete=models.CASCADE
    )
    timestamp_rounding_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_(
            "For an hourly time series whose timestamps end in :00, set this "
            "to zero; if they end in :12, set it to 12. For a ten-minute time "
            "series with timestamps ending in :12, :22, :32, etc., set it to "
            "2.  For daily ending at 08:00, set it to 480. Leave empty if "
            "timestamps are irregular."
        ),
    )
    timestamp_rounding_months = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text=_(
            "Set this to zero, except for annual time series, indicating the "
            "difference from January; for example, set it to 9 if the "
            "timestamps use a hydrological year starting in October. Leave "
            "empty if timestamps are irregular."
        ),
    )
    timestamp_offset_minutes = models.IntegerField(
        null=True,
        blank=True,
        help_text=_(
            "If unsure, set this to zero. It indicates the difference of "
            "what is shown from what is meant. For example, if for an hourly "
            "time series it is -5, then 2015-10-14 11:00 means the interval "
            "from 2015-10-14 09:55 to 2015-10-14 10:55. -1440 is common for "
            "daily time series."
        ),
    )
    timestamp_offset_months = models.SmallIntegerField(
        null=True,
        blank=True,
        help_text=_(
            "If unsure, set this to 1 for monthly, 12 for annual, and zero "
            "otherwise.  For a monthly time series, an offset of -475 "
            "minutes and 1 month means that 2003-11-01 00:00 (normally "
            "shown as 2003-11) denotes the interval 2003-10-31 18:05 to "
            "2003-11-30 18:05."
        ),
    )
    datafile = models.FileField(null=True, blank=True, storage=TimeseriesStorage())
    start_date_utc = models.DateTimeField(null=True, blank=True)
    end_date_utc = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Time Series"
        verbose_name_plural = "Time Series"
        ordering = ("hidden",)

    @property
    def start_date(self):
        if self.start_date_utc is None:
            return None
        return self.start_date_utc.astimezone(tz=self.time_zone.as_tzinfo)

    @property
    def end_date(self):
        if self.end_date_utc is None:
            return None
        return self.end_date_utc.astimezone(tz=self.time_zone.as_tzinfo)

    def _set_start_and_end_date(self):
        if (not self.datafile) or (self.datafile.size < 10):
            self.start_date_utc = None
            self.end_date_utc = None
            return
        with open(self.datafile.path, "r") as f:
            self.start_date_utc = iso8601.parse_date(
                f.readline().split(",")[0], default_timezone=self.time_zone.as_tzinfo
            )
        with ropen(self.datafile.path, bufsize=80) as f:
            self.end_date_utc = iso8601.parse_date(
                f.readline().split(",")[0], default_timezone=self.time_zone.as_tzinfo
            )

    def _set_extra_timeseries_properties(self, adataframe):
        try:
            location = {
                "abscissa": self.gentity.gpoint.point[0],
                "ordinate": self.gentity.gpoint.point[1],
                "srid": self.gentity.gpoint.srid,
                "altitude": self.gentity.gpoint.altitude,
                "asrid": self.gentity.gpoint.asrid,
            }
        except TypeError:
            # TypeError occurs when self.gentity.gpoint.point is None,
            # meaning the co-ordinates aren't registered.
            location = None
        adataframe.time_step = "{},{}".format(
            self.time_step.length_minutes if self.time_step else 0,
            self.time_step.length_months if self.time_step else 0,
        )
        adataframe.timestamp_rounding = (
            None
            if None in (self.timestamp_rounding_minutes, self.timestamp_rounding_months)
            else "{},{}".format(
                self.timestamp_rounding_minutes, self.timestamp_rounding_months
            )
        )
        adataframe.timestamp_offset = (
            None
            if None in (self.timestamp_offset_minutes, self.timestamp_offset_months)
            else "{},{}".format(
                self.timestamp_offset_minutes, self.timestamp_offset_months
            )
        )
        adataframe.interval_type = (
            None if not self.interval_type else self.interval_type.value.lower()
        )
        adataframe.unit = self.unit_of_measurement.symbol
        adataframe.title = self.name
        sign = -1 if self.time_zone.utc_offset < 0 else 1
        adataframe.timezone = "{} (UTC{:+03d}{:02d})".format(
            self.time_zone.code,
            abs(self.time_zone.utc_offset) // 60 * sign,
            abs(self.time_zone.utc_offset) % 60,
        )
        adataframe.variable = self.variable.descr
        adataframe.precision = self.precision
        adataframe.location = location
        adataframe.comment = "%s\n\n%s" % (self.gentity.name, self.remarks)

    def get_data(self, start_date=None, end_date=None):
        if self.datafile:
            with open(self.datafile.path, "r", newline="\n") as f:
                result = pd2hts.read(f, start_date=start_date, end_date=end_date)
        else:
            result = pd.DataFrame()
        self._set_extra_timeseries_properties(result)
        return result

    def set_data(self, data):
        adataframe = pd2hts.read(data)
        if not self.datafile:
            self.datafile.name = "{:010}".format(self.id)
        with open(self.datafile.path, "w") as f:
            pd2hts.write(adataframe, f)
        self.save()
        return len(adataframe)

    def append_data(self, data):
        if not self.datafile:
            return self.set_data(data)
        adataframe = pd2hts.read(data)
        if not len(adataframe):
            return 0
        with ropen(self.datafile.path, bufsize=80) as f:
            old_data_end_date = iso8601.parse_date(f.readline().split(",")[0]).replace(
                tzinfo=None
            )
        new_data_start_date = adataframe.index[0]
        if old_data_end_date >= new_data_start_date:
            raise IntegrityError(
                (
                    "Cannot append time series: "
                    "its first record ({}) has a date earlier than the last "
                    "record ({}) of the timeseries to append to."
                ).format(new_data_start_date, old_data_end_date)
            )
        with open(self.datafile.path, "a") as f:
            pd2hts.write(adataframe, f)
        self.save()
        return len(adataframe)

    def get_first_line(self):
        if not self.datafile or self.datafile.size < 10:
            return ""
        with open(self.datafile.path, "r") as f:
            return f.readline()

    def get_last_line(self):
        if not self.datafile or self.datafile.size < 10:
            return ""
        with ropen(self.datafile.path, bufsize=80) as f:
            lastline = f.readline()
            return lastline if len(lastline) > 5 else f.readline()

    @property
    def related_station(self):
        try:
            return Station.objects.get(id=self.gentity.id)
        except Station.DoesNotExist:
            return None

    def __str__(self):
        return self.name

    def _check_that_offset_and_rounding_are_null_when_time_step_is_null(self):
        if self.time_step:
            return
        one_of_them_is_not_none = (
            self.timestamp_rounding_minutes is not None
            or self.timestamp_rounding_months is not None
            or self.timestamp_offset_minutes is not None
            or self.timestamp_offset_months is not None
        )
        if one_of_them_is_not_none:
            raise IntegrityError(
                _(
                    "Invalid time step: if time_step is null, "
                    "rounding and offset must also be null"
                )
            )

    def _check_integrity_of_offset_and_rounding_when_time_step_is_not_null(self):
        if not self.time_step:
            return
        an_offset_is_none = (
            self.timestamp_offset_minutes is None
            or self.timestamp_offset_months is None
        )
        if an_offset_is_none:
            raise IntegrityError(
                _(
                    "Invalid time step: if time_step is not "
                    "null, offset must be provided"
                )
            )
        roundings_are_inconsistent = (
            self.timestamp_rounding_minutes is None
            and self.timestamp_rounding_months is not None
        ) or (
            self.timestamp_rounding_minutes is not None
            and self.timestamp_rounding_months is None
        )
        if roundings_are_inconsistent:
            raise IntegrityError(
                _("Invalid time step: roundings must be both null or not null")
            )

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        self._check_that_offset_and_rounding_are_null_when_time_step_is_null()
        self._check_integrity_of_offset_and_rounding_when_time_step_is_not_null()
        self._set_start_and_end_date()
        super(Timeseries, self).save(force_insert, force_update, *args, **kwargs)
