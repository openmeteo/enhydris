# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.db.models import Q


def check_empty(apps, schema_editor):
    """Check that the dbsync fields are empty before removing them."""
    model_names = ('EventType', 'FileType', 'Gentity', 'GentityAltCode',
                   'GentityAltCodeType', 'GentityEvent', 'GentityFile',
                   'GentityGenericData', 'GentityGenericDataType',
                   'Instrument', 'InstrumentType', 'IntervalType',
                   'Lentity', 'Overseer', 'StationType', 'Timeseries',
                   'TimeStep', 'TimeZone', 'UnitOfMeasurement', 'Variable')
    for model_name in model_names:
        model = apps.get_model('hcore', model_name)
        offending_rows = model.objects.filter(
            Q(original_db__isnull=False) | Q(original_id__isnull=False))
        if offending_rows.count():
            raise Exception(
                "One of the rows of the database table that corresponds "
                "to {} has original_id or original_db_id that is not null. "
                "The database cannot be updated, as it apparently has "
                "been using the dbsync features, which have been abolished "
                "in this version of Enhydris. Please use Enhydris version "
                "0.2.".format(model_name))


def dummy(apps, schema_editor):
    """Do nothing for reverse data migration."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('hcore', '0004_auto_minor_related_field_fixes'),
    ]

    operations = [
        migrations.RunPython(check_empty, dummy),
        migrations.RemoveField(
            model_name='eventtype',
            name='original_db',
        ),
        migrations.RemoveField(
            model_name='eventtype',
            name='original_id',
        ),
        migrations.RemoveField(
            model_name='filetype',
            name='original_db',
        ),
        migrations.RemoveField(
            model_name='filetype',
            name='original_id',
        ),
        migrations.RemoveField(
            model_name='gentity',
            name='original_db',
        ),
        migrations.RemoveField(
            model_name='gentity',
            name='original_id',
        ),
        migrations.RemoveField(
            model_name='gentityaltcode',
            name='original_db',
        ),
        migrations.RemoveField(
            model_name='gentityaltcode',
            name='original_id',
        ),
        migrations.RemoveField(
            model_name='gentityaltcodetype',
            name='original_db',
        ),
        migrations.RemoveField(
            model_name='gentityaltcodetype',
            name='original_id',
        ),
        migrations.RemoveField(
            model_name='gentityevent',
            name='original_db',
        ),
        migrations.RemoveField(
            model_name='gentityevent',
            name='original_id',
        ),
        migrations.RemoveField(
            model_name='gentityfile',
            name='original_db',
        ),
        migrations.RemoveField(
            model_name='gentityfile',
            name='original_id',
        ),
        migrations.RemoveField(
            model_name='gentitygenericdata',
            name='original_db',
        ),
        migrations.RemoveField(
            model_name='gentitygenericdata',
            name='original_id',
        ),
        migrations.RemoveField(
            model_name='gentitygenericdatatype',
            name='original_db',
        ),
        migrations.RemoveField(
            model_name='gentitygenericdatatype',
            name='original_id',
        ),
        migrations.RemoveField(
            model_name='instrument',
            name='original_db',
        ),
        migrations.RemoveField(
            model_name='instrument',
            name='original_id',
        ),
        migrations.RemoveField(
            model_name='instrumenttype',
            name='original_db',
        ),
        migrations.RemoveField(
            model_name='instrumenttype',
            name='original_id',
        ),
        migrations.RemoveField(
            model_name='intervaltype',
            name='original_db',
        ),
        migrations.RemoveField(
            model_name='intervaltype',
            name='original_id',
        ),
        migrations.RemoveField(
            model_name='lentity',
            name='original_db',
        ),
        migrations.RemoveField(
            model_name='lentity',
            name='original_id',
        ),
        migrations.RemoveField(
            model_name='overseer',
            name='original_db',
        ),
        migrations.RemoveField(
            model_name='overseer',
            name='original_id',
        ),
        migrations.RemoveField(
            model_name='stationtype',
            name='original_db',
        ),
        migrations.RemoveField(
            model_name='stationtype',
            name='original_id',
        ),
        migrations.RemoveField(
            model_name='timeseries',
            name='original_db',
        ),
        migrations.RemoveField(
            model_name='timeseries',
            name='original_id',
        ),
        migrations.RemoveField(
            model_name='timestep',
            name='original_db',
        ),
        migrations.RemoveField(
            model_name='timestep',
            name='original_id',
        ),
        migrations.RemoveField(
            model_name='timezone',
            name='original_db',
        ),
        migrations.RemoveField(
            model_name='timezone',
            name='original_id',
        ),
        migrations.RemoveField(
            model_name='unitofmeasurement',
            name='original_db',
        ),
        migrations.RemoveField(
            model_name='unitofmeasurement',
            name='original_id',
        ),
        migrations.RemoveField(
            model_name='variable',
            name='original_db',
        ),
        migrations.RemoveField(
            model_name='variable',
            name='original_id',
        ),
    ]
