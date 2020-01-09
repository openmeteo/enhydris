import os
import sys
from io import StringIO

from django.core.management import call_command
from django.db import connection, migrations


def create_countries(apps, schema_editor):
    PoliticalDivision = apps.get_model("enhydris", "PoliticalDivision")
    if PoliticalDivision.objects.exists():
        sys.stderr.write(
            "PoliticalDivision already has records. Apparently this is\n"
            "an old database being upgraded. I'm not adding countries.\n"
        )
        return
    dirname = os.path.dirname(os.path.abspath(__file__))
    countries_file = os.path.join(dirname, "0002-iso-3166-1-alpha-2.txt")
    pk = 0
    with open(countries_file) as f:
        in_preamble = True
        for line in f:
            # Skip to blank line
            if in_preamble:
                if not line.strip():
                    in_preamble = False
                continue

            pk += 1
            name, code = line.strip().split(";")
            short_name = name[:51]
            PoliticalDivision.objects.create(
                id=pk, name=name, short_name=short_name, code=code
            )

    # Reset the id sequence
    sqlsequencereset = StringIO()
    call_command("sqlsequencereset", "enhydris", "--no-color", stdout=sqlsequencereset)
    sqlsequencereset.seek(0)
    reset_sequence = [line for line in sqlsequencereset if '"enhydris_gentity"' in line]
    assert len(reset_sequence) == 1
    with connection.cursor() as cursor:
        cursor.execute(reset_sequence[0])


def create_interval_types(apps, schema_editor):
    IntervalType = apps.get_model("enhydris", "IntervalType")
    if IntervalType.objects.exists():
        sys.stderr.write(
            "IntervalType already has records. Apparently this is\n"
            "an old database being upgraded. I'm not adding interval types.\n"
        )
        return
    interval_types = {
        1: "Sum",
        2: "Average value",
        3: "Minimum",
        4: "Maximum",
        5: "Vector average",
    }
    for pk, descr in interval_types.items():
        IntervalType.objects.create(
            id=pk, descr=descr, value=descr.upper().replace(" ", "_")
        )

    # Reset the id sequence
    sqlsequencereset = StringIO()
    call_command("sqlsequencereset", "enhydris", "--no-color", stdout=sqlsequencereset)
    sqlsequencereset.seek(0)
    reset_sequence = [
        line for line in sqlsequencereset if '"enhydris_intervaltype"' in line
    ]
    assert len(reset_sequence) <= 1
    # In later migrations we delete IntervalType. Somehow, then, this sequence does
    # not exist (probably a bug in the frozen models). This is why we have the "if"
    # below.
    if len(reset_sequence) == 1:
        with connection.cursor() as cursor:
            cursor.execute(reset_sequence[0])


def reverse_migration(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [("enhydris", "0001_initial")]

    operations = [
        migrations.RunPython(create_countries, reverse_migration),
        migrations.RunPython(create_interval_types, reverse_migration),
    ]
