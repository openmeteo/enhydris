# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.files.storage


class Migration(migrations.Migration):

    dependencies = [
        ('hcore', '0009_remove_ts_records'),
    ]

    operations = [
        migrations.AddField(
            model_name='timeseries',
            name='end_date',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='timeseries',
            name='start_date',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='timeseries',
            name='datafile',
            field=models.FileField(storage=django.core.files.storage.FileSystemStorage(location=b'timeseries_data'), null=True, upload_to=b'', blank=True),
        ),
    ]
