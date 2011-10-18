# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'GISSpringDstype'
        db.create_table('gis_objects_gisspringdstype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('descr', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('descr_alt', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
        ))
        db.send_create_signal('gis_objects', ['GISSpringDstype'])

        # Adding model 'GISBoreholeSpringWaterUse'
        db.create_table('gis_objects_gisboreholespringwateruse', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('descr', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('descr_alt', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
        ))
        db.send_create_signal('gis_objects', ['GISBoreholeSpringWaterUse'])

        # Adding model 'GISBoreholeSpringWaterUser'
        db.create_table('gis_objects_gisboreholespringwateruser', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('descr', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('descr_alt', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
        ))
        db.send_create_signal('gis_objects', ['GISBoreholeSpringWaterUser'])

        # Adding model 'GISSpringHgeoInfo'
        db.create_table('gis_objects_gisspringhgeoinfo', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('descr', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('descr_alt', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
        ))
        db.send_create_signal('gis_objects', ['GISSpringHgeoInfo'])

        # Adding model 'GISBoreholeSpringLandUse'
        db.create_table('gis_objects_gisboreholespringlanduse', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('descr', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('descr_alt', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
        ))
        db.send_create_signal('gis_objects', ['GISBoreholeSpringLandUse'])

        # Adding field 'GISBoreholeSpring.water_use'
        db.add_column('gis_objects_gisboreholespring', 'water_use', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gis_objects.GISBoreholeSpringWaterUse'], null=True, blank=True), keep_default=False)

        # Adding field 'GISBoreholeSpring.water_user'
        db.add_column('gis_objects_gisboreholespring', 'water_user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gis_objects.GISBoreholeSpringWaterUser'], null=True, blank=True), keep_default=False)

        # Adding field 'GISBoreholeSpring.land_use'
        db.add_column('gis_objects_gisboreholespring', 'land_use', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gis_objects.GISBoreholeSpringLandUse'], null=True, blank=True), keep_default=False)

        # Adding field 'GISBoreholeSpring.continuous_flow'
        db.add_column('gis_objects_gisboreholespring', 'continuous_flow', self.gf('django.db.models.fields.FloatField')(null=True, blank=True), keep_default=False)

        # Adding field 'GISSpring.dstype'
        db.add_column('gis_objects_gisspring', 'dstype', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gis_objects.GISSpringDstype'], null=True, blank=True), keep_default=False)

        # Adding field 'GISSpring.hgeo_info'
        db.add_column('gis_objects_gisspring', 'hgeo_info', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gis_objects.GISSpringHgeoInfo'], null=True, blank=True), keep_default=False)

        # Adding field 'GISSpring.is_continuous'
        db.add_column('gis_objects_gisspring', 'is_continuous', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)


    def backwards(self, orm):
        
        # Deleting model 'GISSpringDstype'
        db.delete_table('gis_objects_gisspringdstype')

        # Deleting model 'GISBoreholeSpringWaterUse'
        db.delete_table('gis_objects_gisboreholespringwateruse')

        # Deleting model 'GISBoreholeSpringWaterUser'
        db.delete_table('gis_objects_gisboreholespringwateruser')

        # Deleting model 'GISSpringHgeoInfo'
        db.delete_table('gis_objects_gisspringhgeoinfo')

        # Deleting model 'GISBoreholeSpringLandUse'
        db.delete_table('gis_objects_gisboreholespringlanduse')

        # Deleting field 'GISBoreholeSpring.water_use'
        db.delete_column('gis_objects_gisboreholespring', 'water_use_id')

        # Deleting field 'GISBoreholeSpring.water_user'
        db.delete_column('gis_objects_gisboreholespring', 'water_user_id')

        # Deleting field 'GISBoreholeSpring.land_use'
        db.delete_column('gis_objects_gisboreholespring', 'land_use_id')

        # Deleting field 'GISBoreholeSpring.continuous_flow'
        db.delete_column('gis_objects_gisboreholespring', 'continuous_flow')

        # Deleting field 'GISSpring.dstype'
        db.delete_column('gis_objects_gisspring', 'dstype_id')

        # Deleting field 'GISSpring.hgeo_info'
        db.delete_column('gis_objects_gisspring', 'hgeo_info_id')

        # Deleting field 'GISSpring.is_continuous'
        db.delete_column('gis_objects_gisspring', 'is_continuous')


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
            'continuous_flow': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'gpoint_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Gpoint']", 'unique': 'True', 'primary_key': 'True'}),
            'land_use': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['gis_objects.GISBoreholeSpringLandUse']", 'null': 'True', 'blank': 'True'}),
            'water_use': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['gis_objects.GISBoreholeSpringWaterUse']", 'null': 'True', 'blank': 'True'}),
            'water_user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['gis_objects.GISBoreholeSpringWaterUser']", 'null': 'True', 'blank': 'True'})
        },
        'gis_objects.gisboreholespringlanduse': {
            'Meta': {'ordering': "('descr',)", 'object_name': 'GISBoreholeSpringLandUse'},
            'descr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'descr_alt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'gis_objects.gisboreholespringwateruse': {
            'Meta': {'ordering': "('descr',)", 'object_name': 'GISBoreholeSpringWaterUse'},
            'descr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'descr_alt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'gis_objects.gisboreholespringwateruser': {
            'Meta': {'ordering': "('descr',)", 'object_name': 'GISBoreholeSpringWaterUser'},
            'descr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'descr_alt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
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
            'capacity': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'gisentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gis_objects.GISEntity']", 'unique': 'True'}),
            'gpoint_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Gpoint']", 'unique': 'True', 'primary_key': 'True'}),
            'outlet_level': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'overflow_stage': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'peak_capacity': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'storage': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
        'gis_objects.gisreservoir': {
            'Meta': {'ordering': "('name',)", 'object_name': 'GISReservoir', '_ormbases': ['hcore.Garea', 'gis_objects.GISEntity']},
            'entity_type': ('django.db.models.fields.IntegerField', [], {'blank': 'True'}),
            'garea_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Garea']", 'unique': 'True', 'primary_key': 'True'}),
            'gisentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gis_objects.GISEntity']", 'unique': 'True'})
        },
        'gis_objects.gisspring': {
            'Meta': {'ordering': "('name',)", 'object_name': 'GISSpring', '_ormbases': ['gis_objects.GISBoreholeSpring', 'gis_objects.GISEntity']},
            'dstype': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['gis_objects.GISSpringDstype']", 'null': 'True', 'blank': 'True'}),
            'gisboreholespring_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gis_objects.GISBoreholeSpring']", 'unique': 'True', 'primary_key': 'True'}),
            'gisentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gis_objects.GISEntity']", 'unique': 'True'}),
            'hgeo_info': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['gis_objects.GISSpringHgeoInfo']", 'null': 'True', 'blank': 'True'}),
            'is_continuous': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'gis_objects.gisspringdstype': {
            'Meta': {'ordering': "('descr',)", 'object_name': 'GISSpringDstype'},
            'descr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'descr_alt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'gis_objects.gisspringhgeoinfo': {
            'Meta': {'ordering': "('descr',)", 'object_name': 'GISSpringHgeoInfo'},
            'descr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'descr_alt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
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
