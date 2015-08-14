# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hcore', '0003_last_modified'),
    ]

    operations = [
        migrations.RenameField(
            model_name='timeseries',
            old_name='actual_offset_minutes',
            new_name='timestamp_offset_minutes',
        ),
        migrations.RenameField(
            model_name='timeseries',
            old_name='actual_offset_months',
            new_name='timestamp_offset_months',
        ),
        migrations.RenameField(
            model_name='timeseries',
            old_name='nominal_offset_minutes',
            new_name='timestamp_rounding_minutes',
        ),
        migrations.RenameField(
            model_name='timeseries',
            old_name='nominal_offset_months',
            new_name='timestamp_rounding_months',
        ),
    ]
