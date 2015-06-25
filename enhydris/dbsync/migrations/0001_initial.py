# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Database',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, blank=True)),
                ('ip_address', models.CharField(max_length=16, verbose_name='IP address')),
                ('hostname', models.CharField(unique=True, max_length=255, verbose_name='Hostname')),
                ('descr', models.TextField(max_length=255, verbose_name='Description', blank=True)),
                ('last_sync', models.DateTimeField(null=True, editable=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
