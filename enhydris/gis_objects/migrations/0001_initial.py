# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'GISEntity'
        db.create_table('gis_objects_gisentity', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('gis_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('original_gentity_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('gtype', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gis_objects.GISEntityType'], null=True, blank=True)),
        ))
        db.send_create_signal('gis_objects', ['GISEntity'])

        # Adding model 'GISEntityType'
        db.create_table('gis_objects_gisentitytype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('descr', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('descr_alt', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
        ))
        db.send_create_signal('gis_objects', ['GISEntityType'])

        # Adding model 'GISBoreholeSpring'
        db.create_table('gis_objects_gisboreholespring', (
            ('gpoint_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['hcore.Gpoint'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('gis_objects', ['GISBoreholeSpring'])

        # Adding model 'GISBorehole'
        db.create_table('gis_objects_gisborehole', (
            ('gisentity_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['gis_objects.GISEntity'], unique=True)),
            ('gisboreholespring_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['gis_objects.GISBoreholeSpring'], unique=True, primary_key=True)),
            ('code', self.gf('django.db.models.fields.IntegerField')(blank=True)),
            ('group', self.gf('django.db.models.fields.CharField')(max_length=80, blank=True)),
        ))
        db.send_create_signal('gis_objects', ['GISBorehole'])

        # Adding model 'GISPump'
        db.create_table('gis_objects_gispump', (
            ('gisentity_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['gis_objects.GISEntity'], unique=True)),
            ('gpoint_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['hcore.Gpoint'], unique=True, primary_key=True)),
            ('entity_type', self.gf('django.db.models.fields.IntegerField')(blank=True)),
        ))
        db.send_create_signal('gis_objects', ['GISPump'])

        # Adding model 'GISRefinery'
        db.create_table('gis_objects_gisrefinery', (
            ('gisentity_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['gis_objects.GISEntity'], unique=True)),
            ('gpoint_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['hcore.Gpoint'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('gis_objects', ['GISRefinery'])

        # Adding model 'GISSpring'
        db.create_table('gis_objects_gisspring', (
            ('gisentity_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['gis_objects.GISEntity'], unique=True)),
            ('gisboreholespring_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['gis_objects.GISBoreholeSpring'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('gis_objects', ['GISSpring'])

        # Adding model 'GISAqueductNode'
        db.create_table('gis_objects_gisaqueductnode', (
            ('gisentity_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['gis_objects.GISEntity'], unique=True)),
            ('gpoint_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['hcore.Gpoint'], unique=True, primary_key=True)),
            ('entity_type', self.gf('django.db.models.fields.IntegerField')(blank=True)),
            ('type_name', self.gf('django.db.models.fields.CharField')(max_length=80, blank=True)),
        ))
        db.send_create_signal('gis_objects', ['GISAqueductNode'])

        # Adding model 'GISAqueductLine'
        db.create_table('gis_objects_gisaqueductline', (
            ('gisentity_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['gis_objects.GISEntity'], unique=True)),
            ('gline_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['hcore.Gline'], unique=True, primary_key=True)),
            ('entity_type', self.gf('django.db.models.fields.IntegerField')(blank=True)),
            ('q', self.gf('django.db.models.fields.FloatField')(blank=True)),
            ('exs', self.gf('django.db.models.fields.IntegerField')(blank=True)),
            ('remarks', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('type_name', self.gf('django.db.models.fields.CharField')(max_length=80, blank=True)),
        ))
        db.send_create_signal('gis_objects', ['GISAqueductLine'])

        # Adding model 'GISReservoir'
        db.create_table('gis_objects_gisreservoir', (
            ('gisentity_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['gis_objects.GISEntity'], unique=True)),
            ('garea_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['hcore.Garea'], unique=True, primary_key=True)),
            ('entity_type', self.gf('django.db.models.fields.IntegerField')(blank=True)),
        ))
        db.send_create_signal('gis_objects', ['GISReservoir'])


    def backwards(self, orm):
        
        # Deleting model 'GISEntity'
        db.delete_table('gis_objects_gisentity')

        # Deleting model 'GISEntityType'
        db.delete_table('gis_objects_gisentitytype')

        # Deleting model 'GISBoreholeSpring'
        db.delete_table('gis_objects_gisboreholespring')

        # Deleting model 'GISBorehole'
        db.delete_table('gis_objects_gisborehole')

        # Deleting model 'GISPump'
        db.delete_table('gis_objects_gispump')

        # Deleting model 'GISRefinery'
        db.delete_table('gis_objects_gisrefinery')

        # Deleting model 'GISSpring'
        db.delete_table('gis_objects_gisspring')

        # Deleting model 'GISAqueductNode'
        db.delete_table('gis_objects_gisaqueductnode')

        # Deleting model 'GISAqueductLine'
        db.delete_table('gis_objects_gisaqueductline')

        # Deleting model 'GISReservoir'
        db.delete_table('gis_objects_gisreservoir')


    models = {
        'dbsync.database': {
            'Meta': {'object_name': 'Database'},
            'descr': ('django.db.models.fields.TextField', [], {'max_length': '255', 'blank': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'last_sync': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'})
        },
        'gis_objects.gisaqueductline': {
            'Meta': {'ordering': "('name',)", 'object_name': 'GISAqueductLine', '_ormbases': ['hcore.Gline', 'gis_objects.GISEntity']},
            'entity_type': ('django.db.models.fields.IntegerField', [], {'blank': 'True'}),
            'exs': ('django.db.models.fields.IntegerField', [], {'blank': 'True'}),
            'gisentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gis_objects.GISEntity']", 'unique': 'True'}),
            'gline_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Gline']", 'unique': 'True', 'primary_key': 'True'}),
            'q': ('django.db.models.fields.FloatField', [], {'blank': 'True'}),
            'remarks': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'type_name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'})
        },
        'gis_objects.gisaqueductnode': {
            'Meta': {'ordering': "('name',)", 'object_name': 'GISAqueductNode', '_ormbases': ['hcore.Gpoint', 'gis_objects.GISEntity']},
            'entity_type': ('django.db.models.fields.IntegerField', [], {'blank': 'True'}),
            'gisentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gis_objects.GISEntity']", 'unique': 'True'}),
            'gpoint_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Gpoint']", 'unique': 'True', 'primary_key': 'True'}),
            'type_name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'})
        },
        'gis_objects.gisborehole': {
            'Meta': {'ordering': "('name',)", 'object_name': 'GISBorehole', '_ormbases': ['gis_objects.GISBoreholeSpring', 'gis_objects.GISEntity']},
            'code': ('django.db.models.fields.IntegerField', [], {'blank': 'True'}),
            'gisboreholespring_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gis_objects.GISBoreholeSpring']", 'unique': 'True', 'primary_key': 'True'}),
            'gisentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gis_objects.GISEntity']", 'unique': 'True'}),
            'group': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'})
        },
        'gis_objects.gisboreholespring': {
            'Meta': {'ordering': "('name',)", 'object_name': 'GISBoreholeSpring', '_ormbases': ['hcore.Gpoint']},
            'gpoint_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Gpoint']", 'unique': 'True', 'primary_key': 'True'})
        },
        'gis_objects.gisentity': {
            'Meta': {'object_name': 'GISEntity'},
            'gis_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'gtype': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['gis_objects.GISEntityType']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'original_gentity_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'gis_objects.gisentitytype': {
            'Meta': {'ordering': "('descr',)", 'object_name': 'GISEntityType'},
            'descr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'descr_alt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'gis_objects.gispump': {
            'Meta': {'ordering': "('name',)", 'object_name': 'GISPump', '_ormbases': ['hcore.Gpoint', 'gis_objects.GISEntity']},
            'entity_type': ('django.db.models.fields.IntegerField', [], {'blank': 'True'}),
            'gisentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gis_objects.GISEntity']", 'unique': 'True'}),
            'gpoint_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Gpoint']", 'unique': 'True', 'primary_key': 'True'})
        },
        'gis_objects.gisrefinery': {
            'Meta': {'ordering': "('name',)", 'object_name': 'GISRefinery', '_ormbases': ['hcore.Gpoint', 'gis_objects.GISEntity']},
            'gisentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gis_objects.GISEntity']", 'unique': 'True'}),
            'gpoint_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Gpoint']", 'unique': 'True', 'primary_key': 'True'})
        },
        'gis_objects.gisreservoir': {
            'Meta': {'ordering': "('name',)", 'object_name': 'GISReservoir', '_ormbases': ['hcore.Garea', 'gis_objects.GISEntity']},
            'entity_type': ('django.db.models.fields.IntegerField', [], {'blank': 'True'}),
            'garea_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Garea']", 'unique': 'True', 'primary_key': 'True'}),
            'gisentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gis_objects.GISEntity']", 'unique': 'True'})
        },
        'gis_objects.gisspring': {
            'Meta': {'ordering': "('name',)", 'object_name': 'GISSpring', '_ormbases': ['gis_objects.GISBoreholeSpring', 'gis_objects.GISEntity']},
            'gisboreholespring_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gis_objects.GISBoreholeSpring']", 'unique': 'True', 'primary_key': 'True'}),
            'gisentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gis_objects.GISEntity']", 'unique': 'True'})
        },
        'hcore.garea': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Garea', '_ormbases': ['hcore.Gentity']},
            'area': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'gentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Gentity']", 'unique': 'True', 'primary_key': 'True'}),
            'mpoly': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {'null': 'True', 'blank': 'True'})
        },
        'hcore.gentity': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Gentity'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
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
        'hcore.gline': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Gline', '_ormbases': ['hcore.Gentity']},
            'gentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Gentity']", 'unique': 'True', 'primary_key': 'True'}),
            'gpoint1': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'glines1'", 'null': 'True', 'to': "orm['hcore.Gpoint']"}),
            'gpoint2': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'glines2'", 'null': 'True', 'to': "orm['hcore.Gpoint']"}),
            'length': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'linestring': ('django.contrib.gis.db.models.fields.LineStringField', [], {'null': 'True', 'blank': 'True'})
        },
        'hcore.gpoint': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Gpoint', '_ormbases': ['hcore.Gentity']},
            'altitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'approximate': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'asrid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'gentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Gentity']", 'unique': 'True', 'primary_key': 'True'}),
            'point': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True', 'blank': 'True'}),
            'srid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'hcore.politicaldivision': {
            'Meta': {'ordering': "('name',)", 'object_name': 'PoliticalDivision', '_ormbases': ['hcore.Garea']},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True'}),
            'garea_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Garea']", 'unique': 'True', 'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.PoliticalDivision']", 'null': 'True', 'blank': 'True'})
        },
        'hcore.waterbasin': {
            'Meta': {'ordering': "('name',)", 'object_name': 'WaterBasin', '_ormbases': ['hcore.Garea']},
            'garea_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Garea']", 'unique': 'True', 'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.WaterBasin']", 'null': 'True', 'blank': 'True'}),
            'water_division': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hcore.WaterDivision']", 'null': 'True', 'blank': 'True'})
        },
        'hcore.waterdivision': {
            'Meta': {'ordering': "('name',)", 'object_name': 'WaterDivision', '_ormbases': ['hcore.Garea']},
            'garea_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Garea']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['gis_objects']
