# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import connection, migrations
from django.db.utils import ProgrammingError


def delete_database_functions(apps, schema_editor):
    cursor = connection.cursor()
    cursor.execute(
        "DROP FUNCTION IF EXISTS timeseries_start_date(aid INTEGER)")
    cursor.execute(
        "DROP FUNCTION IF EXISTS timeseries_end_date(aid INTEGER)")


def undelete_database_functions(apps, schema_editor):
    cursor = connection.cursor()
    cursor.execute("""
        CREATE FUNCTION timeseries_start_date(aid INTEGER)
        RETURNS timestamp AS $$
        DECLARE
            retvalue timestamp;
        BEGIN
            SELECT INTO retvalue
                to_timestamp(substring(CASE WHEN top='' OR top IS
                                        NULL THEN bottom ELSE top END
                    from '^(.*?),'),
                    'YYYY-MM-DD HH24:MI')::timestamp
            FROM ts_records
            WHERE id=aid;
            RETURN retvalue;
        END
        $$ LANGUAGE plpgsql""")
    cursor.execute("""
        CREATE FUNCTION timeseries_end_date(aid INTEGER)
        RETURNS timestamp AS $$
        DECLARE
            retvalue timestamp;
        BEGIN
            SELECT INTO retvalue to_timestamp(
                    substring(bottom from E'\n([^,]*?),[^\n]*?\n?$'),
                    'YYYY-MM-DD HH24:MI')::timestamp
            FROM ts_records
            WHERE id=aid;
            RETURN retvalue;
        END
        $$ LANGUAGE plpgsql""")


class Migration(migrations.Migration):

    dependencies = [
        ('hcore', '0008_move_data_to_datafile'),
    ]

    operations = [
        migrations.RunPython(delete_database_functions,
                             reverse_code=undelete_database_functions),
        migrations.DeleteModel(
            name='TsRecords',
        ),
    ]
