# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hcore', '0005_remove_is_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timeseries',
            name='timestamp_offset_minutes',
            field=models.IntegerField(help_text='If unsure, set this to zero. It indicates the difference of what is shown from what is meant. For example, if for an hourly time series it is -5, then 2015-10-14 11:00 means the interval from 2015-10-14 09:55 to 2015-10-14 10:55. -1440 is common for daily time series.', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='timeseries',
            name='timestamp_offset_months',
            field=models.SmallIntegerField(help_text='If unsure, set this to 1 for monthly, 12 for annual, and zero otherwise.  For a monthly time series, an offset of -475 minutes and 1 month means that 2003-11-01 00:00 (normally shown as 2003-11) denotes the interval 2003-10-31 18:05 to 2003-11-30 18:05.', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='timeseries',
            name='timestamp_rounding_minutes',
            field=models.PositiveIntegerField(help_text='For an hourly time series whose timestamps end in :00, set this to zero; if they end in :12, set it to 12. For a ten-minute time series with timestamps ending in :12, :22, :32, etc., set it to 2.  For daily ending at 08:00, set it to 480. Leave empty if timestamps are irregular.', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='timeseries',
            name='timestamp_rounding_months',
            field=models.PositiveSmallIntegerField(help_text='Set this to zero, except for annual time series, indicating the difference from January; for example, set it to 9 if the timestamps use a hydrological year starting in October. Leave empty if timestamps are irregular.', null=True, blank=True),
        ),
    ]
