# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hcore', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='timeseries',
            old_name='end_date',
            new_name='end_date_utc',
        ),
        migrations.RenameField(
            model_name='timeseries',
            old_name='start_date',
            new_name='start_date_utc',
        ),
    ]
