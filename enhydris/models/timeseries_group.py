from datetime import timedelta, timezone

from django.conf import settings
from django.contrib.gis.db import models
from django.core.cache import cache
from django.db.models import FilteredRelation, Q
from django.db.models.functions import Coalesce
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from parler.managers import TranslatableManager
from parler.models import TranslatableModel, TranslatedFields
from parler.utils import get_active_language_choices

from .base import Lookup
from .gentity import Gentity


class VariableManager(TranslatableManager):
    def get_queryset(self):
        try:
            langs = get_active_language_choices()
            lang1 = langs[0]
            lang2 = langs[1] if len(langs) > 1 else "nonexistent"
        except ValueError:
            lang1 = settings.LANGUAGE_CODE
            try:
                lang2 = settings.LANGUAGES[1][0]
            except IndexError:
                lang2 = "nonexistent"
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
    translations = TranslatedFields(
        descr=models.CharField(
            max_length=200, blank=True, verbose_name=_("Description")
        )
    )

    objects = VariableManager()

    class Meta:
        verbose_name = _("Variable")
        verbose_name_plural = _("Variables")

    def __str__(self):
        # For an explanation of this, see
        # enhydris.tests.test_models.VariableTestCase.test_translation_bug()
        result = self.descr
        if result is None:
            return self.translations.first().descr
        return result


class UnitOfMeasurement(Lookup):
    symbol = models.CharField(max_length=50, verbose_name=_("Symbol"))
    variables = models.ManyToManyField(Variable)

    def __str__(self):
        if self.symbol:
            return self.symbol
        return str(self.id)

    class Meta:
        verbose_name = _("Unit of measurement")
        verbose_name_plural = _("Units of measurement")
        ordering = ["symbol"]


class TimeZone(models.Model):
    last_modified = models.DateTimeField(default=now, null=True, editable=False)
    code = models.CharField(max_length=50)
    utc_offset = models.SmallIntegerField(verbose_name=_("UTC offset"))

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
        verbose_name = _("Time zone")
        verbose_name_plural = _("Time zones")
        ordering = ("utc_offset",)


class TimeseriesGroup(models.Model):
    last_modified = models.DateTimeField(default=now, null=True, editable=False)
    gentity = models.ForeignKey(Gentity, on_delete=models.CASCADE)
    variable = models.ForeignKey(
        Variable, on_delete=models.CASCADE, verbose_name=_("Variable")
    )
    unit_of_measurement = models.ForeignKey(
        UnitOfMeasurement,
        on_delete=models.CASCADE,
        verbose_name=_("Unit of measurement"),
    )
    name = models.CharField(
        max_length=200,
        blank=True,
        help_text=_(
            "In most cases, you want to leave this blank, and the name of the time "
            'series group will be the name of the variable, such as "Temperature". '
            "However, if you have two groups with the same variable (e.g. if you have "
            "two temperature sensors), specify a name to tell them apart."
        ),
        verbose_name=_("Name"),
    )
    hidden = models.BooleanField(
        null=False, blank=False, default=False, verbose_name=_("Hidden")
    )
    precision = models.SmallIntegerField(
        help_text=_(
            "The number of decimal digits to which the values of the time series "
            "will be rounded. It's usually positive, but it can be zero or negative; "
            "for example, for humidity it is usually zero; for wind direction in "
            "degrees, depending on the sensor, you might want to specify "
            "precision -1, which means the value will be 10, or 20, or 30, etc. This "
            "only affects the rounding of values when the time series is retrieved; "
            "values are always stored with all the decimal digits provided."
        ),
        verbose_name=_("Precision"),
    )
    time_zone = models.ForeignKey(
        TimeZone, on_delete=models.CASCADE, verbose_name=_("Time zone")
    )
    remarks = models.TextField(blank=True, verbose_name=_("Remarks"))

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

    class Meta:
        verbose_name = _("Time series group")
        verbose_name_plural = _("Time series groups")
        ordering = ["gentity", "name"]

    def __str__(self):
        return self.get_name()

    @cached_property
    def default_timeseries(self):
        from .timeseries import Timeseries

        return (
            self._get_timeseries(Timeseries.REGULARIZED)
            or self._get_timeseries(Timeseries.CHECKED)
            or self._get_timeseries(Timeseries.INITIAL)
        )

    def _get_timeseries(self, type):
        # We don't just do self.timeseries_set.get(type=type) because sometimes we have
        # the timeseries prefetched and this would cause another query.
        for timeseries in self.timeseries_set.all():
            if timeseries.type == type:
                return timeseries

    @property
    def start_date(self):
        def get_start_date():
            if self.default_timeseries:
                return self.default_timeseries.start_date

        return cache.get_or_set(
            f"timeseries_group_start_date_{self.id}", get_start_date
        )

    @property
    def end_date(self):
        def get_end_date():
            if self.default_timeseries:
                return self.default_timeseries.end_date

        return cache.get_or_set(f"timeseries_group_end_date_{self.id}", get_end_date)

    @property
    def start_date_naive(self):
        result = self.start_date

        def get_start_date_naive():
            if result is not None:
                return result.replace(tzinfo=None)

        return cache.get_or_set(
            f"timeseries_start_date_naive_{self.id}", get_start_date_naive
        )

    @property
    def end_date_naive(self):
        result = self.end_date

        def get_end_date():
            if result is not None:
                return result.replace(tzinfo=None)

        return cache.get_or_set(f"timeseries_end_date_naive_{self.id}", get_end_date)
