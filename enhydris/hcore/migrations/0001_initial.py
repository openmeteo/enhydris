# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import enhydris.hcore.models
import django.contrib.gis.db.models.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('dbsync', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EventType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('original_id', models.IntegerField(null=True, editable=False, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('descr', models.CharField(max_length=200, blank=True)),
                ('descr_alt', models.CharField(max_length=200, blank=True)),
                ('original_db', models.ForeignKey(editable=False, to='dbsync.Database', null=True)),
            ],
            options={
                'ordering': ('descr',),
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FileType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('original_id', models.IntegerField(null=True, editable=False, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('descr', models.CharField(max_length=200, blank=True)),
                ('descr_alt', models.CharField(max_length=200, blank=True)),
                ('mime_type', models.CharField(max_length=64)),
                ('original_db', models.ForeignKey(editable=False, to='dbsync.Database', null=True)),
            ],
            options={
                'ordering': ('descr',),
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Gentity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('original_id', models.IntegerField(null=True, editable=False, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=200, blank=True)),
                ('short_name', models.CharField(max_length=50, blank=True)),
                ('remarks', models.TextField(blank=True)),
                ('name_alt', models.CharField(max_length=200, blank=True)),
                ('short_name_alt', models.CharField(max_length=50, blank=True)),
                ('remarks_alt', models.TextField(blank=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name_plural': 'Gentities',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Garea',
            fields=[
                ('gentity_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hcore.Gentity')),
                ('area', models.FloatField(null=True, blank=True)),
                ('mpoly', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True)),
            ],
            options={
            },
            bases=('hcore.gentity',),
        ),
        migrations.CreateModel(
            name='GentityAltCode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('original_id', models.IntegerField(null=True, editable=False, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('value', models.CharField(max_length=100)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GentityAltCodeType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('original_id', models.IntegerField(null=True, editable=False, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('descr', models.CharField(max_length=200, blank=True)),
                ('descr_alt', models.CharField(max_length=200, blank=True)),
                ('original_db', models.ForeignKey(editable=False, to='dbsync.Database', null=True)),
            ],
            options={
                'ordering': ('descr',),
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GentityEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('original_id', models.IntegerField(null=True, editable=False, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('date', models.DateField()),
                ('user', models.CharField(max_length=64)),
                ('report', models.TextField(blank=True)),
                ('report_alt', models.TextField(blank=True)),
            ],
            options={
                'ordering': ['-date'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GentityFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('original_id', models.IntegerField(null=True, editable=False, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('date', models.DateField(null=True, blank=True)),
                ('content', models.FileField(upload_to=b'gentityfile')),
                ('descr', models.CharField(max_length=100)),
                ('remarks', models.TextField(blank=True)),
                ('descr_alt', models.CharField(max_length=100)),
                ('remarks_alt', models.TextField(blank=True)),
                ('file_type', models.ForeignKey(to='hcore.FileType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GentityGenericData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('original_id', models.IntegerField(null=True, editable=False, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('descr', models.CharField(max_length=100)),
                ('remarks', models.TextField(blank=True)),
                ('descr_alt', models.CharField(max_length=100)),
                ('remarks_alt', models.TextField(blank=True)),
                ('content', models.TextField(blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GentityGenericDataType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('original_id', models.IntegerField(null=True, editable=False, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('descr', models.CharField(max_length=200, blank=True)),
                ('descr_alt', models.CharField(max_length=200, blank=True)),
                ('file_extension', models.CharField(max_length=16)),
                ('original_db', models.ForeignKey(editable=False, to='dbsync.Database', null=True)),
            ],
            options={
                'ordering': ('descr',),
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Gline',
            fields=[
                ('gentity_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hcore.Gentity')),
                ('length', models.FloatField(null=True, blank=True)),
                ('linestring', django.contrib.gis.db.models.fields.LineStringField(srid=4326, null=True, blank=True)),
            ],
            options={
            },
            bases=('hcore.gentity',),
        ),
        migrations.CreateModel(
            name='Gpoint',
            fields=[
                ('gentity_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hcore.Gentity')),
                ('srid', models.IntegerField(null=True, blank=True)),
                ('approximate', models.BooleanField()),
                ('altitude', models.FloatField(null=True, blank=True)),
                ('asrid', models.IntegerField(null=True, blank=True)),
                ('point', django.contrib.gis.db.models.fields.PointField(srid=4326, null=True, blank=True)),
            ],
            options={
            },
            bases=('hcore.gentity',),
        ),
        migrations.CreateModel(
            name='Instrument',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('original_id', models.IntegerField(null=True, editable=False, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('manufacturer', models.CharField(max_length=50, blank=True)),
                ('model', models.CharField(max_length=50, blank=True)),
                ('is_active', models.BooleanField()),
                ('start_date', models.DateField(null=True, blank=True)),
                ('end_date', models.DateField(null=True, blank=True)),
                ('name', models.CharField(max_length=100, blank=True)),
                ('remarks', models.TextField(blank=True)),
                ('name_alt', models.CharField(max_length=100, blank=True)),
                ('remarks_alt', models.TextField(blank=True)),
                ('original_db', models.ForeignKey(editable=False, to='dbsync.Database', null=True)),
            ],
            options={
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InstrumentType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('original_id', models.IntegerField(null=True, editable=False, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('descr', models.CharField(max_length=200, blank=True)),
                ('descr_alt', models.CharField(max_length=200, blank=True)),
                ('original_db', models.ForeignKey(editable=False, to='dbsync.Database', null=True)),
            ],
            options={
                'ordering': ('descr',),
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IntervalType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('original_id', models.IntegerField(null=True, editable=False, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('descr', models.CharField(max_length=200, blank=True)),
                ('descr_alt', models.CharField(max_length=200, blank=True)),
                ('value', models.CharField(max_length=50)),
                ('original_db', models.ForeignKey(editable=False, to='dbsync.Database', null=True)),
            ],
            options={
                'ordering': ('descr',),
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Lentity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('original_id', models.IntegerField(null=True, editable=False, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('remarks', models.TextField(blank=True)),
                ('remarks_alt', models.TextField(blank=True)),
                ('ordering_string', models.CharField(max_length=255, null=True, editable=False, blank=True)),
            ],
            options={
                'ordering': ('ordering_string',),
                'verbose_name_plural': 'Lentities',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('lentity_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hcore.Lentity')),
                ('name', models.CharField(max_length=200, blank=True)),
                ('acronym', models.CharField(max_length=50, blank=True)),
                ('name_alt', models.CharField(max_length=200, blank=True)),
                ('acronym_alt', models.CharField(max_length=50, blank=True)),
            ],
            options={
                'ordering': ('name',),
            },
            bases=('hcore.lentity',),
        ),
        migrations.CreateModel(
            name='Overseer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('original_id', models.IntegerField(null=True, editable=False, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('is_current', models.BooleanField()),
                ('start_date', models.DateField(null=True, blank=True)),
                ('end_date', models.DateField(null=True, blank=True)),
                ('original_db', models.ForeignKey(editable=False, to='dbsync.Database', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('lentity_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hcore.Lentity')),
                ('last_name', models.CharField(max_length=100, blank=True)),
                ('first_name', models.CharField(max_length=100, blank=True)),
                ('middle_names', models.CharField(max_length=100, blank=True)),
                ('initials', models.CharField(max_length=20, blank=True)),
                ('last_name_alt', models.CharField(max_length=100, blank=True)),
                ('first_name_alt', models.CharField(max_length=100, blank=True)),
                ('middle_names_alt', models.CharField(max_length=100, blank=True)),
                ('initials_alt', models.CharField(max_length=20, blank=True)),
            ],
            options={
                'ordering': ('last_name', 'first_name'),
            },
            bases=('hcore.lentity',),
        ),
        migrations.CreateModel(
            name='PoliticalDivision',
            fields=[
                ('garea_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hcore.Garea')),
                ('code', models.CharField(max_length=5, blank=True)),
                ('parent', models.ForeignKey(blank=True, to='hcore.PoliticalDivision', null=True)),
            ],
            options={
            },
            bases=('hcore.garea',),
        ),
        migrations.CreateModel(
            name='Station',
            fields=[
                ('gpoint_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hcore.Gpoint')),
                ('is_automatic', models.BooleanField()),
                ('is_active', models.BooleanField()),
                ('start_date', models.DateField(null=True, blank=True)),
                ('end_date', models.DateField(null=True, blank=True)),
                ('copyright_holder', models.TextField()),
                ('copyright_years', models.CharField(max_length=10)),
                ('creator', models.ForeignKey(related_name='created_stations', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('maintainers', models.ManyToManyField(related_name='maintaining_stations', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
                ('overseers', models.ManyToManyField(related_name='stations_overseen', through='hcore.Overseer', to='hcore.Person')),
                ('owner', models.ForeignKey(related_name='owned_stations', to='hcore.Lentity')),
            ],
            options={
            },
            bases=('hcore.gpoint',),
        ),
        migrations.CreateModel(
            name='StationType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('original_id', models.IntegerField(null=True, editable=False, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('descr', models.CharField(max_length=200, blank=True)),
                ('descr_alt', models.CharField(max_length=200, blank=True)),
                ('original_db', models.ForeignKey(editable=False, to='dbsync.Database', null=True)),
            ],
            options={
                'ordering': ('descr',),
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Timeseries',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('original_id', models.IntegerField(null=True, editable=False, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=200, blank=True)),
                ('name_alt', models.CharField(default=b'', max_length=200, blank=True)),
                ('hidden', models.BooleanField(default=False)),
                ('precision', models.SmallIntegerField(null=True, blank=True)),
                ('remarks', models.TextField(blank=True)),
                ('remarks_alt', models.TextField(default=b'', blank=True)),
                ('nominal_offset_minutes', models.PositiveIntegerField(null=True, blank=True)),
                ('nominal_offset_months', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('actual_offset_minutes', models.IntegerField(null=True, blank=True)),
                ('actual_offset_months', models.SmallIntegerField(null=True, blank=True)),
            ],
            options={
                'ordering': ('hidden',),
                'verbose_name': 'Time Series',
                'verbose_name_plural': 'Time Series',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TimeStep',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('original_id', models.IntegerField(null=True, editable=False, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('descr', models.CharField(max_length=200, blank=True)),
                ('descr_alt', models.CharField(max_length=200, blank=True)),
                ('length_minutes', models.PositiveIntegerField()),
                ('length_months', models.PositiveSmallIntegerField()),
                ('original_db', models.ForeignKey(editable=False, to='dbsync.Database', null=True)),
            ],
            options={
                'ordering': ('descr',),
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TimeZone',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('original_id', models.IntegerField(null=True, editable=False, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('code', models.CharField(max_length=50)),
                ('utc_offset', models.SmallIntegerField()),
                ('original_db', models.ForeignKey(editable=False, to='dbsync.Database', null=True)),
            ],
            options={
                'ordering': ('utc_offset',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TsRecords',
            fields=[
                ('id', models.ForeignKey(primary_key=True, db_column=b'id', serialize=False, to='hcore.Timeseries')),
                ('top', models.TextField(blank=True)),
                ('middle', enhydris.hcore.models.BlobField(null=True, blank=True)),
                ('bottom', models.TextField()),
            ],
            options={
                'db_table': 'ts_records',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UnitOfMeasurement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('original_id', models.IntegerField(null=True, editable=False, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('descr', models.CharField(max_length=200, blank=True)),
                ('descr_alt', models.CharField(max_length=200, blank=True)),
                ('symbol', models.CharField(max_length=50)),
                ('original_db', models.ForeignKey(editable=False, to='dbsync.Database', null=True)),
            ],
            options={
                'ordering': ('descr',),
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('fname', models.CharField(max_length=30, null=True, verbose_name='First Name', blank=True)),
                ('lname', models.CharField(max_length=30, null=True, verbose_name='Last Name', blank=True)),
                ('address', models.CharField(max_length=100, null=True, verbose_name='Location', blank=True)),
                ('organization', models.CharField(max_length=100, null=True, verbose_name='Organization', blank=True)),
                ('email_is_public', models.BooleanField(default=False)),
                ('user', models.ForeignKey(verbose_name='Username', to=settings.AUTH_USER_MODEL, unique=True)),
            ],
            options={
                'verbose_name': 'Profile',
                'verbose_name_plural': 'Profiles',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Variable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('original_id', models.IntegerField(null=True, editable=False, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('descr', models.CharField(max_length=200, blank=True)),
                ('descr_alt', models.CharField(max_length=200, blank=True)),
                ('original_db', models.ForeignKey(editable=False, to='dbsync.Database', null=True)),
            ],
            options={
                'ordering': ('descr',),
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WaterBasin',
            fields=[
                ('garea_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hcore.Garea')),
                ('parent', models.ForeignKey(blank=True, to='hcore.WaterBasin', null=True)),
            ],
            options={
            },
            bases=('hcore.garea',),
        ),
        migrations.CreateModel(
            name='WaterDivision',
            fields=[
                ('garea_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hcore.Garea')),
            ],
            options={
            },
            bases=('hcore.garea',),
        ),
        migrations.AddField(
            model_name='waterbasin',
            name='water_division',
            field=models.ForeignKey(blank=True, to='hcore.WaterDivision', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='unitofmeasurement',
            name='variables',
            field=models.ManyToManyField(to='hcore.Variable'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='timeseries',
            name='gentity',
            field=models.ForeignKey(related_name='timeseries', to='hcore.Gentity'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='timeseries',
            name='instrument',
            field=models.ForeignKey(blank=True, to='hcore.Instrument', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='timeseries',
            name='interval_type',
            field=models.ForeignKey(blank=True, to='hcore.IntervalType', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='timeseries',
            name='original_db',
            field=models.ForeignKey(editable=False, to='dbsync.Database', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='timeseries',
            name='time_step',
            field=models.ForeignKey(blank=True, to='hcore.TimeStep', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='timeseries',
            name='time_zone',
            field=models.ForeignKey(to='hcore.TimeZone'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='timeseries',
            name='unit_of_measurement',
            field=models.ForeignKey(to='hcore.UnitOfMeasurement'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='timeseries',
            name='variable',
            field=models.ForeignKey(to='hcore.Variable'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='station',
            name='stype',
            field=models.ManyToManyField(to='hcore.StationType', verbose_name=b'type'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='overseer',
            name='person',
            field=models.ForeignKey(to='hcore.Person'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='overseer',
            name='station',
            field=models.ForeignKey(to='hcore.Station'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='lentity',
            name='original_db',
            field=models.ForeignKey(editable=False, to='dbsync.Database', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='instrument',
            name='station',
            field=models.ForeignKey(to='hcore.Station'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='instrument',
            name='type',
            field=models.ForeignKey(to='hcore.InstrumentType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gline',
            name='gpoint1',
            field=models.ForeignKey(related_name='glines1', blank=True, to='hcore.Gpoint', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gline',
            name='gpoint2',
            field=models.ForeignKey(related_name='glines2', blank=True, to='hcore.Gpoint', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gentitygenericdata',
            name='data_type',
            field=models.ForeignKey(to='hcore.GentityGenericDataType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gentitygenericdata',
            name='gentity',
            field=models.ForeignKey(to='hcore.Gentity'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gentitygenericdata',
            name='original_db',
            field=models.ForeignKey(editable=False, to='dbsync.Database', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gentityfile',
            name='gentity',
            field=models.ForeignKey(to='hcore.Gentity'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gentityfile',
            name='original_db',
            field=models.ForeignKey(editable=False, to='dbsync.Database', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gentityevent',
            name='gentity',
            field=models.ForeignKey(to='hcore.Gentity'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gentityevent',
            name='original_db',
            field=models.ForeignKey(editable=False, to='dbsync.Database', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gentityevent',
            name='type',
            field=models.ForeignKey(to='hcore.EventType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gentityaltcode',
            name='gentity',
            field=models.ForeignKey(to='hcore.Gentity'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gentityaltcode',
            name='original_db',
            field=models.ForeignKey(editable=False, to='dbsync.Database', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gentityaltcode',
            name='type',
            field=models.ForeignKey(to='hcore.GentityAltCodeType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gentity',
            name='original_db',
            field=models.ForeignKey(editable=False, to='dbsync.Database', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gentity',
            name='political_division',
            field=models.ForeignKey(blank=True, to='hcore.PoliticalDivision', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gentity',
            name='water_basin',
            field=models.ForeignKey(blank=True, to='hcore.WaterBasin', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gentity',
            name='water_division',
            field=models.ForeignKey(blank=True, to='hcore.WaterDivision', null=True),
            preserve_default=True,
        ),
    ]
