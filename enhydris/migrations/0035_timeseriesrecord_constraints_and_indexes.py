from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("enhydris", "0034_timeseriesrecord_data"),
    ]

    operations = [
        migrations.RunSQL(
            """
            ALTER TABLE enhydris_timeseriesrecord
            ADD CONSTRAINT enhydris_timeseriesrecord_pk
                PRIMARY KEY(timeseries_id, "timestamp")
            """,
            reverse_sql="""
            ALTER TABLE enhydris_timeseriesrecord
            DROP CONSTRAINT enhydris_timeseriesrecord_pk
            """,
        ),
        migrations.RunSQL(
            """
            ALTER TABLE enhydris_timeseriesrecord
            ADD CONSTRAINT enhydris_timeseriesrecord_timeseries_fk
                FOREIGN KEY (timeseries_id)
                REFERENCES enhydris_timeseries(id) DEFERRABLE INITIALLY DEFERRED
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "CREATE INDEX enhydris_timeseriesrecord_timeseries_id_idx "
            "ON enhydris_timeseriesrecord(timeseries_id)",
            reverse_sql="DROP INDEX enhydris_timeseriesrecord_timeseries_id_idx",
        ),
        migrations.RunSQL(
            "CREATE INDEX enhydris_timeseriesrecord_timestamp_timeseries_id_idx "
            'ON enhydris_timeseriesrecord("timestamp", timeseries_id)',
            reverse_sql="""
            DROP INDEX enhydris_timeseriesrecord_timestamp_timeseries_id_idx""",
        ),
    ]
