# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Topic'
        db.create_table('hfaq_topic', (
            ('slug', self.gf('django.db.models.fields.CharField')(unique=True, max_length=80)),
            ('order', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name_alt', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('hfaq', ['Topic'])

        # Adding model 'Item'
        db.create_table('hfaq_item', (
            ('answer_alt', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('question', self.gf('django.db.models.fields.TextField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('topic', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hfaq.Topic'])),
            ('question_alt', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('published', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('answer', self.gf('django.db.models.fields.TextField')()),
            ('order', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('hfaq', ['Item'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Topic'
        db.delete_table('hfaq_topic')

        # Deleting model 'Item'
        db.delete_table('hfaq_item')
    
    
    models = {
        'hfaq.item': {
            'Meta': {'object_name': 'Item'},
            'answer': ('django.db.models.fields.TextField', [], {}),
            'answer_alt': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'question': ('django.db.models.fields.TextField', [], {}),
            'question_alt': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hfaq.Topic']"})
        },
        'hfaq.topic': {
            'Meta': {'object_name': 'Topic'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'name_alt': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'})
        }
    }
    
    complete_apps = ['hfaq']
