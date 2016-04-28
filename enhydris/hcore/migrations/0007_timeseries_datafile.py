# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.files.storage


class Migration(migrations.Migration):

    dependencies = [
        ('hcore', '0006_offset_help'),
    ]

    operations = [
        migrations.AddField(
            model_name='timeseries',
            name='datafile',
            field=models.FileField(storage=django.core.files.storage.FileSystemStorage(location=b'timeseries_data'), null=True, upload_to=b''),
        ),
    ]
