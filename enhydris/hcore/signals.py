from django.db import transaction


def after_syncdb(sender, **kwargs):
    import sys
    from django.db import connection
    if sender.__name__ != 'enhydris.hcore.models':
        return
    cursor = connection.cursor()

    sys.stderr.write("Creating database function timeseries_start_date...\n")
    try:
        with transaction.atomic():
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
    except:
        sys.stderr.write(
            "timeseries_start_date creation failed; "
            "maybe it already existed\n")

    sys.stderr.write("Creating database function timeseries_end_date...\n")
    try:
        with transaction.atomic():
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
    except:
        sys.stderr.write(
            "timeseries_end_date creation failed; maybe it already existed\n")
