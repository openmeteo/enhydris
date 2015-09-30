# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def check_can_proceed(apps, schema_editor):
    """Check that the is_active fields all have the same value."""
    Station = apps.get_model('hcore', 'Station')
    Instrument = apps.get_model('hcore', 'Instrument')
    station_offending_rows = Station.objects.filter(is_active=True)
    instrument_offending_rows = Instrument.objects.filter(is_active=True)
    if station_offending_rows.count() or instrument_offending_rows.count():
        raise Exception(
            "The is_active field has been abolished, but one of the stations "
            "or one of the instruments in the database has is_active=True. "
            "Cowardly refusing to upgrade the database. If you are certain "
            "you don't need the is_active fields, make sure it is False in "
            "all stations and all instruments, then try again. If you need "
            "the is_active field, use Enhydris 0.5 for now and call support.")


def dummy(apps, schema_editor):
    """Do nothing for reverse data migration."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('hcore', '0004_offsets'),
    ]

    operations = [
        migrations.RunPython(check_can_proceed, reverse_code=dummy),
        migrations.RemoveField(
            model_name='instrument',
            name='is_active',
        ),
        migrations.RemoveField(
            model_name='station',
            name='is_active',
        ),
    ]
