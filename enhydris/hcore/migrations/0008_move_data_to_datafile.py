# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import db
from django.db import migrations

from pthelma.timeseries import Timeseries


def copy_tsdata_from_db_to_datafile(apps, schema_editor):
    TimeseriesModel = apps.get_model('hcore', 'Timeseries')
    for timeseries in TimeseriesModel.objects.all():
        t = Timeseries(timeseries.id)
        t.read_from_db(db.connection)
        if len(t):
            timeseries.datafile.name = '{:010}'.format(timeseries.id)
            with open(timeseries.datafile.path, 'w') as f:
                t.write(f)
        else:
            timeseries.datafile = None
        timeseries.save()


def copy_tsdata_from_datafile_to_db(apps, schema_editor):
    TimeseriesModel = apps.get_model('hcore', 'Timeseries')
    for timeseries in TimeseriesModel.objects.all():
        t = Timeseries(timeseries.id)
        if not timeseries.datafile:
            continue
        with open(timeseries.datafile.path, 'r') as f:
            t.read(f)
        t.write_to_db(db.connection, transaction=db.transaction, commit=False)


class Migration(migrations.Migration):

    dependencies = [
        ('hcore', '0007_timeseries_datafile'),
    ]

    operations = [
        migrations.RunPython(copy_tsdata_from_db_to_datafile,
                             reverse_code=copy_tsdata_from_datafile_to_db),
    ]
