# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('hcore', '0002_maintainers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventtype',
            name='last_modified',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='filetype',
            name='last_modified',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='gentity',
            name='last_modified',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='gentityaltcode',
            name='last_modified',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='gentityaltcodetype',
            name='last_modified',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='gentityevent',
            name='last_modified',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='gentityfile',
            name='last_modified',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='gentitygenericdata',
            name='last_modified',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='gentitygenericdatatype',
            name='last_modified',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='instrument',
            name='last_modified',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='instrumenttype',
            name='last_modified',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='intervaltype',
            name='last_modified',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='lentity',
            name='last_modified',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='overseer',
            name='last_modified',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='stationtype',
            name='last_modified',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='timeseries',
            name='last_modified',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='timestep',
            name='last_modified',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='timezone',
            name='last_modified',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='unitofmeasurement',
            name='last_modified',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='variable',
            name='last_modified',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False),
        ),
    ]
