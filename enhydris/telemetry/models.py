import datetime as dt
import os.path
import subprocess
import sys
import zoneinfo
from io import StringIO
from traceback import print_tb

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

import enhydris
from enhydris.models import Station
from enhydris.telemetry import drivers


def fix_zone_name(timezone):
    if timezone.startswith("Etc/GMT+"):
        return "UTC-" + timezone[8:]
    elif timezone.startswith("Etc/GMT-"):
        return "UTC+" + timezone[8:]
    else:
        return timezone


timezones = zoneinfo.available_timezones()
timezone_choices = [(zone, fix_zone_name(zone)) for zone in timezones]
timezone_choices.sort()


class Telemetry(models.Model):
    station = models.OneToOneField(Station, on_delete=models.CASCADE)
    type = models.CharField(
        max_length=30,
        choices=[(x, drivers[x].name) for x in drivers],
        verbose_name=_("Telemetry system type"),
        help_text=_(
            "The type of the system from which the data is to be fetched. "
            "If unlisted, it might mean that it is currently unsupported."
        ),
    )
    data_time_zone = models.CharField(
        max_length=35,
        blank=True,
        choices=timezone_choices,
        verbose_name=_("Time zone of the timestamps (useful only for DST switches)"),
        help_text=_(
            "If the station switches to Daylight Saving Time, enter the time zone "
            "here. This is only used in order to know when the DST switches occur. "
            "The timestamp, after converting to winter time, is entered as is. If "
            "the station does not switch to DST, leave this field empty."
        ),
    )
    fetch_interval_minutes = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(10), MaxValueValidator(1440)],
        verbose_name=_("Fetch interval (how often to fetch data), in minutes"),
        help_text=_("E.g. 60 to fetch data every 60 minutes, 1440 for once a day"),
    )
    fetch_offset_minutes = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(1339)],
        verbose_name=_("Fetch time offset, in minutes"),
        help_text=_(
            "If the fetch interval is 10 and the offset is 2, then data will be "
            "fetched at :02, :12, :22, etc. If the fetch interval is 1440 and "
            "the offset is 125, then data will be fetched every day at 02:05am. "
            "The offset generally counts from midnight."
        ),
    )
    fetch_offset_time_zone = models.CharField(
        max_length=35,
        choices=timezone_choices,
        verbose_name=_("Time zone for the fetch time offset"),
        help_text=_("The time zone to which the fetch time offset refers."),
    )
    configuration = models.JSONField()

    @property
    def is_due(self):
        now = dt.datetime.now(tz=zoneinfo.ZoneInfo(self.fetch_offset_time_zone))
        current_offset = now.minute + now.hour * 60
        return current_offset % self.fetch_interval_minutes == self.fetch_offset_minutes

    def fetch(self):
        telemetry = enhydris.telemetry.drivers[self.type](self)
        try:
            telemetry.fetch()
        except Exception:
            TelemetryLogMessage.log(self)


class TelemetryLogMessage(models.Model):
    telemetry = models.ForeignKey(Telemetry, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    exception_name = models.CharField(max_length=50)
    message = models.TextField()
    traceback = models.TextField()
    enhydris_version = models.TextField()
    enhydris_commit_id = models.CharField(max_length=40)

    class Meta:
        ordering = ["telemetry", "-timestamp"]

    @classmethod
    def log(cls, telemetry):
        """Logs the current exception."""
        formatted_traceback = StringIO()
        print_tb(sys.exc_info()[2], file=formatted_traceback)
        cls.objects.create(
            telemetry=telemetry,
            exception_name=sys.exc_info()[0].__name__,
            message=str(sys.exc_info()[1]),
            traceback=formatted_traceback.getvalue(),
            enhydris_version=enhydris.__version__,
            enhydris_commit_id=cls.get_enhydris_commit_id_from_git(),
        )

    @classmethod
    def get_enhydris_commit_id_from_git(cls):
        try:
            return cls._saved_commit_id
        except AttributeError:
            pass

        etld = cls._get_enhydris_top_level_directory()
        try:
            cls._saved_commit_id = (
                subprocess.run(
                    ["git", "rev-parse", "HEAD"], capture_output=True, cwd=etld
                )
                .stdout.decode()
                .strip()
            )
        except FileNotFoundError:  # Git is not installed
            cls._saved_commit_id = ""

        return cls._saved_commit_id

    @classmethod
    def _get_enhydris_top_level_directory(cls):
        levels_deep = __name__.count(".")
        dirname = os.path.dirname(__file__)
        upstairs = levels_deep * [".."]
        return os.path.join(dirname, *upstairs)

    def get_full_message(self):
        isotime = self.timestamp.replace(tzinfo=None).isoformat(
            sep=" ", timespec="seconds"
        )
        return f"{isotime} {self.exception_name}: {self.message}"

    def get_full_version(self):
        if self.enhydris_commit_id:
            return f"{self.enhydris_version} ({self.enhydris_commit_id[:10]})"
        else:
            return self.enhydris_version
