from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.gis.db import models
from django.core.cache import cache
from django.db.models import FilteredRelation, Q, Value
from django.db.models.functions import Coalesce
from django.db.models.manager import Manager
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

from .base import Lookup
from .gentity import Gentity

if TYPE_CHECKING:
    from enhydris.models import Timeseries


class VariableManager(models.Manager["Variable"]):
    def get_queryset(self):
        lang1 = get_language()
        lang2 = settings.LANGUAGE_CODE
        return (
            super()
            .get_queryset()
            .annotate(t1=self._filtered_relation(lang1))
            .annotate(t2=self._filtered_relation(lang2))
            .annotate(sort_key=Coalesce("t1__descr", "t2__descr", Value("")))
            .order_by("sort_key")
        )

    def _filtered_relation(self, language_code: str | None):
        return FilteredRelation(
            "translations", condition=Q(translations__language_code=language_code)
        )


class Variable(models.Model):
    translations: Manager["VariableTranslation"]

    last_modified = models.DateTimeField(default=now, null=True, editable=False)

    objects = VariableManager()

    class Meta:
        verbose_name = _("Variable")
        verbose_name_plural = _("Variables")

    @property
    def descr(self) -> str:
        # Return the VariableManager's annotation if it exists.
        if "sort_key" in vars(self):
            return vars(self)["sort_key"]

        language_code = get_language()
        descr_cache = vars(self).setdefault("_descr_cache", {})
        if language_code in descr_cache:
            return descr_cache[language_code]
        prefetched_translations = getattr(self, "prefetched_translations", None)
        if prefetched_translations is not None:
            for preferred_language in (language_code, settings.LANGUAGE_CODE):
                for t in prefetched_translations:
                    if t.language_code == preferred_language:
                        descr_cache[language_code] = t.descr
                        return t.descr
            descr_cache[language_code] = ""
            return ""

        try:
            descr = self.translations.get(language_code=language_code).descr
        except VariableTranslation.DoesNotExist:
            try:
                descr = self.translations.get(
                    language_code=settings.LANGUAGE_CODE
                ).descr
            except VariableTranslation.DoesNotExist:
                descr = ""
        descr_cache[language_code] = descr
        return descr

    def __str__(self):
        return self.descr


class VariableTranslation(models.Model):
    variable = models.ForeignKey(
        Variable,
        on_delete=models.CASCADE,
        related_name="translations",
        verbose_name=_("Variable"),
    )
    language_code = models.CharField(max_length=15, verbose_name=_("Language"))
    descr = models.CharField(max_length=200, verbose_name=_("Description"))

    class Meta:
        unique_together = (
            (
                "variable",
                "language_code",
            ),
        )


class UnitOfMeasurement(Lookup):
    symbol = models.CharField(max_length=50, verbose_name=_("Symbol"))
    variables = models.ManyToManyField(Variable)

    def __str__(self):
        if self.symbol:
            return self.symbol
        return str(self.pk)

    class Meta:  # type: ignore
        verbose_name = _("Unit of measurement")
        verbose_name_plural = _("Units of measurement")
        ordering = ["symbol"]


class TimeseriesGroup(models.Model):
    timeseries_set: Manager["Timeseries"]

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
    remarks = models.TextField(blank=True, verbose_name=_("Remarks"))

    def get_name(self):
        if self.name:
            return self.name
        return self.variable.descr

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

    def _get_timeseries(self, type: int):
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
            f"timeseries_group_start_date_{self.pk}", get_start_date
        )

    @property
    def end_date(self):
        def get_end_date():
            if self.default_timeseries:
                return self.default_timeseries.end_date

        return cache.get_or_set(f"timeseries_group_end_date_{self.pk}", get_end_date)
