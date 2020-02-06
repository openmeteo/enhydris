import textwrap

from django.db import migrations


def check_instruments_is_empty(apps, schema_editor):
    Instrument = apps.get_model("enhydris", "Instrument")
    if Instrument.objects.exists():
        error()


def error():
    msg = """\
        This migration removes instruments. The instruments data shall be gone for ever.
        I'm a coward and I refuse to take responsibility for this. Go delete them
        yourself first. This is how to do it:

        BEGIN;
        UPDATE enhydris_timeseries SET instrument_id=null;
        DELETE FROM enhydris_instrument;
        COMMIT;
        """
    raise ValueError(textwrap.dedent(msg))


def do_nothing(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("enhydris", "0029_remove_interval_type"),
    ]

    operations = [
        migrations.RunPython(check_instruments_is_empty, do_nothing),
        migrations.RemoveField(model_name="timeseries", name="instrument"),
        migrations.DeleteModel(name="Instrument"),
        migrations.DeleteModel(name="InstrumentType"),
    ]
