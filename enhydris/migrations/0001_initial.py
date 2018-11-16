import django.contrib.gis.db.models.fields
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import enhydris.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="EventType",
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
                    "last_modified",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False, null=True
                    ),
                ),
                ("descr", models.CharField(blank=True, max_length=200)),
                ("descr_alt", models.CharField(blank=True, max_length=200)),
            ],
            options={"abstract": False, "ordering": ("descr",)},
        ),
        migrations.CreateModel(
            name="FileType",
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
                    "last_modified",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False, null=True
                    ),
                ),
                ("descr", models.CharField(blank=True, max_length=200)),
                ("descr_alt", models.CharField(blank=True, max_length=200)),
                ("mime_type", models.CharField(max_length=64)),
            ],
            options={"abstract": False, "ordering": ("descr",)},
        ),
        migrations.CreateModel(
            name="Gentity",
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
                    "last_modified",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False, null=True
                    ),
                ),
                ("name", models.CharField(blank=True, max_length=200)),
                ("short_name", models.CharField(blank=True, max_length=50)),
                ("remarks", models.TextField(blank=True)),
                ("name_alt", models.CharField(blank=True, max_length=200)),
                ("short_name_alt", models.CharField(blank=True, max_length=50)),
                ("remarks_alt", models.TextField(blank=True)),
            ],
            options={"ordering": ("name",), "verbose_name_plural": "Gentities"},
        ),
        migrations.CreateModel(
            name="GentityAltCode",
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
                    "last_modified",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False, null=True
                    ),
                ),
                ("value", models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name="GentityAltCodeType",
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
                    "last_modified",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False, null=True
                    ),
                ),
                ("descr", models.CharField(blank=True, max_length=200)),
                ("descr_alt", models.CharField(blank=True, max_length=200)),
            ],
            options={"abstract": False, "ordering": ("descr",)},
        ),
        migrations.CreateModel(
            name="GentityEvent",
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
                    "last_modified",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False, null=True
                    ),
                ),
                ("date", models.DateField()),
                ("user", models.CharField(max_length=64)),
                ("report", models.TextField(blank=True)),
                ("report_alt", models.TextField(blank=True)),
            ],
            options={"ordering": ["-date"]},
        ),
        migrations.CreateModel(
            name="GentityFile",
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
                    "last_modified",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False, null=True
                    ),
                ),
                ("date", models.DateField(blank=True, null=True)),
                ("content", models.FileField(upload_to="gentityfile")),
                ("descr", models.CharField(max_length=100)),
                ("remarks", models.TextField(blank=True)),
                ("descr_alt", models.CharField(max_length=100)),
                ("remarks_alt", models.TextField(blank=True)),
                (
                    "file_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="enhydris.FileType",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="GentityGenericData",
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
                    "last_modified",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False, null=True
                    ),
                ),
                ("descr", models.CharField(max_length=100)),
                ("remarks", models.TextField(blank=True)),
                ("descr_alt", models.CharField(max_length=100)),
                ("remarks_alt", models.TextField(blank=True)),
                ("content", models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="GentityGenericDataType",
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
                    "last_modified",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False, null=True
                    ),
                ),
                ("descr", models.CharField(blank=True, max_length=200)),
                ("descr_alt", models.CharField(blank=True, max_length=200)),
                ("file_extension", models.CharField(max_length=16)),
            ],
            options={"abstract": False, "ordering": ("descr",)},
        ),
        migrations.CreateModel(
            name="Instrument",
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
                    "last_modified",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False, null=True
                    ),
                ),
                ("manufacturer", models.CharField(blank=True, max_length=50)),
                ("model", models.CharField(blank=True, max_length=50)),
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
                ("name", models.CharField(blank=True, max_length=100)),
                ("remarks", models.TextField(blank=True)),
                ("name_alt", models.CharField(blank=True, max_length=100)),
                ("remarks_alt", models.TextField(blank=True)),
            ],
            options={"ordering": ("name",)},
        ),
        migrations.CreateModel(
            name="InstrumentType",
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
                    "last_modified",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False, null=True
                    ),
                ),
                ("descr", models.CharField(blank=True, max_length=200)),
                ("descr_alt", models.CharField(blank=True, max_length=200)),
            ],
            options={"abstract": False, "ordering": ("descr",)},
        ),
        migrations.CreateModel(
            name="IntervalType",
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
                    "last_modified",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False, null=True
                    ),
                ),
                ("descr", models.CharField(blank=True, max_length=200)),
                ("descr_alt", models.CharField(blank=True, max_length=200)),
                ("value", models.CharField(max_length=50)),
            ],
            options={"abstract": False, "ordering": ("descr",)},
        ),
        migrations.CreateModel(
            name="Lentity",
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
                    "last_modified",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False, null=True
                    ),
                ),
                ("remarks", models.TextField(blank=True)),
                ("remarks_alt", models.TextField(blank=True)),
                (
                    "ordering_string",
                    models.CharField(
                        blank=True, editable=False, max_length=255, null=True
                    ),
                ),
            ],
            options={
                "ordering": ("ordering_string",),
                "verbose_name_plural": "Lentities",
            },
        ),
        migrations.CreateModel(
            name="Overseer",
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
                    "last_modified",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False, null=True
                    ),
                ),
                ("is_current", models.BooleanField(default=False)),
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="StationType",
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
                    "last_modified",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False, null=True
                    ),
                ),
                ("descr", models.CharField(blank=True, max_length=200)),
                ("descr_alt", models.CharField(blank=True, max_length=200)),
            ],
            options={"abstract": False, "ordering": ("descr",)},
        ),
        migrations.CreateModel(
            name="Timeseries",
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
                    "last_modified",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False, null=True
                    ),
                ),
                ("name", models.CharField(blank=True, max_length=200)),
                ("name_alt", models.CharField(blank=True, default="", max_length=200)),
                ("hidden", models.BooleanField(default=False)),
                ("precision", models.SmallIntegerField(blank=True, null=True)),
                ("remarks", models.TextField(blank=True)),
                ("remarks_alt", models.TextField(blank=True, default="")),
                (
                    "timestamp_rounding_minutes",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text=(
                            "For an hourly time series whose timestamps end in :00, "
                            "set this to zero; if they end in :12, set it to 12. For "
                            "a ten-minute time series with timestamps ending in :12, "
                            ":22, :32, etc., set it to 2.  For daily ending at 08:00, "
                            "set it to 480. Leave empty if timestamps are irregular."
                        ),
                        null=True,
                    ),
                ),
                (
                    "timestamp_rounding_months",
                    models.PositiveSmallIntegerField(
                        blank=True,
                        help_text=(
                            "Set this to zero, except for annual time series, "
                            "indicating the difference from January; for example, "
                            "set it to 9 if the timestamps use a hydrological year "
                            "starting in October. Leave empty if timestamps are "
                            "irregular."
                        ),
                        null=True,
                    ),
                ),
                (
                    "timestamp_offset_minutes",
                    models.IntegerField(
                        blank=True,
                        help_text=(
                            "If unsure, set this to zero. It indicates the difference "
                            "of what is shown from what is meant. For example, if "
                            "for an hourly time series it is -5, then 2015-10-14 "
                            "11:00 means the interval from 2015-10-14 09:55 to "
                            "2015-10-14 10:55. -1440 is common for daily time series."
                        ),
                        null=True,
                    ),
                ),
                (
                    "timestamp_offset_months",
                    models.SmallIntegerField(
                        blank=True,
                        help_text=(
                            "If unsure, set this to 1 for monthly, 12 for annual, "
                            "and zero otherwise.  For a monthly time series, an "
                            "offset of -475 minutes and 1 month means that "
                            "2003-11-01 00:00 (normally shown as 2003-11) denotes "
                            "the interval 2003-10-31 18:05 to 2003-11-30 18:05."
                        ),
                        null=True,
                    ),
                ),
                (
                    "datafile",
                    models.FileField(
                        blank=True,
                        null=True,
                        storage=enhydris.models.TimeseriesStorage(),
                        upload_to="",
                    ),
                ),
                ("start_date_utc", models.DateTimeField(blank=True, null=True)),
                ("end_date_utc", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "ordering": ("hidden",),
                "verbose_name": "Time Series",
                "verbose_name_plural": "Time Series",
            },
        ),
        migrations.CreateModel(
            name="TimeStep",
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
                    "last_modified",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False, null=True
                    ),
                ),
                ("descr", models.CharField(blank=True, max_length=200)),
                ("descr_alt", models.CharField(blank=True, max_length=200)),
                ("length_minutes", models.PositiveIntegerField()),
                ("length_months", models.PositiveSmallIntegerField()),
            ],
            options={"abstract": False, "ordering": ("descr",)},
        ),
        migrations.CreateModel(
            name="TimeZone",
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
                    "last_modified",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False, null=True
                    ),
                ),
                ("code", models.CharField(max_length=50)),
                ("utc_offset", models.SmallIntegerField()),
            ],
            options={"ordering": ("utc_offset",)},
        ),
        migrations.CreateModel(
            name="UnitOfMeasurement",
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
                    "last_modified",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False, null=True
                    ),
                ),
                ("descr", models.CharField(blank=True, max_length=200)),
                ("descr_alt", models.CharField(blank=True, max_length=200)),
                ("symbol", models.CharField(max_length=50)),
            ],
            options={"abstract": False, "ordering": ("descr",)},
        ),
        migrations.CreateModel(
            name="UserProfile",
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
                    "fname",
                    models.CharField(
                        blank=True, max_length=30, null=True, verbose_name="First Name"
                    ),
                ),
                (
                    "lname",
                    models.CharField(
                        blank=True, max_length=30, null=True, verbose_name="Last Name"
                    ),
                ),
                (
                    "address",
                    models.CharField(
                        blank=True, max_length=100, null=True, verbose_name="Location"
                    ),
                ),
                (
                    "organization",
                    models.CharField(
                        blank=True,
                        max_length=100,
                        null=True,
                        verbose_name="Organization",
                    ),
                ),
                ("email_is_public", models.BooleanField(default=False)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Username",
                    ),
                ),
            ],
            options={"verbose_name": "Profile", "verbose_name_plural": "Profiles"},
        ),
        migrations.CreateModel(
            name="Variable",
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
                    "last_modified",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False, null=True
                    ),
                ),
                ("descr", models.CharField(blank=True, max_length=200)),
                ("descr_alt", models.CharField(blank=True, max_length=200)),
            ],
            options={"abstract": False, "ordering": ("descr",)},
        ),
        migrations.CreateModel(
            name="Garea",
            fields=[
                (
                    "gentity_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="enhydris.Gentity",
                    ),
                ),
                ("area", models.FloatField(blank=True, null=True)),
                (
                    "mpoly",
                    django.contrib.gis.db.models.fields.MultiPolygonField(
                        blank=True, null=True, srid=4326
                    ),
                ),
            ],
            bases=("enhydris.gentity",),
        ),
        migrations.CreateModel(
            name="Gline",
            fields=[
                (
                    "gentity_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="enhydris.Gentity",
                    ),
                ),
                ("length", models.FloatField(blank=True, null=True)),
                (
                    "linestring",
                    django.contrib.gis.db.models.fields.LineStringField(
                        blank=True, null=True, srid=4326
                    ),
                ),
            ],
            bases=("enhydris.gentity",),
        ),
        migrations.CreateModel(
            name="Gpoint",
            fields=[
                (
                    "gentity_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="enhydris.Gentity",
                    ),
                ),
                ("srid", models.IntegerField(blank=True, null=True)),
                ("approximate", models.BooleanField(default=False)),
                ("altitude", models.FloatField(blank=True, null=True)),
                ("asrid", models.IntegerField(blank=True, null=True)),
                (
                    "point",
                    django.contrib.gis.db.models.fields.PointField(
                        blank=True, null=True, srid=4326
                    ),
                ),
            ],
            bases=("enhydris.gentity",),
        ),
        migrations.CreateModel(
            name="Organization",
            fields=[
                (
                    "lentity_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="enhydris.Lentity",
                    ),
                ),
                ("name", models.CharField(blank=True, max_length=200)),
                ("acronym", models.CharField(blank=True, max_length=50)),
                ("name_alt", models.CharField(blank=True, max_length=200)),
                ("acronym_alt", models.CharField(blank=True, max_length=50)),
            ],
            options={"ordering": ("name",)},
            bases=("enhydris.lentity",),
        ),
        migrations.CreateModel(
            name="Person",
            fields=[
                (
                    "lentity_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="enhydris.Lentity",
                    ),
                ),
                ("last_name", models.CharField(blank=True, max_length=100)),
                ("first_name", models.CharField(blank=True, max_length=100)),
                ("middle_names", models.CharField(blank=True, max_length=100)),
                ("initials", models.CharField(blank=True, max_length=20)),
                ("last_name_alt", models.CharField(blank=True, max_length=100)),
                ("first_name_alt", models.CharField(blank=True, max_length=100)),
                ("middle_names_alt", models.CharField(blank=True, max_length=100)),
                ("initials_alt", models.CharField(blank=True, max_length=20)),
            ],
            options={"ordering": ("last_name", "first_name")},
            bases=("enhydris.lentity",),
        ),
        migrations.AddField(
            model_name="unitofmeasurement",
            name="variables",
            field=models.ManyToManyField(to="enhydris.Variable"),
        ),
        migrations.AddField(
            model_name="timeseries",
            name="gentity",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="timeseries",
                to="enhydris.Gentity",
            ),
        ),
        migrations.AddField(
            model_name="timeseries",
            name="instrument",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="enhydris.Instrument",
            ),
        ),
        migrations.AddField(
            model_name="timeseries",
            name="interval_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="enhydris.IntervalType",
            ),
        ),
        migrations.AddField(
            model_name="timeseries",
            name="time_step",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="enhydris.TimeStep",
            ),
        ),
        migrations.AddField(
            model_name="timeseries",
            name="time_zone",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="enhydris.TimeZone"
            ),
        ),
        migrations.AddField(
            model_name="timeseries",
            name="unit_of_measurement",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="enhydris.UnitOfMeasurement",
            ),
        ),
        migrations.AddField(
            model_name="timeseries",
            name="variable",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="enhydris.Variable"
            ),
        ),
        migrations.AddField(
            model_name="instrument",
            name="type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="enhydris.InstrumentType",
            ),
        ),
        migrations.AddField(
            model_name="gentitygenericdata",
            name="data_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="enhydris.GentityGenericDataType",
            ),
        ),
        migrations.AddField(
            model_name="gentitygenericdata",
            name="gentity",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="enhydris.Gentity"
            ),
        ),
        migrations.AddField(
            model_name="gentityfile",
            name="gentity",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="enhydris.Gentity"
            ),
        ),
        migrations.AddField(
            model_name="gentityevent",
            name="gentity",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="enhydris.Gentity"
            ),
        ),
        migrations.AddField(
            model_name="gentityevent",
            name="type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="enhydris.EventType"
            ),
        ),
        migrations.AddField(
            model_name="gentityaltcode",
            name="gentity",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="enhydris.Gentity"
            ),
        ),
        migrations.AddField(
            model_name="gentityaltcode",
            name="type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="enhydris.GentityAltCodeType",
            ),
        ),
        migrations.CreateModel(
            name="PoliticalDivision",
            fields=[
                (
                    "garea_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="enhydris.Garea",
                    ),
                ),
                ("code", models.CharField(blank=True, max_length=5)),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="enhydris.PoliticalDivision",
                    ),
                ),
            ],
            bases=("enhydris.garea",),
        ),
        migrations.CreateModel(
            name="Station",
            fields=[
                (
                    "gpoint_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="enhydris.Gpoint",
                    ),
                ),
                ("is_automatic", models.BooleanField(default=False)),
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
                ("copyright_holder", models.TextField()),
                ("copyright_years", models.CharField(max_length=10)),
                (
                    "creator",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="created_stations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "maintainers",
                    models.ManyToManyField(
                        blank=True,
                        related_name="maintaining_stations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            bases=("enhydris.gpoint",),
        ),
        migrations.CreateModel(
            name="WaterBasin",
            fields=[
                (
                    "garea_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="enhydris.Garea",
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="enhydris.WaterBasin",
                    ),
                ),
            ],
            bases=("enhydris.garea",),
        ),
        migrations.CreateModel(
            name="WaterDivision",
            fields=[
                (
                    "garea_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="enhydris.Garea",
                    ),
                )
            ],
            bases=("enhydris.garea",),
        ),
        migrations.AddField(
            model_name="overseer",
            name="person",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="enhydris.Person"
            ),
        ),
        migrations.AddField(
            model_name="gline",
            name="gpoint1",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="glines1",
                to="enhydris.Gpoint",
            ),
        ),
        migrations.AddField(
            model_name="gline",
            name="gpoint2",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="glines2",
                to="enhydris.Gpoint",
            ),
        ),
        migrations.AddField(
            model_name="station",
            name="overseers",
            field=models.ManyToManyField(
                related_name="stations_overseen",
                through="enhydris.Overseer",
                to="enhydris.Person",
            ),
        ),
        migrations.AddField(
            model_name="station",
            name="owner",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="owned_stations",
                to="enhydris.Lentity",
            ),
        ),
        migrations.AddField(
            model_name="station",
            name="stype",
            field=models.ManyToManyField(
                to="enhydris.StationType", verbose_name="type"
            ),
        ),
        migrations.AddField(
            model_name="overseer",
            name="station",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="enhydris.Station"
            ),
        ),
        migrations.AddField(
            model_name="instrument",
            name="station",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="enhydris.Station"
            ),
        ),
        migrations.AddField(
            model_name="gentity",
            name="political_division",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="enhydris.PoliticalDivision",
            ),
        ),
        migrations.AddField(
            model_name="gentity",
            name="water_basin",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="enhydris.WaterBasin",
            ),
        ),
        migrations.AddField(
            model_name="gentity",
            name="water_division",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="enhydris.WaterDivision",
            ),
        ),
    ]
