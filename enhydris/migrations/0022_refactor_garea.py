import textwrap

import django.contrib.gis.db.models.fields
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


def delete_countries_if_unused(apps, schema_editor):
    # Normally we require that PoliticalDivision has been emptied manually before
    # running this migration. However, countries that have been created by an earlier
    # migration are removed automatically.
    PoliticalDivision = apps.get_model("enhydris", "PoliticalDivision")
    PoliticalDivision.objects.filter(parent=None, id__lte=246).delete()


def error():
    msg = """\
        This migration removes water basins, water divisions, and political
        divisions.  This data shall be gone for ever. I'm a coward and I refuse to take
        responsibility for this. Go delete them yourself first. This is how to do it:

        BEGIN;
        UPDATE enhydris_gentity
            SET water_basin_id=null, water_division_id=null, political_division_id=null;
        DELETE FROM enhydris_waterbasin;
        DELETE FROM enhydris_waterdivision;
        DELETE FROM enhydris_politicaldivision;
        DELETE FROM enhydris_garea;
        DELETE FROM enhydris_gentity
            WHERE id NOT IN (
                SELECT gentity_ptr_id from enhydris_gpoint
            );
        /*
          The last two queries should have returned the same row count, equal to the
          sum of the three previous ones.
        */
        COMMIT;
        """
    raise ValueError(textwrap.dedent(msg))


def check_gentity_geopointers_are_empty(apps, schema_editor):
    Gentity = apps.get_model("enhydris", "Gentity")
    queryset = Gentity.objects.exclude(
        water_basin__isnull=True,
        water_division__isnull=True,
        political_division__isnull=True,
    )
    if queryset.exists():
        error()


def check_garea_is_empty(apps, schema_editor):
    Garea = apps.get_model("enhydris", "Garea")
    if Garea.objects.exists():
        error()


def do_nothing(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [("enhydris", "0021_gpoint_geometry")]

    operations = [
        migrations.RunPython(check_gentity_geopointers_are_empty, do_nothing),
        migrations.RunPython(delete_countries_if_unused, do_nothing),
        migrations.RunPython(check_garea_is_empty, do_nothing),
        migrations.CreateModel(
            name="GareaCategory",
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
            ],
            options={
                "verbose_name": "Garea categories",
                "verbose_name_plural": "Garea categories",
            },
        ),
    ]
