# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hcore', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gpoint',
            name='approximate',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='instrument',
            name='is_active',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='overseer',
            name='is_current',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='station',
            name='is_active',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='station',
            name='is_automatic',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
