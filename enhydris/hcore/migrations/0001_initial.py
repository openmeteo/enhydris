
from south.db import db
from django.db import models
from enhydris.hcore.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'Overseer'
        db.create_table('hcore_overseer', (
            ('id', orm['hcore.Overseer:id']),
            ('station', orm['hcore.Overseer:station']),
            ('person', orm['hcore.Overseer:person']),
            ('is_current', orm['hcore.Overseer:is_current']),
            ('start_date', orm['hcore.Overseer:start_date']),
            ('end_date', orm['hcore.Overseer:end_date']),
        ))
        db.send_create_signal('hcore', ['Overseer'])
        
        # Adding model 'EventType'
        db.create_table('hcore_eventtype', (
            ('id', orm['hcore.EventType:id']),
            ('descr', orm['hcore.EventType:descr']),
            ('descr_alt', orm['hcore.EventType:descr_alt']),
        ))
        db.send_create_signal('hcore', ['EventType'])
        
        # Adding model 'InstrumentType'
        db.create_table('hcore_instrumenttype', (
            ('id', orm['hcore.InstrumentType:id']),
            ('descr', orm['hcore.InstrumentType:descr']),
            ('descr_alt', orm['hcore.InstrumentType:descr_alt']),
        ))
        db.send_create_signal('hcore', ['InstrumentType'])
        
        # Adding model 'Variable'
        db.create_table('hcore_variable', (
            ('id', orm['hcore.Variable:id']),
            ('descr', orm['hcore.Variable:descr']),
            ('descr_alt', orm['hcore.Variable:descr_alt']),
        ))
        db.send_create_signal('hcore', ['Variable'])
        
        # Adding model 'Gentity'
        db.create_table('hcore_gentity', (
            ('id', orm['hcore.Gentity:id']),
            ('water_basin', orm['hcore.Gentity:water_basin']),
            ('water_division', orm['hcore.Gentity:water_division']),
            ('political_division', orm['hcore.Gentity:political_division']),
            ('name', orm['hcore.Gentity:name']),
            ('short_name', orm['hcore.Gentity:short_name']),
            ('remarks', orm['hcore.Gentity:remarks']),
            ('name_alt', orm['hcore.Gentity:name_alt']),
            ('short_name_alt', orm['hcore.Gentity:short_name_alt']),
            ('remarks_alt', orm['hcore.Gentity:remarks_alt']),
        ))
        db.send_create_signal('hcore', ['Gentity'])
        
        # Adding model 'Gline'
        db.create_table('hcore_gline', (
            ('gentity_ptr', orm['hcore.Gline:gentity_ptr']),
            ('gpoint1', orm['hcore.Gline:gpoint1']),
            ('gpoint2', orm['hcore.Gline:gpoint2']),
            ('length', orm['hcore.Gline:length']),
        ))
        db.send_create_signal('hcore', ['Gline'])
        
        # Adding model 'TimeZone'
        db.create_table('hcore_timezone', (
            ('id', orm['hcore.TimeZone:id']),
            ('code', orm['hcore.TimeZone:code']),
            ('utc_offset', orm['hcore.TimeZone:utc_offset']),
        ))
        db.send_create_signal('hcore', ['TimeZone'])
        
        # Adding model 'Garea'
        db.create_table('hcore_garea', (
            ('gentity_ptr', orm['hcore.Garea:gentity_ptr']),
            ('area', orm['hcore.Garea:area']),
        ))
        db.send_create_signal('hcore', ['Garea'])
        
        # Adding model 'StationType'
        db.create_table('hcore_stationtype', (
            ('id', orm['hcore.StationType:id']),
            ('descr', orm['hcore.StationType:descr']),
            ('descr_alt', orm['hcore.StationType:descr_alt']),
        ))
        db.send_create_signal('hcore', ['StationType'])
        
        # Adding model 'UserProfile'
        db.create_table('hcore_userprofile', (
            ('id', orm['hcore.UserProfile:id']),
            ('user', orm['hcore.UserProfile:user']),
            ('fname', orm['hcore.UserProfile:fname']),
            ('lname', orm['hcore.UserProfile:lname']),
            ('address', orm['hcore.UserProfile:address']),
            ('organization', orm['hcore.UserProfile:organization']),
            ('is_public', orm['hcore.UserProfile:is_public']),
        ))
        db.send_create_signal('hcore', ['UserProfile'])
        
        # Adding model 'WaterDivision'
        db.create_table('hcore_waterdivision', (
            ('garea_ptr', orm['hcore.WaterDivision:garea_ptr']),
        ))
        db.send_create_signal('hcore', ['WaterDivision'])
        
        # Adding model 'Station'
        db.create_table('hcore_station', (
            ('gpoint_ptr', orm['hcore.Station:gpoint_ptr']),
            ('owner', orm['hcore.Station:owner']),
            ('type', orm['hcore.Station:type']),
            ('is_active', orm['hcore.Station:is_active']),
            ('is_automatic', orm['hcore.Station:is_automatic']),
            ('start_date', orm['hcore.Station:start_date']),
            ('end_date', orm['hcore.Station:end_date']),
        ))
        db.send_create_signal('hcore', ['Station'])
        
        # Adding model 'WaterBasin'
        db.create_table('hcore_waterbasin', (
            ('garea_ptr', orm['hcore.WaterBasin:garea_ptr']),
            ('parent', orm['hcore.WaterBasin:parent']),
            ('water_division', orm['hcore.WaterBasin:water_division']),
        ))
        db.send_create_signal('hcore', ['WaterBasin'])
        
        # Adding model 'Person'
        db.create_table('hcore_person', (
            ('lentity_ptr', orm['hcore.Person:lentity_ptr']),
            ('last_name', orm['hcore.Person:last_name']),
            ('first_name', orm['hcore.Person:first_name']),
            ('middle_names', orm['hcore.Person:middle_names']),
            ('initials', orm['hcore.Person:initials']),
            ('last_name_alt', orm['hcore.Person:last_name_alt']),
            ('first_name_alt', orm['hcore.Person:first_name_alt']),
            ('middle_names_alt', orm['hcore.Person:middle_names_alt']),
            ('initials_alt', orm['hcore.Person:initials_alt']),
        ))
        db.send_create_signal('hcore', ['Person'])
        
        # Adding model 'GentityEvent'
        db.create_table('hcore_gentityevent', (
            ('id', orm['hcore.GentityEvent:id']),
            ('gentity', orm['hcore.GentityEvent:gentity']),
            ('date', orm['hcore.GentityEvent:date']),
            ('type', orm['hcore.GentityEvent:type']),
            ('user', orm['hcore.GentityEvent:user']),
            ('report', orm['hcore.GentityEvent:report']),
            ('report_alt', orm['hcore.GentityEvent:report_alt']),
        ))
        db.send_create_signal('hcore', ['GentityEvent'])
        
        # Adding model 'Organization'
        db.create_table('hcore_organization', (
            ('lentity_ptr', orm['hcore.Organization:lentity_ptr']),
            ('name', orm['hcore.Organization:name']),
            ('acronym', orm['hcore.Organization:acronym']),
            ('name_alt', orm['hcore.Organization:name_alt']),
            ('acronym_alt', orm['hcore.Organization:acronym_alt']),
        ))
        db.send_create_signal('hcore', ['Organization'])
        
        # Adding model 'FileType'
        db.create_table('hcore_filetype', (
            ('id', orm['hcore.FileType:id']),
            ('descr', orm['hcore.FileType:descr']),
            ('descr_alt', orm['hcore.FileType:descr_alt']),
            ('mime_type', orm['hcore.FileType:mime_type']),
        ))
        db.send_create_signal('hcore', ['FileType'])
        
        # Adding model 'Lentity'
        db.create_table('hcore_lentity', (
            ('id', orm['hcore.Lentity:id']),
            ('remarks', orm['hcore.Lentity:remarks']),
            ('remarks_alt', orm['hcore.Lentity:remarks_alt']),
        ))
        db.send_create_signal('hcore', ['Lentity'])
        
        # Adding model 'GentityAltCodeType'
        db.create_table('hcore_gentityaltcodetype', (
            ('id', orm['hcore.GentityAltCodeType:id']),
            ('descr', orm['hcore.GentityAltCodeType:descr']),
            ('descr_alt', orm['hcore.GentityAltCodeType:descr_alt']),
        ))
        db.send_create_signal('hcore', ['GentityAltCodeType'])
        
        # Adding model 'Timeseries'
        db.create_table('hcore_timeseries', (
            ('id', orm['hcore.Timeseries:id']),
            ('gentity', orm['hcore.Timeseries:gentity']),
            ('variable', orm['hcore.Timeseries:variable']),
            ('unit_of_measurement', orm['hcore.Timeseries:unit_of_measurement']),
            ('name', orm['hcore.Timeseries:name']),
            ('precision', orm['hcore.Timeseries:precision']),
            ('time_zone', orm['hcore.Timeseries:time_zone']),
            ('remarks', orm['hcore.Timeseries:remarks']),
            ('instrument', orm['hcore.Timeseries:instrument']),
            ('time_step', orm['hcore.Timeseries:time_step']),
            ('nominal_offset_minutes', orm['hcore.Timeseries:nominal_offset_minutes']),
            ('nominal_offset_months', orm['hcore.Timeseries:nominal_offset_months']),
            ('actual_offset_minutes', orm['hcore.Timeseries:actual_offset_minutes']),
            ('actual_offset_months', orm['hcore.Timeseries:actual_offset_months']),
        ))
        db.send_create_signal('hcore', ['Timeseries'])
        
        # Adding model 'GentityFile'
        db.create_table('hcore_gentityfile', (
            ('id', orm['hcore.GentityFile:id']),
            ('gentity', orm['hcore.GentityFile:gentity']),
            ('date', orm['hcore.GentityFile:date']),
            ('file_type', orm['hcore.GentityFile:file_type']),
            ('content', orm['hcore.GentityFile:content']),
            ('descr', orm['hcore.GentityFile:descr']),
            ('remarks', orm['hcore.GentityFile:remarks']),
            ('descr_alt', orm['hcore.GentityFile:descr_alt']),
            ('remarks_alt', orm['hcore.GentityFile:remarks_alt']),
        ))
        db.send_create_signal('hcore', ['GentityFile'])
        
        # Adding model 'TimeStep'
        db.create_table('hcore_timestep', (
            ('id', orm['hcore.TimeStep:id']),
            ('descr', orm['hcore.TimeStep:descr']),
            ('descr_alt', orm['hcore.TimeStep:descr_alt']),
            ('length_minutes', orm['hcore.TimeStep:length_minutes']),
            ('length_months', orm['hcore.TimeStep:length_months']),
        ))
        db.send_create_signal('hcore', ['TimeStep'])
        
        # Adding model 'Gpoint'
        db.create_table('hcore_gpoint', (
            ('gentity_ptr', orm['hcore.Gpoint:gentity_ptr']),
            ('abscissa', orm['hcore.Gpoint:abscissa']),
            ('ordinate', orm['hcore.Gpoint:ordinate']),
            ('srid', orm['hcore.Gpoint:srid']),
            ('approximate', orm['hcore.Gpoint:approximate']),
            ('altitude', orm['hcore.Gpoint:altitude']),
            ('asrid', orm['hcore.Gpoint:asrid']),
        ))
        db.send_create_signal('hcore', ['Gpoint'])
        
        # Adding model 'PoliticalDivision'
        db.create_table('hcore_politicaldivision', (
            ('garea_ptr', orm['hcore.PoliticalDivision:garea_ptr']),
            ('parent', orm['hcore.PoliticalDivision:parent']),
            ('code', orm['hcore.PoliticalDivision:code']),
        ))
        db.send_create_signal('hcore', ['PoliticalDivision'])
        
        # Adding model 'GentityAltCode'
        db.create_table('hcore_gentityaltcode', (
            ('id', orm['hcore.GentityAltCode:id']),
            ('gentity', orm['hcore.GentityAltCode:gentity']),
            ('type', orm['hcore.GentityAltCode:type']),
            ('value', orm['hcore.GentityAltCode:value']),
        ))
        db.send_create_signal('hcore', ['GentityAltCode'])
        
        # Adding model 'Instrument'
        db.create_table('hcore_instrument', (
            ('id', orm['hcore.Instrument:id']),
            ('station', orm['hcore.Instrument:station']),
            ('type', orm['hcore.Instrument:type']),
            ('manufacturer', orm['hcore.Instrument:manufacturer']),
            ('model', orm['hcore.Instrument:model']),
            ('is_active', orm['hcore.Instrument:is_active']),
            ('start_date', orm['hcore.Instrument:start_date']),
            ('end_date', orm['hcore.Instrument:end_date']),
            ('name', orm['hcore.Instrument:name']),
            ('remarks', orm['hcore.Instrument:remarks']),
            ('name_alt', orm['hcore.Instrument:name_alt']),
            ('remarks_alt', orm['hcore.Instrument:remarks_alt']),
        ))
        db.send_create_signal('hcore', ['Instrument'])
        
        # Adding model 'UnitOfMeasurement'
        db.create_table('hcore_unitofmeasurement', (
            ('id', orm['hcore.UnitOfMeasurement:id']),
            ('descr', orm['hcore.UnitOfMeasurement:descr']),
            ('descr_alt', orm['hcore.UnitOfMeasurement:descr_alt']),
            ('symbol', orm['hcore.UnitOfMeasurement:symbol']),
        ))
        db.send_create_signal('hcore', ['UnitOfMeasurement'])
        
        # Adding ManyToManyField 'UnitOfMeasurement.variables'
        db.create_table('hcore_unitofmeasurement_variables', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('unitofmeasurement', models.ForeignKey(orm.UnitOfMeasurement, null=False)),
            ('variable', models.ForeignKey(orm.Variable, null=False))
        ))
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'Overseer'
        db.delete_table('hcore_overseer')
        
        # Deleting model 'EventType'
        db.delete_table('hcore_eventtype')
        
        # Deleting model 'InstrumentType'
        db.delete_table('hcore_instrumenttype')
        
        # Deleting model 'Variable'
        db.delete_table('hcore_variable')
        
        # Deleting model 'Gentity'
        db.delete_table('hcore_gentity')
        
        # Deleting model 'Gline'
        db.delete_table('hcore_gline')
        
        # Deleting model 'TimeZone'
        db.delete_table('hcore_timezone')
        
        # Deleting model 'Garea'
        db.delete_table('hcore_garea')
        
        # Deleting model 'StationType'
        db.delete_table('hcore_stationtype')
        
        # Deleting model 'UserProfile'
        db.delete_table('hcore_userprofile')
        
        # Deleting model 'WaterDivision'
        db.delete_table('hcore_waterdivision')
        
        # Deleting model 'Station'
        db.delete_table('hcore_station')
        
        # Deleting model 'WaterBasin'
        db.delete_table('hcore_waterbasin')
        
        # Deleting model 'Person'
        db.delete_table('hcore_person')
        
        # Deleting model 'GentityEvent'
        db.delete_table('hcore_gentityevent')
        
        # Deleting model 'Organization'
        db.delete_table('hcore_organization')
        
        # Deleting model 'FileType'
        db.delete_table('hcore_filetype')
        
        # Deleting model 'Lentity'
        db.delete_table('hcore_lentity')
        
        # Deleting model 'GentityAltCodeType'
        db.delete_table('hcore_gentityaltcodetype')
        
        # Deleting model 'Timeseries'
        db.delete_table('hcore_timeseries')
        
        # Deleting model 'GentityFile'
        db.delete_table('hcore_gentityfile')
        
        # Deleting model 'TimeStep'
        db.delete_table('hcore_timestep')
        
        # Deleting model 'Gpoint'
        db.delete_table('hcore_gpoint')
        
        # Deleting model 'PoliticalDivision'
        db.delete_table('hcore_politicaldivision')
        
        # Deleting model 'GentityAltCode'
        db.delete_table('hcore_gentityaltcode')
        
        # Deleting model 'Instrument'
        db.delete_table('hcore_instrument')
        
        # Deleting model 'UnitOfMeasurement'
        db.delete_table('hcore_unitofmeasurement')
        
        # Dropping ManyToManyField 'UnitOfMeasurement.variables'
        db.delete_table('hcore_unitofmeasurement_variables')
        
    
    
    models = {
        'auth.group': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'hcore.eventtype': {
            'descr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'descr_alt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'hcore.filetype': {
            'descr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'descr_alt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mime_type': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'hcore.garea': {
            'area': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'gentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Gentity']", 'unique': 'True', 'primary_key': 'True'})
        },
        'hcore.gentity': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'name_alt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'political_division': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.PoliticalDivision']", 'null': 'True', 'blank': 'True'}),
            'remarks': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'remarks_alt': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'short_name_alt': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'water_basin': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.WaterBasin']", 'null': 'True', 'blank': 'True'}),
            'water_division': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.WaterDivision']", 'null': 'True', 'blank': 'True'})
        },
        'hcore.gentityaltcode': {
            'gentity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.Gentity']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.GentityAltCodeType']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'hcore.gentityaltcodetype': {
            'descr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'descr_alt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'hcore.gentityevent': {
            'date': ('django.db.models.fields.DateField', [], {}),
            'gentity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.Gentity']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'report': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'report_alt': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.EventType']"}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'hcore.gentityfile': {
            'content': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'descr': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'descr_alt': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'file_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.FileType']"}),
            'gentity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.Gentity']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'remarks': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'remarks_alt': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'hcore.gline': {
            'gentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Gentity']", 'unique': 'True', 'primary_key': 'True'}),
            'gpoint1': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'glines1'", 'null': 'True', 'to': "orm['hcore.Gpoint']"}),
            'gpoint2': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'glines2'", 'null': 'True', 'to': "orm['hcore.Gpoint']"}),
            'length': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
        'hcore.gpoint': {
            'abscissa': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'altitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'approximate': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'asrid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'gentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Gentity']", 'unique': 'True', 'primary_key': 'True'}),
            'ordinate': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'srid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'hcore.instrument': {
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'manufacturer': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'name_alt': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'remarks': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'remarks_alt': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'station': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.Station']"}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.InstrumentType']"})
        },
        'hcore.instrumenttype': {
            'descr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'descr_alt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'hcore.lentity': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'remarks': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'remarks_alt': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'hcore.organization': {
            'acronym': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'acronym_alt': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'lentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Lentity']", 'unique': 'True', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'name_alt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        },
        'hcore.overseer': {
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_current': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.Person']"}),
            'start_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'station': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.Station']"})
        },
        'hcore.person': {
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'first_name_alt': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'initials': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'initials_alt': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'last_name_alt': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'lentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Lentity']", 'unique': 'True', 'primary_key': 'True'}),
            'middle_names': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'middle_names_alt': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        'hcore.politicaldivision': {
            'code': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True'}),
            'garea_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Garea']", 'unique': 'True', 'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.PoliticalDivision']", 'null': 'True', 'blank': 'True'})
        },
        'hcore.station': {
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gpoint_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Gpoint']", 'unique': 'True', 'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_automatic': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'overseers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['hcore.Person']"}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.Lentity']"}),
            'start_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.StationType']"})
        },
        'hcore.stationtype': {
            'descr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'descr_alt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'hcore.timeseries': {
            'actual_offset_minutes': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'actual_offset_months': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'gentity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.Gentity']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instrument': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.Instrument']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'nominal_offset_minutes': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'nominal_offset_months': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'precision': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'remarks': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'time_step': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.TimeStep']", 'null': 'True', 'blank': 'True'}),
            'time_zone': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.TimeZone']"}),
            'unit_of_measurement': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.UnitOfMeasurement']"}),
            'variable': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.Variable']"})
        },
        'hcore.timestep': {
            'descr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'descr_alt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'length_minutes': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'length_months': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        'hcore.timezone': {
            'code': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'utc_offset': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        'hcore.unitofmeasurement': {
            'descr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'descr_alt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'symbol': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'variables': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['hcore.Variable']"})
        },
        'hcore.userprofile': {
            'address': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'fname': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'lname': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'organization': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'hcore.variable': {
            'descr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'descr_alt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'hcore.waterbasin': {
            'garea_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Garea']", 'unique': 'True', 'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.WaterBasin']", 'null': 'True', 'blank': 'True'}),
            'water_division': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.WaterDivision']", 'null': 'True', 'blank': 'True'})
        },
        'hcore.waterdivision': {
            'garea_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Garea']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['hcore']
