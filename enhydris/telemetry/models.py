import datetime as dt
import logging
import os.path
import subprocess
import sys
import zoneinfo
from io import StringIO
from traceback import print_tb

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import IntegrityError, models
from django.utils.translation import gettext_lazy as _

import iso8601

import enhydris
from enhydris.models import Station, Timeseries, TimeseriesGroup
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
        choices=sorted([(x, drivers[x].name) for x in drivers], key=lambda x: x[1]),
        verbose_name=_("Telemetry system type"),
        help_text=_(
            "The type of the system from which the data is to be fetched. "
            "If unlisted, it might mean that it is currently unsupported."
        ),
    )
    data_timezone = models.CharField(
        max_length=35,
        default="UTC",
        choices=timezone_choices,
        verbose_name=_("Time zone of the timestamps"),
        help_text=_('The time zone of the data, like "Europe/Athens" or "Etc/GMT".'),
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
    device_locator = models.CharField(max_length=200, blank=True)
    username = models.CharField(max_length=200, blank=True)
    password = models.CharField(max_length=200, blank=True)
    remote_station_id = models.CharField(max_length=20, blank=True)

    additional_config = models.JSONField(default=dict)

    @property
    def is_due(self):
        now = dt.datetime.now(tz=dt.timezone.utc)
        current_offset = now.minute + now.hour * 60
        return current_offset % self.fetch_interval_minutes == self.fetch_offset_minutes

    def fetch(self):
        try:
            self._setup_api_client()
            with self.api_client:
                self._fetch_sensors()
        except Exception:
            TelemetryLogMessage.log(self)

    def _setup_api_client(self):
        self.api_client = enhydris.telemetry.drivers[self.type](self)

    def _fetch_sensors(self):
        for sensor in self.sensor_set.all():
            self._fetch_sensor(sensor)

    def _fetch_sensor(self, sensor):
        timeseries, created = Timeseries.objects.get_or_create(
            timeseries_group_id=sensor.timeseries_group_id, type=Timeseries.INITIAL
        )
        timeseries_end_date = timeseries.end_date
        measurements = self.api_client.get_measurements(
            sensor_id=sensor.sensor_id, timeseries_end_date=timeseries_end_date
        )
        measurements = self._cleanup_measurements(measurements)
        timeseries.append_data(measurements, default_timezone=self.data_timezone)

    def _cleanup_measurements(self, measurements):
        result = StringIO()
        prev_timestamp = dt.datetime(1, 1, 1, 0, 0)
        measurements.seek(0)
        for line in measurements:
            cur_timestamp = iso8601.parse_date(line.split(",")[0])
            cur_timestamp = cur_timestamp.replace(second=0, tzinfo=None)
            if cur_timestamp == prev_timestamp:
                continue
            result.write(line)
            prev_timestamp = cur_timestamp
        result.seek(0)
        return result

    def _check_data_timezone(self):
        if self.data_timezone not in [choice[0] for choice in timezone_choices]:
            raise IntegrityError(f"'{self.data_timezone}' is not a valid time zone")

    def save(self, *args, **kwargs):
        self._check_data_timezone()
        super().save(*args, **kwargs)


class Sensor(models.Model):
    telemetry = models.ForeignKey(Telemetry, on_delete=models.CASCADE)
    sensor_id = models.CharField(max_length=20, blank=False)
    timeseries_group = models.ForeignKey(TimeseriesGroup, on_delete=models.CASCADE)

    class Meta:
        unique_together = [
            ("telemetry", "sensor_id"),
            ("telemetry", "timeseries_group"),
        ]


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
        cls._exception_name = sys.exc_info()[0].__name__
        cls._message = str(sys.exc_info()[1])
        cls._traceback = cls._get_formatted_traceback(sys.exc_info()[2])
        cls._enhydris_commit_id = cls.get_enhydris_commit_id_from_git()
        cls._telemetry = telemetry

        self = cls._log_to_db()
        self._log_to_logger()

    @staticmethod
    def _get_formatted_traceback(traceback_info):
        formatted_traceback = StringIO()
        print_tb(traceback_info, file=formatted_traceback)
        return formatted_traceback.getvalue()

    @classmethod
    def _log_to_db(cls):
        return cls.objects.create(
            telemetry=cls._telemetry,
            exception_name=cls._exception_name,
            message=cls._message,
            traceback=cls._traceback,
            enhydris_version=enhydris.__version__,
            enhydris_commit_id=cls._enhydris_commit_id,
        )

    def _log_to_logger(self):
        logging.getLogger("telemetry").error(self.get_full_message())
        logging.getLogger("telemetry").debug(self.traceback + self.get_full_message())

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
