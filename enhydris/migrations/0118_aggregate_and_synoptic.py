from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("enhydris", "0117_pandas_frequency_specifiers"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                UPDATE django_migrations SET app='autoprocess'
                    WHERE app='enhydris_autoprocess';
                UPDATE django_migrations SET app='synoptic'
                    WHERE app='enhydris_synoptic';
            """,
            reverse_sql="""
                UPDATE django_migrations SET app='enhydris_autoprocess'
                    WHERE app='autoprocess';
                UPDATE django_migrations SET app='enhydris_synoptic'
                    WHERE app='synoptic';
            """,
        ),
    ]
