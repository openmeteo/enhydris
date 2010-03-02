
from south.db import db
from django.db import models
from enhydris.dbsync.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'Database'
        db.create_table('dbsync_database', (
            ('id', orm['dbsync.Database:id']),
            ('name', orm['dbsync.Database:name']),
            ('ip_address', orm['dbsync.Database:ip_address']),
            ('hostname', orm['dbsync.Database:hostname']),
            ('descr', orm['dbsync.Database:descr']),
        ))
        db.send_create_signal('dbsync', ['Database'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'Database'
        db.delete_table('dbsync_database')
        
    
    
    models = {
        'dbsync.database': {
            'descr': ('django.db.models.fields.TextField', [], {'max_length': '255', 'blank': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'})
        }
    }
    
    complete_apps = ['dbsync']
