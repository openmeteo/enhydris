# Generated by Django 3.2.9 on 2021-12-12 15:01

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models

from enhydris.telemetry.models import timezone_choices


class Migration(migrations.Migration):

    dependencies = [
        ("enhydris", "0111_sitesdata"),
    ]

    operations = [
        migrations.CreateModel(
            name="Telemetry",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        max_length=30,
                        choices=[("meteoview2", "Metrica MeteoView2")],
                        help_text=(
                            "The type of the system from which the data is to be "
                            "fetched. If unlisted, it might mean that it is currently "
                            "unsupported."
                        ),
                        verbose_name="Telemetry system type",
                    ),
                ),
                (
                    "data_time_zone",
                    models.CharField(
                        blank=True,
                        max_length=35,
                        choices=timezone_choices,
                        help_text=(
                            "If the station switches to Daylight Saving Time, enter "
                            "the time zone here. This is only used in order to know "
                            "when the DST switches occur. The timestamp, after "
                            "converting to winter time, is entered as is. If the "
                            "station does not switch to DST, leave this field empty."
                        ),
                        verbose_name=(
                            "Time zone of the timestamps (useful only for DST switches)"
                        ),
                    ),
                ),
                (
                    "fetch_interval_minutes",
                    models.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(10),
                            django.core.validators.MaxValueValidator(1440),
                        ],
                        help_text=(
                            "E.g. 60 to fetch data every 60 minutes, 1440 for once a "
                            "day"
                        ),
                        verbose_name=(
                            "Fetch interval (how often to fetch data), in minutes"
                        ),
                    ),
                ),
                (
                    "fetch_offset_minutes",
                    models.PositiveSmallIntegerField(
                        validators=[django.core.validators.MaxValueValidator(1339)],
                        help_text=(
                            "If the fetch interval is 10 and the offset is 2, then "
                            "data will be fetched at :02, :12, :22, etc. If the fetch "
                            "interval is 1440 and the offset is 125, then data will be "
                            "fetched every day at 02:05am. The offset generally counts "
                            "from midnight."
                        ),
                        verbose_name="Fetch time offset, in minutes",
                    ),
                ),
                (
                    "fetch_offset_time_zone",
                    models.CharField(
                        max_length=35,
                        choices=timezone_choices,
                        help_text=(
                            "The time zone to which the fetch time offset refers."
                        ),
                        verbose_name="Time zone for the fetch time offset",
                    ),
                ),
                ("configuration", models.JSONField()),
                (
                    "station",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="enhydris.station",
                    ),
                ),
            ],
        ),
    ]
