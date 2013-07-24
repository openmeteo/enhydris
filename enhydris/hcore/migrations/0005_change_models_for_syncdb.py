
from south.db import db
from django.db import models
from enhydris.hcore.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding field 'GentityAltCode.original_db'
        db.add_column('hcore_gentityaltcode', 'original_db', orm['hcore.gentityaltcode:original_db'])
        
        # Adding field 'GentityFile.original_db'
        db.add_column('hcore_gentityfile', 'original_db', orm['hcore.gentityfile:original_db'])
        
        # Adding field 'Instrument.original_db'
        db.add_column('hcore_instrument', 'original_db', orm['hcore.instrument:original_db'])
        
        # Adding field 'Gentity.original_db'
        db.add_column('hcore_gentity', 'original_db', orm['hcore.gentity:original_db'])
        
        # Adding field 'TimeZone.original_db'
        db.add_column('hcore_timezone', 'original_db', orm['hcore.timezone:original_db'])
        
        # Adding field 'Overseer.original_db'
        db.add_column('hcore_overseer', 'original_db', orm['hcore.overseer:original_db'])
        
        # Adding field 'Timeseries.original_db'
        db.add_column('hcore_timeseries', 'original_db', orm['hcore.timeseries:original_db'])
        
        # Adding field 'GentityEvent.original_db'
        db.add_column('hcore_gentityevent', 'original_db', orm['hcore.gentityevent:original_db'])
        
        # Adding field 'Lentity.original_db'
        db.add_column('hcore_lentity', 'original_db', orm['hcore.lentity:original_db'])
        
        # Deleting field 'InstrumentType.original_site'
        db.delete_column('hcore_instrumenttype', 'original_site')
        
        # Deleting field 'GentityAltCodeType.original_site'
        db.delete_column('hcore_gentityaltcodetype', 'original_site')
        
        # Deleting field 'TimeStep.original_site'
        db.delete_column('hcore_timestep', 'original_site')
        
        # Deleting field 'UnitOfMeasurement.original_id'
        db.delete_column('hcore_unitofmeasurement', 'original_id')
        
        # Deleting field 'TimeZone.original_site'
        db.delete_column('hcore_timezone', 'original_site')
        
        # Deleting field 'Overseer.original_site'
        db.delete_column('hcore_overseer', 'original_site')
        
        # Deleting field 'Lentity.original_site'
        db.delete_column('hcore_lentity', 'original_site')
        
        # Deleting field 'FileType.original_id'
        db.delete_column('hcore_filetype', 'original_id')
        
        # Deleting field 'Variable.original_site'
        db.delete_column('hcore_variable', 'original_site')
        
        # Deleting field 'EventType.original_site'
        db.delete_column('hcore_eventtype', 'original_site')
        
        # Deleting field 'StationType.original_site'
        db.delete_column('hcore_stationtype', 'original_site')
        
        # Deleting field 'InstrumentType.original_id'
        db.delete_column('hcore_instrumenttype', 'original_id')
        
        # Deleting field 'GentityAltCodeType.original_id'
        db.delete_column('hcore_gentityaltcodetype', 'original_id')
        
        # Deleting field 'Timeseries.original_site'
        db.delete_column('hcore_timeseries', 'original_site')
        
        # Deleting field 'UnitOfMeasurement.original_site'
        db.delete_column('hcore_unitofmeasurement', 'original_site')
        
        # Deleting field 'GentityFile.original_site'
        db.delete_column('hcore_gentityfile', 'original_site')
        
        # Deleting field 'Variable.original_id'
        db.delete_column('hcore_variable', 'original_id')
        
        # Deleting field 'Instrument.original_site'
        db.delete_column('hcore_instrument', 'original_site')
        
        # Deleting field 'FileType.original_site'
        db.delete_column('hcore_filetype', 'original_site')
        
        # Deleting field 'TimeStep.original_id'
        db.delete_column('hcore_timestep', 'original_id')
        
        # Deleting field 'GentityEvent.original_site'
        db.delete_column('hcore_gentityevent', 'original_site')
        
        # Deleting field 'EventType.original_id'
        db.delete_column('hcore_eventtype', 'original_id')
        
        # Deleting field 'StationType.original_id'
        db.delete_column('hcore_stationtype', 'original_id')
        
        # Deleting field 'GentityAltCode.original_site'
        db.delete_column('hcore_gentityaltcode', 'original_site')
        
        # Deleting field 'Gentity.original_site'
        db.delete_column('hcore_gentity', 'original_site')
        
    
    
    def backwards(self, orm):
        
        # Deleting field 'GentityAltCode.original_db'
        db.delete_column('hcore_gentityaltcode', 'original_db_id')
        
        # Deleting field 'GentityFile.original_db'
        db.delete_column('hcore_gentityfile', 'original_db_id')
        
        # Deleting field 'Instrument.original_db'
        db.delete_column('hcore_instrument', 'original_db_id')
        
        # Deleting field 'Gentity.original_db'
        db.delete_column('hcore_gentity', 'original_db_id')
        
        # Deleting field 'TimeZone.original_db'
        db.delete_column('hcore_timezone', 'original_db_id')
        
        # Deleting field 'Overseer.original_db'
        db.delete_column('hcore_overseer', 'original_db_id')
        
        # Deleting field 'Timeseries.original_db'
        db.delete_column('hcore_timeseries', 'original_db_id')
        
        # Deleting field 'GentityEvent.original_db'
        db.delete_column('hcore_gentityevent', 'original_db_id')
        
        # Deleting field 'Lentity.original_db'
        db.delete_column('hcore_lentity', 'original_db_id')
        
        # Adding field 'InstrumentType.original_site'
        db.add_column('hcore_instrumenttype', 'original_site', orm['hcore.instrumenttype:original_site'])
        
        # Adding field 'GentityAltCodeType.original_site'
        db.add_column('hcore_gentityaltcodetype', 'original_site', orm['hcore.gentityaltcodetype:original_site'])
        
        # Adding field 'TimeStep.original_site'
        db.add_column('hcore_timestep', 'original_site', orm['hcore.timestep:original_site'])
        
        # Adding field 'UnitOfMeasurement.original_id'
        db.add_column('hcore_unitofmeasurement', 'original_id', orm['hcore.unitofmeasurement:original_id'])
        
        # Adding field 'TimeZone.original_site'
        db.add_column('hcore_timezone', 'original_site', orm['hcore.timezone:original_site'])
        
        # Adding field 'Overseer.original_site'
        db.add_column('hcore_overseer', 'original_site', orm['hcore.overseer:original_site'])
        
        # Adding field 'Lentity.original_site'
        db.add_column('hcore_lentity', 'original_site', orm['hcore.lentity:original_site'])
        
        # Adding field 'FileType.original_id'
        db.add_column('hcore_filetype', 'original_id', orm['hcore.filetype:original_id'])
        
        # Adding field 'Variable.original_site'
        db.add_column('hcore_variable', 'original_site', orm['hcore.variable:original_site'])
        
        # Adding field 'EventType.original_site'
        db.add_column('hcore_eventtype', 'original_site', orm['hcore.eventtype:original_site'])
        
        # Adding field 'StationType.original_site'
        db.add_column('hcore_stationtype', 'original_site', orm['hcore.stationtype:original_site'])
        
        # Adding field 'InstrumentType.original_id'
        db.add_column('hcore_instrumenttype', 'original_id', orm['hcore.instrumenttype:original_id'])
        
        # Adding field 'GentityAltCodeType.original_id'
        db.add_column('hcore_gentityaltcodetype', 'original_id', orm['hcore.gentityaltcodetype:original_id'])
        
        # Adding field 'Timeseries.original_site'
        db.add_column('hcore_timeseries', 'original_site', orm['hcore.timeseries:original_site'])
        
        # Adding field 'UnitOfMeasurement.original_site'
        db.add_column('hcore_unitofmeasurement', 'original_site', orm['hcore.unitofmeasurement:original_site'])
        
        # Adding field 'GentityFile.original_site'
        db.add_column('hcore_gentityfile', 'original_site', orm['hcore.gentityfile:original_site'])
        
        # Adding field 'Variable.original_id'
        db.add_column('hcore_variable', 'original_id', orm['hcore.variable:original_id'])
        
        # Adding field 'Instrument.original_site'
        db.add_column('hcore_instrument', 'original_site', orm['hcore.instrument:original_site'])
        
        # Adding field 'FileType.original_site'
        db.add_column('hcore_filetype', 'original_site', orm['hcore.filetype:original_site'])
        
        # Adding field 'TimeStep.original_id'
        db.add_column('hcore_timestep', 'original_id', orm['hcore.timestep:original_id'])
        
        # Adding field 'GentityEvent.original_site'
        db.add_column('hcore_gentityevent', 'original_site', orm['hcore.gentityevent:original_site'])
        
        # Adding field 'EventType.original_id'
        db.add_column('hcore_eventtype', 'original_id', orm['hcore.eventtype:original_id'])
        
        # Adding field 'StationType.original_id'
        db.add_column('hcore_stationtype', 'original_id', orm['hcore.stationtype:original_id'])
        
        # Adding field 'GentityAltCode.original_site'
        db.add_column('hcore_gentityaltcode', 'original_site', orm['hcore.gentityaltcode:original_site'])
        
        # Adding field 'Gentity.original_site'
        db.add_column('hcore_gentity', 'original_site', orm['hcore.gentity:original_site'])
        
    
    
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
        'dbsync.database': {
            'Meta': {'unique_together': "(('db_name', 'ip_address'),)"},
            'db_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'descr': ('django.db.models.fields.TextField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'})
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
            'original_db': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dbsync.Database']", 'null': 'True'}),
            'original_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
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
            'original_db': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dbsync.Database']", 'null': 'True'}),
            'original_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
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
            'original_db': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dbsync.Database']", 'null': 'True'}),
            'original_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
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
            'original_db': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dbsync.Database']", 'null': 'True'}),
            'original_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
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
            'original_db': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dbsync.Database']", 'null': 'True'}),
            'original_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
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
            'original_db': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dbsync.Database']", 'null': 'True'}),
            'original_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
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
            'original_db': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dbsync.Database']", 'null': 'True'}),
            'original_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
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
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_stations'", 'null': 'True', 'to': "orm['auth.User']"}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gpoint_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Gpoint']", 'unique': 'True', 'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_automatic': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'maintainers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
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
            'original_db': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dbsync.Database']", 'null': 'True'}),
            'original_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
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
            'original_db': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dbsync.Database']", 'null': 'True'}),
            'original_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
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
            'fname': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lname': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
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
