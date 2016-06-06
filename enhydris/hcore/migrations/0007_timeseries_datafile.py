# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import enhydris.hcore.models


class Migration(migrations.Migration):

    dependencies = [
        ('hcore', '0006_offset_help'),
    ]

    operations = [
        migrations.AddField(
            model_name='timeseries',
            name='datafile',
            field=models.FileField(storage=enhydris.hcore.models.TimeseriesStorage(), null=True, upload_to=b'', blank=True),
        ),
    ]
