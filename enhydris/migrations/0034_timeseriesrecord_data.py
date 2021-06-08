import datetime as dt
import os
import tempfile

from django.conf import settings
from django.db import connection, migrations


def convert_files_to_data(apps, schema_editor):
    Timeseries = apps.get_model("enhydris", "Timeseries")
    for timeseries in Timeseries.objects.all().order_by("id"):
        TimeseriesConverter(apps, schema_editor, timeseries).convert()


class TimeseriesConverter:
    def __init__(self, apps, schema_editor, timeseries):
        self.apps = apps
        self.schema_editor = schema_editor
        self.timeseries = timeseries
        self.tzinfo = self._get_tzinfo()

    def _get_tzinfo(self):
        time_zone = self.timeseries.time_zone
        return dt.timezone(dt.timedelta(minutes=time_zone.utc_offset), time_zone.code)

    def convert(self):
        timeseries_id = self.timeseries.id
        if not os.path.exists(self.datafilename):
            return
        with open(self.datafilename) as src:
            with tempfile.NamedTemporaryFile(mode="w") as dst:
                for row in src:
                    timestamp, value, flags = row.split(",")
                    timestamp = f"{timestamp}{self.utc_offset_notation}"
                    dst.write(f"{timeseries_id},{timestamp},{value},{flags}")
                src.flush()
                os.chmod(dst.name, 0o755)
                connection.cursor().execute(
                    f"""
                    COPY enhydris_timeseriesrecord
                        (timeseries_id, "timestamp", value, flags)
                    FROM '{dst.name}'
                    (FORMAT CSV, FORCE_NOT_NULL ('flags'))
                    """
                )

    @property
    def datafilename(self):
        directory = os.path.abspath(settings.ENHYDRIS_TIMESERIES_DATA_DIR)
        filename = "{:010}".format(self.timeseries.id)
        return os.path.join(directory, filename)

    @property
    def utc_offset_notation(self):
        try:
            return self._cached_utc_offset_notation
        except AttributeError:
            self._calculate_utc_offset_notation()
            return self._cached_utc_offset_notation

    def _calculate_utc_offset_notation(self):
        utc_offset_minutes = self.timeseries.time_zone.utc_offset
        sign = (utc_offset_minutes < 0) and "-" or "+"
        utc_offset_minutes = abs(utc_offset_minutes)
        hours = utc_offset_minutes // 60
        minutes = utc_offset_minutes % 60
        self._cached_utc_offset_notation = f"{sign}{hours:02}{minutes:02}"


def delete_from_table(apps, schema_editor):
    for months in range(6, 1440, 6):
        connection.cursor().execute(
            f"""
            SELECT drop_chunks(
                newer_than => interval '{months} months',
                table_name => 'enhydris_timeseriesrecord'
            )
            """
        )


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("enhydris", "0033_timeseriesrecord"),
    ]

    operations = [
        migrations.RunPython(convert_files_to_data, reverse_code=delete_from_table),
    ]
