import csv
import datetime as dt
import logging
import re
from io import StringIO

from django.db import DataError, IntegrityError, models, transaction
from django.db.models.signals import post_delete
from django.utils.translation import gettext_lazy as _

import numpy as np
import pandas as pd
from haggregate import RegularizationMode as RM
from haggregate import RegularizeError, aggregate, regularize
from htimeseries import HTimeseries
from rocc import Threshold, rocc

from enhydris.models import Timeseries, TimeseriesGroup, check_time_step

from . import tasks


class AutoProcess(models.Model):
    timeseries_group = models.ForeignKey(TimeseriesGroup, on_delete=models.CASCADE)

    class Meta:
        db_table = "enhydris_autoprocess_autoprocess"
        verbose_name_plural = _("Auto processes")

    def execute(self):
        try:
            result = self.process_timeseries()
            self.target_timeseries.append_data(result)
        except Exception as e:
            msg = (
                f"{e.__class__.__name__} while executing AutoProcess with "
                f"id={self.id}: {str(e)}"
            )
            raise RuntimeError(msg)

    @property
    def htimeseries(self):
        if not hasattr(self, "_htimeseries"):
            self._htimeseries = self.source_timeseries.get_data(
                start_date=self._get_start_date()
            )
        return self._htimeseries

    @property
    def as_specific_instance(self):
        """Return the AutoProcess as an instance of the appropriate subclass.

        AutoProcess is essentially an abstract base class; its instances are always one
        of its subclasses, i.e. Checks, CurveInterpolation, or Aggregation. Sometimes we
        might have an AutoProcess instance without yet knowing what subclass it is; in
        that case, "myinstance.as_specific_instance" is the subclass.

        The method works by following the reverse implied one-to-one relationships
        created by Django when using multi-table inheritance. If auto_process is an
        AutoProcess object and there exists a related Checks object, this is accessible
        as auto_process.checks. So by checking whether the auto_process object ("self"
        in this case) has a "checks" (or "curveinterpolation", or "aggregation")
        attribute, we can figure out what the actual subclass is.
        """
        for alternative in ("checks", "curveinterpolation", "aggregation"):
            if hasattr(self, alternative):
                return getattr(self, alternative)

    def _get_start_date(self):
        start_date = self.target_timeseries.end_date
        if start_date:
            start_date += dt.timedelta(minutes=1)
        return start_date

    def save(self, *args, **kwargs):
        result = super().save(*args, **kwargs)
        transaction.on_commit(lambda: tasks.execute_auto_process.delay(self.id))
        return result

    @property
    def source_timeseries(self):
        raise NotImplementedError("This property is available only in subclasses")

    @property
    def target_timeseries(self):
        raise NotImplementedError("This property is available only in subclasses")


class SelectRelatedManager(models.Manager):
    """A manager that calls select_related().

    Many models use a related object in their __str__() method. To avoid making extra
    queries just in order to print an object, we change their default manager to this
    one that uses select_related().
    """

    def get_queryset(self):
        return super().get_queryset().select_related()


class Checks(AutoProcess):
    objects = SelectRelatedManager()
    check_types = []

    class Meta:
        db_table = "enhydris_autoprocess_checks"

    def __str__(self):
        return _("Checks for {}").format(str(self.timeseries_group))

    @property
    def source_timeseries(self):
        obj, created = self.timeseries_group.timeseries_set.get_or_create(
            type=Timeseries.INITIAL
        )
        return obj

    @property
    def target_timeseries(self):
        obj, created = self.timeseries_group.timeseries_set.get_or_create(
            type=Timeseries.CHECKED
        )
        return obj

    def process_timeseries(self):
        for check_type in self.check_types:
            checked_timeseries = self.htimeseries
            try:
                check = check_type.objects.get(checks=self)
                checked_timeseries = check.check_timeseries(checked_timeseries)
            except check_type.DoesNotExist:
                pass
        return checked_timeseries.data


def delete_checks_if_no_check(sender, instance, **kwargs):
    checks = Checks.objects.get(pk=instance.checks.id)
    for check_type in Checks.check_types:
        if check_type.objects.filter(checks=checks).exists():
            return
    checks.delete()


class RangeCheck(models.Model):
    checks = models.OneToOneField(Checks, on_delete=models.CASCADE, primary_key=True)
    upper_bound = models.FloatField(verbose_name=_("Upper bound"))
    lower_bound = models.FloatField(verbose_name=_("Lower bound"))
    soft_upper_bound = models.FloatField(
        blank=True, null=True, verbose_name=_("Soft upper bound")
    )
    soft_lower_bound = models.FloatField(
        blank=True, null=True, verbose_name=_("Soft lower bound")
    )
    objects = SelectRelatedManager()

    class Meta:
        db_table = "enhydris_autoprocess_rangecheck"
        verbose_name = _("Range check")
        verbose_name_plural = _("Range checks")

    def __str__(self):
        return _("Range check for {}").format(str(self.checks.timeseries_group))

    def check_timeseries(self, source_htimeseries):
        result = self._do_hard_limits(source_htimeseries)
        result = self._do_soft_limits(result)
        return result

    def _do_hard_limits(self, source_htimeseries):
        mask = self._find_out_of_bounds_values(
            source_htimeseries, self.lower_bound, self.upper_bound
        )
        self._replace_out_of_bounds_values_with_nan(source_htimeseries, mask)
        return self._add_flag_to_out_of_bounds_values(source_htimeseries, mask, "RANGE")

    def _do_soft_limits(self, source_htimeseries):
        mask = self._find_out_of_bounds_values(
            source_htimeseries, self.soft_lower_bound, self.soft_upper_bound
        )
        return self._add_flag_to_out_of_bounds_values(
            source_htimeseries, mask, "SUSPECT"
        )

    def _find_out_of_bounds_values(self, source_htimeseries, low, high):
        timeseries = source_htimeseries.data
        return ~pd.isnull(timeseries["value"]) & ~timeseries["value"].between(low, high)

    def _replace_out_of_bounds_values_with_nan(self, ahtimeseries, mask):
        ahtimeseries.data.loc[mask, "value"] = np.nan
        return ahtimeseries

    def _add_flag_to_out_of_bounds_values(self, ahtimeseries, mask, flag):
        out_of_bounds_with_flags_mask = mask & (ahtimeseries.data["flags"] != "")
        ahtimeseries.data.loc[out_of_bounds_with_flags_mask, "flags"] += " "
        ahtimeseries.data.loc[mask, "flags"] += flag
        return ahtimeseries


Checks.check_types.append(RangeCheck)
post_delete.connect(delete_checks_if_no_check, sender=RangeCheck)


class RateOfChangeCheck(models.Model):
    checks = models.OneToOneField(Checks, on_delete=models.CASCADE, primary_key=True)
    symmetric = models.BooleanField(
        help_text=_(
            "If this is selected, it is the absolute value of the change that matters, "
            "not its direction. In this case, the allowed differences must all be "
            "positive. If it's not selected, only rates larger than a positive "
            "or smaller than a negative difference are considered."
        ),
        verbose_name=_("Symmetric"),
    )
    objects = SelectRelatedManager()

    class Meta:
        db_table = "enhydris_autoprocess_rateofchangecheck"
        verbose_name = _("Time consistency check")
        verbose_name_plural = _("Time consistency checks")

    def __str__(self):
        return _("Time consistency check for {}").format(
            str(self.checks.timeseries_group)
        )

    def check_timeseries(self, source_htimeseries):
        rocc(
            timeseries=source_htimeseries,
            thresholds=self.thresholds,
            symmetric=self.symmetric,
            flag="TEMPORAL",
        )
        data = source_htimeseries.data
        data.loc[data["flags"].str.contains("TEMPORAL"), "value"] = np.nan
        return source_htimeseries

    @property
    def thresholds(self):
        thresholds = RateOfChangeThreshold.objects.filter(
            rate_of_change_check=self
        ).order_by("delta_t")
        result = []
        for threshold in thresholds:
            result.append(Threshold(threshold.delta_t, threshold.allowed_diff))
        return result

    def get_thresholds_as_text(self):
        result = ""
        for threshold in self.thresholds:
            result += f"{threshold.delta_t}\t{threshold.allowed_diff}\n"
        return result

    def set_thresholds(self, s):
        self.rateofchangethreshold_set.all().delete()
        for line in s.splitlines():
            delta_t, allowed_diff = line.split()
            RateOfChangeThreshold(
                rate_of_change_check=self,
                delta_t=delta_t,
                allowed_diff=allowed_diff,
            ).save()


Checks.check_types.append(RateOfChangeCheck)
post_delete.connect(delete_checks_if_no_check, sender=RateOfChangeCheck)


class RateOfChangeThreshold(models.Model):
    rate_of_change_check = models.ForeignKey(
        RateOfChangeCheck, on_delete=models.CASCADE
    )
    delta_t = models.CharField(max_length=6)
    allowed_diff = models.FloatField()

    class Meta:
        db_table = "enhydris_autoprocess_rateofchangethreshold"

    @classmethod
    def is_delta_t_valid(cls, delta_t):
        m = re.match(r"(\d+)(\w+)", delta_t)
        if m is None or not int(m.group(1)) or m.group(2) not in ("min", "h", "D"):
            return False
        else:
            return True

    def save(self, *args, **kwargs):
        if not self.is_delta_t_valid(self.delta_t):
            raise DataError(f'"{self.delta_t}" is not a valid delta_t')
        super().save(*args, **kwargs)


class CurveInterpolation(AutoProcess):
    target_timeseries_group = models.ForeignKey(
        TimeseriesGroup,
        on_delete=models.CASCADE,
        verbose_name=_("Target time series group"),
    )
    objects = SelectRelatedManager()

    class Meta:
        db_table = "enhydris_autoprocess_curveinterpolation"
        verbose_name = _("Curve interpolation")
        verbose_name_plural = _("Curve interpolations")

    def __str__(self):
        return f"=> {self.target_timeseries_group}"

    @property
    def source_timeseries(self):
        try:
            return self.timeseries_group.timeseries_set.get(type=Timeseries.CHECKED)
        except Timeseries.DoesNotExist:
            pass
        obj, created = self.timeseries_group.timeseries_set.get_or_create(
            type=Timeseries.INITIAL
        )
        return obj

    @property
    def target_timeseries(self):
        obj, created = self.target_timeseries_group.timeseries_set.get_or_create(
            type=Timeseries.INITIAL
        )
        return obj

    def process_timeseries(self):
        source = self.htimeseries.data
        target = source.copy()
        target["value"] = np.nan
        target["flags"] = ""
        for period in self.curveperiod_set.order_by("start_date"):
            x, y = period._get_curve()
            utc = dt.timezone.utc
            start = dt.datetime.combine(period.start_date, dt.time(0, 0), tzinfo=utc)
            end = dt.datetime.combine(period.end_date, dt.time(23, 59), tzinfo=utc)
            values_array = source.loc[start:end, "value"].values
            new_array = np.interp(values_array, x, y, left=np.nan, right=np.nan)
            target.loc[start:end, "value"] = new_array
        return target


class CurvePeriod(models.Model):
    curve_interpolation = models.ForeignKey(
        CurveInterpolation, on_delete=models.CASCADE
    )
    start_date = models.DateField(verbose_name=_("Start date"))
    end_date = models.DateField(verbose_name=_("End date"))
    objects = SelectRelatedManager()

    class Meta:
        db_table = "enhydris_autoprocess_curveperiod"
        verbose_name = _("Curve period")
        verbose_name_plural = _("Curve periods")

    def __str__(self):
        return "{}: {} - {}".format(
            str(self.curve_interpolation), self.start_date, self.end_date
        )

    def _get_curve(self):
        x = []
        y = []
        for point in self.curvepoint_set.filter(curve_period=self).order_by("x"):
            x.append(point.x)
            y.append(point.y)
        return x, y

    def set_curve(self, s):
        """Replaces all existing points with ones read from a string.

        The string can be comma-delimited or tab-delimited, or a mix.
        """

        s = s.replace("\t", ",")
        self.curvepoint_set.all().delete()
        for row in csv.reader(StringIO(s)):
            x, y = [float(item) for item in row[:2]]
            CurvePoint.objects.create(curve_period=self, x=x, y=y)


class CurvePoint(models.Model):
    curve_period = models.ForeignKey(CurvePeriod, on_delete=models.CASCADE)
    x = models.FloatField()
    y = models.FloatField()
    objects = SelectRelatedManager()

    def __str__(self):
        return _("{}: Point ({}, {})").format(str(self.curve_period), self.x, self.y)

    class Meta:
        db_table = "enhydris_autoprocess_curvepoint"


class Aggregation(AutoProcess):
    METHOD_CHOICES = [
        ("sum", "Sum"),
        ("mean", "Mean"),
        ("max", "Max"),
        ("min", "Min"),
    ]
    target_time_step = models.CharField(
        max_length=7,
        help_text=_(
            'E.g. "10min", "1h" (hourly), "1D" (daily), "1M" (monthly), "1Y" (yearly). '
            "More specifically, it's a number plus a unit, with no space in "
            "between. The units available are min, h, D, M, Y."
        ),
        verbose_name=_("Target time step"),
    )
    method = models.CharField(
        max_length=4, choices=METHOD_CHOICES, verbose_name=_("Method")
    )
    max_missing = models.PositiveSmallIntegerField(
        default=0,
        help_text=_(
            "Defines what happens if some of the source records corresponding to a "
            "destination record are missing. Suppose you are aggregating ten-minute "
            "to hourly and for 23 January between 12:00 and 13:00 there are only "
            "four nonempty records in the ten-minute time series (instead of the "
            "usual six). If you set this to 1 or lower, the hourly record for 23 "
            "January 13:00 will be empty; if 2 or larger, the hourly value will be "
            "derived from the four values. In the latter case, the MISS flag will "
            "also be set in the resulting record."
        ),
        verbose_name=_("Max missing"),
    )
    resulting_timestamp_offset = models.CharField(
        max_length=7,
        blank=True,
        help_text=_(
            'If the time step of the target time series is one day ("D") and you set '
            'the resulting timestamp offset to "1min", the resulting time stamps will '
            "be ending in 23:59.  This does not modify the calculations; it only "
            "subtracts the specified offset from the timestamp after the calculations "
            "have finished. Leave empty to leave the timestamps alone."
        ),
        verbose_name=_("Resulting timestamp offset"),
    )
    objects = SelectRelatedManager()

    class Meta:
        db_table = "enhydris_autoprocess_aggregation"
        verbose_name = _("Aggregation")
        verbose_name_plural = _("Aggregations")

    def __str__(self):
        return _("Aggregation for {}").format(str(self.timeseries_group))

    @property
    def source_timeseries(self):
        try:
            return self.timeseries_group.timeseries_set.get(type=Timeseries.CHECKED)
        except Timeseries.DoesNotExist:
            obj, created = self.timeseries_group.timeseries_set.get_or_create(
                type=Timeseries.INITIAL
            )
            return obj

    @property
    def target_timeseries(self):
        obj, created = self.timeseries_group.timeseries_set.get_or_create(
            type=Timeseries.AGGREGATED,
            time_step=self.target_time_step,
            name=self.get_method_display(),
        )
        return obj

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        check_time_step(self.target_time_step)
        self._check_resulting_timestamp_offset()
        super().save(force_insert, force_update, *args, **kwargs)

    def _get_start_date(self):
        if self._last_target_timeseries_record_needs_recalculation():
            # NOTE:
            #   Running ...latest().delete() won't work. Maybe because currently
            #   TimeseriesRecord has some primary key hacks.
            adate = self.target_timeseries.timeseriesrecord_set.latest().timestamp
            self.target_timeseries.timeseriesrecord_set.filter(timestamp=adate).delete()
            self.target_timeseries.save()
        return super()._get_start_date()

    def _last_target_timeseries_record_needs_recalculation(self):
        # No recalculation needed if it didn't have the "MISSING" flag.
        if "MISS" not in self.target_timeseries.get_last_record_as_string():
            return False

        # Technically we should examine the number of missing values (given in the flag)
        # and whether more data has become available for that date. But this would be
        # quite complicated so we won't do it. The worst that can happen is that the
        # last aggregated record gets unnecessarily recalculated for a few times.
        return True

    def _check_resulting_timestamp_offset(self):
        if not self.resulting_timestamp_offset:
            return
        else:
            self._check_nonempty_resulting_timestamp_offset()

    def _check_nonempty_resulting_timestamp_offset(self):
        m = re.match(r"(-?)(\d*)(.*)$", self.resulting_timestamp_offset)
        sign, number, unit = m.group(1, 2, 3)
        if unit != "min" or (sign == "-" and number == ""):
            raise IntegrityError(
                '"{}" is not a valid resulting time step offset.'.format(
                    self.resulting_timestamp_offset
                )
            )

    def process_timeseries(self):
        if self.htimeseries.data.empty:
            return HTimeseries()
        self.source_end_date = self.htimeseries.data.index[-1]
        try:
            regularized = self._regularize_time_series(self.htimeseries)
            aggregated = self._aggregate_time_series(regularized)
        except (RegularizeError, ValueError) as e:
            logging.getLogger("enhydris.autoprocess").error(str(e))
            return HTimeseries()
        return aggregated

    def _regularize_time_series(self, source_htimeseries):
        mode = self.method == "mean" and RM.INSTANTANEOUS or RM.INTERVAL
        return regularize(source_htimeseries, new_date_flag="DATEINSERT", mode=mode)

    def _aggregate_time_series(self, source_htimeseries):
        source_step = self._get_source_step(source_htimeseries)
        target_step = self._get_target_step()
        min_count = (
            self._divide_target_step_by_source_step(source_step, target_step)
            - self.max_missing
        )
        min_count = max(min_count, 1)
        return aggregate(
            source_htimeseries,
            target_step,
            self.method,
            min_count=min_count,
            target_timestamp_offset=self.resulting_timestamp_offset or None,
            missing_flag="MISSING{}",
        )

    def _get_source_step(self, source_htimeseries):
        return pd.infer_freq(source_htimeseries.data.index)

    def _get_target_step(self):
        result = self.target_timeseries.time_step
        if not result[0].isdigit():
            result = "1" + result
        return result

    def _divide_target_step_by_source_step(self, source_step, target_step):
        return int(
            pd.Timedelta(target_step) / pd.tseries.frequencies.to_offset(source_step)
        )
