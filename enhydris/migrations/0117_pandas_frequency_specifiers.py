import re

from django.db import migrations


def modernize_frequency_specifiers(apps, schema_editor):
    Timeseries = apps.get_model("enhydris", "Timeseries")
    for timeseries in Timeseries.objects.all():
        new_time_step = _get_new_time_step(timeseries.time_step)
        if new_time_step != timeseries.time_step:
            timeseries.time_step = new_time_step
            timeseries.save()


REOBJ = re.compile(r"(\d*)([A-Z]+)$")


def _get_new_time_step(old_time_step):
    m = REOBJ.match(old_time_step)
    if m is None:
        return old_time_step
    new_unit = {"H": "h", "T": "min"}.get(m.group(2), m.group(2))
    new_number = m.group(1) or "1"
    return f"{new_number}{new_unit}"


def do_nothing(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("enhydris", "0116_timeseries_name"),
    ]

    operations = [migrations.RunPython(modernize_frequency_specifiers, do_nothing)]
