# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def move_water_division_from_water_basin(apps, schema_editor):
    """
    There is a duplicate field: Gentity.water_division and
    WaterBasin.water_division. Before removing the latter, we will move its
    contents, if any, to the former, provided it does not conflict with
    anything already there.
    """
    WaterBasin = apps.get_model('hcore', 'WaterBasin')
    Gentity = apps.get_model('hcore', 'Gentity')
    for basin in WaterBasin.objects.all():
        if basin.water_division is None:
            continue
        gentity = Gentity.objects.get(pk=basin.pk)
        if gentity.water_division is None:
            gentity.water_division = basin.water_division
            gentity.save()
            continue
        if gentity.water_division.id != basin.water_division.id:
            raise Exception(
                "The water basin with id={} has a different water division "
                "in the waterbasin table and in the gentity table. Please "
                "fix this issue manually and retry the migration.")


def dummy(apps, schema_editor):
    """Do nothing for reverse data migration."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('hcore', '0002_auto_fix_booleans'),
    ]

    operations = [
        migrations.RunPython(move_water_division_from_water_basin, dummy),
        migrations.RemoveField(
            model_name='waterbasin',
            name='water_division',
        ),
    ]
