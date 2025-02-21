import datetime as dt
import re
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.mail import send_mail
from django.db import DataError, IntegrityError, models
from django.utils.translation import gettext as _

import iso8601
from rocc import Threshold, rocc

from enhydris.models import DISPLAY_TIMEZONE_CHOICES, Station, TimeseriesGroup

# NOTE: Confusingly, there are three distinct uses of "group" here. They refer to
# different things:
# - A "timeseries group" refers to an Enhydris time series group. See Enhydris's
#   database documentation for details on what this is.
# - A "synoptic group" means a report prepared by this app. It has a slug (e.g. "ntua")
#   so that visitors can view the report at a URL (e.g.
#   "https://openmeteo.org/synoptic/ntua/"). It was named thus because it is a report
#   about a group of stations, so "synoptic group" actually means "a group of stations
#   for which we create a synoptic report".
# - In a given synoptic group, two timeseries groups may be "groupped" together; that
#   is, shown in the same chart. This is achieved with
#   SynopticTimeseriesGroup.group_with.
#
# SynopticTimeseriesGroup means "a timeseries group used in a synoptic station".
#
# Yes, this sucks. Ideas on improving it are welcome.


class SynopticGroup(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, help_text="Identifier to be used in URL")
    stations = models.ManyToManyField(Station, through="SynopticGroupStation")
    timezone = models.CharField(
        max_length=50,
        default="Etc/GMT",
        verbose_name=_("Time zone"),
        choices=DISPLAY_TIMEZONE_CHOICES,
    )
    fresh_time_limit = models.DurationField(
        help_text=(
            "Maximum time that may have elapsed for the data to be considered fresh. "
            "For data older than this the date on the map shows red; for fresh data it "
            "shows green. Specify it in seconds or in the format 'DD HH:MM:SS'."
        )
    )

    class Meta:
        db_table = "enhydris_synoptic_synopticgroup"

    def __str__(self):
        return self.name

    def queue_warning(self, asyntsg, warning_text):
        if not hasattr(self, "early_warnings"):
            self.early_warnings = {}
        self.early_warnings[asyntsg.get_title()] = {
            "station": asyntsg.synoptic_group_station.station.name,
            "variable": asyntsg.get_title(),
            "warning_text": warning_text,
        }

    def send_early_warning_emails(self):
        if len(getattr(self, "early_warnings", {})) == 0:
            return
        emails = [x.email for x in self.earlywarningemail_set.all()]
        content = ""
        for var in self.early_warnings:
            content += self._get_early_warning_text(self.early_warnings[var])
        subject = self._get_warning_email_subject()
        send_mail(subject, content, settings.DEFAULT_FROM_EMAIL, emails)

    def _get_warning_email_subject(self):
        stations = list({v["station"] for k, v in self.early_warnings.items()})
        stations.sort()
        stations = ", ".join(stations)
        return _("Enhydris early warning ({})").format(stations)

    def _get_early_warning_text(self, data):
        station = data["station"]
        variable = data["variable"]
        text = data["warning_text"]
        return f"{station} {variable} {text}\n"


class EarlyWarningEmail(models.Model):
    synoptic_group = models.ForeignKey(SynopticGroup, on_delete=models.CASCADE)
    email = models.EmailField()

    class Meta:
        db_table = "enhydris_synoptic_earlywarningemail"
        verbose_name = _("Email address to send early warnings")
        verbose_name_plural = _("Where to send early warnings")


class SynopticGroupStation(models.Model):
    synoptic_group = models.ForeignKey(SynopticGroup, on_delete=models.CASCADE)
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField()
    timeseries_groups = models.ManyToManyField(
        TimeseriesGroup, through="SynopticTimeseriesGroup"
    )

    class Meta:
        db_table = "enhydris_synoptic_synopticgroupstation"
        unique_together = (("synoptic_group", "order"),)
        ordering = ["synoptic_group", "order"]

    def __str__(self):
        return str(self.station)

    def check_timeseries_groups_integrity(self, *args, **kwargs):
        """
        This method checks whether the timeseries_groups.through.order field starts with
        1 and is contiguous, and that groupped time series are in order.  I wrote it
        thinking I could use it somewhere, but I don't think it's possible (see
        http://stackoverflow.com/questions/33500336/). However, since I wrote it, I keep
        it, although I'm not using it anywhere. Mind you, it's unit-tested.
        """
        # Check that time series are in order
        expected_order = 0
        for syn_ts in self.synoptictimeseriesgroup_set.order_by("order"):
            expected_order += 1
            if syn_ts.order != expected_order:
                raise IntegrityError(
                    _("The order of the data must start from 1 and be continuous.")
                )

        # Check that grouped time series are in order
        current_synopticgroup_leader = None
        previous_synoptictimeseriesgroup = None
        for syn_tsg in self.synoptictimeseriesgroup_set.order_by("order"):
            if not syn_tsg.group_with:
                current_synopticgroup_leader = None
                continue
            current_synopticgroup_leader = (
                current_synopticgroup_leader or previous_synoptictimeseriesgroup
            )
            if syn_tsg.group_with.id != current_synopticgroup_leader.id:
                raise IntegrityError(
                    _("Groupped time series must be ordered together.")
                )
            previous_synoptictimeseriesgroup = syn_tsg

        super(SynopticGroupStation, self).save(*args, **kwargs)

    @property
    def synoptic_timeseries_groups(self):
        """List of synoptic timeseries group objects with data.

        The objects in the list have attribute "data", which is a pandas dataframe with
        the last 24 hours preceding the last common date, "value", which is the
        value at the last common date, and "value_status" which is the string "ok",
        "high" or "low", depending on where "value" is compared to low_limit and
        high_limit.
        """
        if not hasattr(self, "_synoptic_timeseries_groups"):
            self._determine_timeseries_groups()
        return self._synoptic_timeseries_groups

    def _determine_timeseries_groups(self):
        if self.last_common_date is None:
            self._synoptic_timeseries_groups = []
            return
        start_date = self.last_common_date - dt.timedelta(minutes=1439)
        self._synoptic_timeseries_groups = list(self.synoptictimeseriesgroup_set.all())
        self.error = False  # This may be changed by _set_ts_value()
        for asyntsg in self._synoptic_timeseries_groups:
            asyntsg.data = asyntsg.timeseries_group.default_timeseries.get_data(
                start_date=start_date, end_date=self.last_common_date
            ).data
            self._set_tsg_value(asyntsg)
            self._set_tsg_value_status(asyntsg)

    def _set_tsg_value(self, asyntsg):
        try:
            asyntsg.value = asyntsg.data.loc[self.last_common_date]["value"]
        except KeyError:
            self.error = True

    def _set_tsg_value_status(self, asyntsg):
        if not hasattr(asyntsg, "value") or asyntsg.value is None:
            asyntsg.value_status = "error"
        elif asyntsg.low_limit is not None and asyntsg.value < asyntsg.low_limit:
            asyntsg.value_status = "low"
            self.synoptic_group.queue_warning(
                asyntsg,
                self._out_of_limits_message(asyntsg, f"low limit {asyntsg.low_limit}"),
            )
        elif asyntsg.high_limit is not None and asyntsg.value > asyntsg.high_limit:
            asyntsg.value_status = "high"
            clarif = f"high limit {asyntsg.high_limit}"
            self.synoptic_group.queue_warning(
                asyntsg, self._out_of_limits_message(asyntsg, clarif)
            )
        else:
            asyntsg.value_status = "ok"

        check_rate_of_change_results = self._check_rate_of_change(asyntsg)
        if check_rate_of_change_results:
            # For the time being we don't set the status here, we just send a warning.
            self.synoptic_group.queue_warning(asyntsg, check_rate_of_change_results)

    def _out_of_limits_message(self, asyntsg, clarification):
        timestr = self.last_common_date.replace(tzinfo=None).isoformat(
            sep=" ", timespec="minutes"
        )
        return f"{timestr} {asyntsg.value} ({clarification})"

    def _check_rate_of_change(self, asyntsg):
        start_date = self.last_common_date - self._get_roc_timedelta(asyntsg)
        timeseries = asyntsg.timeseries_group.default_timeseries.get_data(
            start_date=start_date, end_date=self.last_common_date
        )
        messages = rocc(
            timeseries=timeseries,
            thresholds=asyntsg.roc_thresholds,
            symmetric=asyntsg.symmetric_rocc,
            flag="",
        )
        if not messages:
            return None
        message = messages[-1]
        date = iso8601.parse_date(message.split()[0]).replace(tzinfo=None)
        if date == self.last_common_date.replace(tzinfo=None):
            return message

    def _get_roc_timedelta(self, asyntsg):
        roc_timedeltas = [
            self._parse_timedelta(x.split()[0])
            for x in asyntsg.get_roc_thresholds_as_text().splitlines()
        ]
        if roc_timedeltas:
            return max(roc_timedeltas)
        else:
            return dt.timedelta(0)

    def _parse_timedelta(self, stepspec):
        if stepspec.endswith("min"):
            return dt.timedelta(minutes=int(stepspec[:-3]))
        elif stepspec[-1] == "H":
            return dt.timedelta(hours=int(stepspec[:-1]))
        elif stepspec[-1] == "D":
            return dt.timedelta(days=int(stepspec[:-1]))

    @property
    def last_common_date(self):
        if not hasattr(self, "_last_common_date"):
            self._determine_last_common_date()
        return self._last_common_date

    def _determine_last_common_date(self):
        # We don't actually get the last common date, which would be difficult; instead,
        # we get the minimum of the last dates of the timeseries, which will usually be
        # the last common date. station is an enhydris.synoptic.models.Station object.
        last_common_date = None
        for asyntsg in self.synoptictimeseriesgroup_set.all():
            end_date = asyntsg.timeseries_group.default_timeseries.end_date
            if end_date and ((not last_common_date) or (end_date < last_common_date)):
                last_common_date = end_date
        self._last_common_date = last_common_date

    @property
    def last_common_date_pretty(self):
        return self.last_common_date and self.last_common_date.strftime(
            "%d %b %Y %H:%M (%z)"
        )

    @property
    def last_common_date_pretty_without_timezone(self):
        return self.last_common_date and self.last_common_date.astimezone(
            ZoneInfo(self.synoptic_group.timezone)
        ).strftime("%d %b %Y %H:%M")

    @property
    def freshness(self):
        if self.last_common_date is None:
            return "old"
        oldness = dt.datetime.now(dt.timezone.utc) - self.last_common_date
        is_old = oldness > self.synoptic_group.fresh_time_limit
        return "old" if is_old else "recent"

    @property
    def target_url(self):
        target = getattr(
            settings,
            "ENHYDRIS_SYNOPTIC_STATION_LINK_TARGET",
            "station/{station.id}/",
        )
        return target.format(station=self.station)


class SynopticTimeseriesGroupManager(models.Manager):
    def primary(self):
        """Return only time series groups that don't have group_with."""
        return self.filter(group_with__isnull=True)


class SynopticTimeseriesGroup(models.Model):
    synoptic_group_station = models.ForeignKey(
        SynopticGroupStation, on_delete=models.CASCADE
    )
    timeseries_group = models.ForeignKey(TimeseriesGroup, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField()
    title = models.CharField(
        max_length=50,
        blank=True,
        help_text=_(
            "Used as the chart title and as the time series title in the report. "
            "Time series in different stations with the same title will show as a "
            "layer on the map. Leave empty to use the time series name."
        ),
    )
    low_limit = models.FloatField(
        blank=True,
        null=True,
        help_text=_(
            "If the variable goes lower than this, it will be shown red on the map."
        ),
    )
    high_limit = models.FloatField(
        blank=True,
        null=True,
        help_text=_(
            "If the variable goes higher than this, it will be shown red on the map."
        ),
    )
    group_with = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        help_text=_(
            "Specify this field if you want to group this time series with "
            "another in the same chart and in the report."
        ),
    )
    subtitle = models.CharField(
        max_length=50,
        blank=True,
        help_text=_(
            "If time series are grouped, this is shows in the legend of the chart "
            "and in the report, in brackets."
        ),
    )
    default_chart_min = models.FloatField(
        blank=True,
        null=True,
        help_text=_(
            "Minimum value of the y axis of the chart. If the variable goes "
            "lower, the chart will automatically expand. If empty, the chart will "
            "always expand just enough to accomodate the value."
        ),
    )
    default_chart_max = models.FloatField(
        blank=True,
        null=True,
        help_text=_(
            "Maximum value of the y axis of the chart. If the variable goes "
            "lower, the chart will automatically expand. If empty, the chart will "
            "always expand just enough to accomodate the value."
        ),
    )

    objects = SynopticTimeseriesGroupManager()

    class Meta:
        db_table = "enhydris_synoptic_synoptictimeseriesgroup"
        unique_together = (
            ("synoptic_group_station", "timeseries_group"),
            ("synoptic_group_station", "order"),
        )
        ordering = ["synoptic_group_station", "order"]

    def __str__(self):
        return str(self.synoptic_group_station) + " - " + self.full_name

    def get_title(self):
        return self.title or self.timeseries_group.get_name()

    def get_subtitle(self):
        return self.subtitle or self.timeseries_group.get_name()

    @property
    def full_name(self):
        result = self.get_title()
        if self.subtitle:
            result += " (" + self.subtitle + ")"
        return result

    # Rate-of-change check stuff
    # This code has been largely copied from enhydris.autoprocess.models.  For that
    # matter, it has not been unit tested.  We should do something to not have this
    # duplication.
    symmetric_rocc = models.BooleanField(
        help_text=_(
            "If this is selected, it is the absolute value of the change that matters, "
            "not its direction. In this case, the allowed differences must all be "
            "positive. If it's not selected, only rates larger than a positive "
            "or smaller than a negative difference are considered."
        ),
        default=False,
        verbose_name=_("Symmetric"),
    )

    @property
    def roc_thresholds(self):
        thresholds = RateOfChangeThreshold.objects.filter(
            synoptic_timeseries_group=self
        ).order_by("delta_t")
        result = []
        for threshold in thresholds:
            result.append(Threshold(threshold.delta_t, threshold.allowed_diff))
        return result

    def get_roc_thresholds_as_text(self):
        result = ""
        for threshold in self.roc_thresholds:
            result += f"{threshold.delta_t}\t{threshold.allowed_diff}\n"
        return result

    def set_roc_thresholds(self, s):
        self.rateofchangethreshold_set.all().delete()
        for line in s.splitlines():
            delta_t, allowed_diff = line.split()
            RateOfChangeThreshold(
                synoptic_timeseries_group=self,
                delta_t=delta_t,
                allowed_diff=allowed_diff,
            ).save()

    # End of rate-of-change-check stuff


# More rate-of-change stuff, likewise copied from elsewhere (see comment above).
class RateOfChangeThreshold(models.Model):
    synoptic_timeseries_group = models.ForeignKey(
        SynopticTimeseriesGroup, on_delete=models.CASCADE
    )
    delta_t = models.CharField(max_length=6)
    allowed_diff = models.FloatField()

    class Meta:
        db_table = "enhydris_synoptic_rateofchangethreshold"

    @classmethod
    def is_delta_t_valid(cls, delta_t):
        m = re.match(r"(\d+)(\w+)", delta_t)
        if m is None or not int(m.group(1)) or m.group(2) not in ("min", "H", "D"):
            return False
        else:
            return True

    def save(self, *args, **kwargs):
        if not self.is_delta_t_valid(self.delta_t):
            raise DataError(f'"{self.delta_t}" is not a valid delta_t')
        super().save(*args, **kwargs)


# End of rate-of-change stuff
