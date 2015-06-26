# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hcore', '0003_remove_waterbasin_water_division'),
    ]

    operations = [
        migrations.AlterField(
            model_name='station',
            name='maintainers',
            field=models.ManyToManyField(related_name='maintaining_stations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='tsrecords',
            name='id',
            field=models.OneToOneField(primary_key=True, db_column=b'id', serialize=False, to='hcore.Timeseries'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='user',
            field=models.OneToOneField(verbose_name='Username', to=settings.AUTH_USER_MODEL),
        ),
    ]
