import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("enhydris", "0032_abolish_filetype"),
    ]

    operations = [
        migrations.CreateModel(
            name="TimeseriesRecord",
            fields=[
                (
                    "timeseries",
                    models.ForeignKey(
                        to="enhydris.Timeseries",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                ("timestamp", models.DateTimeField(primary_key=True, serialize=False)),
                ("value", models.FloatField(blank=True, null=True)),
                ("flags", models.CharField(blank=True, max_length=237)),
            ],
            options={"get_latest_by": "timestamp", "managed": False},
        ),
        migrations.RunSQL(
            "CREATE EXTENSION IF NOT EXISTS timescaledb",
            reverse_sql="DROP EXTENSION timescaledb",
        ),
        migrations.RunSQL(
            """
            CREATE TABLE enhydris_timeseriesrecord (
                timeseries_id INTEGER NOT NULL,
                "timestamp" TIMESTAMP WITH TIME ZONE NOT NULL,
                value DOUBLE PRECISION NULL,
                flags VARCHAR(237) NOT NULL
            )
            """,
            reverse_sql="DROP TABLE enhydris_timeseriesrecord",
        ),
        migrations.RunSQL(
            """
            SELECT create_hypertable(
                'enhydris_timeseriesrecord',
                'timestamp',
                chunk_time_interval => interval '1 year'
            )
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
