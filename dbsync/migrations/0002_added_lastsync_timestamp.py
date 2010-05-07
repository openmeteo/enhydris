
from south.db import db
from django.db import models
from enhydris.dbsync.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding field 'Database.last_sync'
        db.add_column('dbsync_database', 'last_sync', orm['dbsync.database:last_sync'])
        
    
    
    def backwards(self, orm):
        
        # Deleting field 'Database.last_sync'
        db.delete_column('dbsync_database', 'last_sync')
        
    
    
    models = {
        'dbsync.database': {
            'descr': ('django.db.models.fields.TextField', [], {'max_length': '255', 'blank': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'last_sync': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'})
        }
    }
    
    complete_apps = ['dbsync']
