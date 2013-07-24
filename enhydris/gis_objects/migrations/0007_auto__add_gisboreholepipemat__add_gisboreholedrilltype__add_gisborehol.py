# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'GISBoreholePipeMat'
        db.create_table('gis_objects_gisboreholepipemat', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('descr', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('descr_alt', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
        ))
        db.send_create_signal('gis_objects', ['GISBoreholePipeMat'])

        # Adding model 'GISBoreholeDrillType'
        db.create_table('gis_objects_gisboreholedrilltype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('descr', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('descr_alt', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
        ))
        db.send_create_signal('gis_objects', ['GISBoreholeDrillType'])

        # Adding model 'GISBoreholePmeterType'
        db.create_table('gis_objects_gisboreholepmetertype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('descr', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('descr_alt', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
        ))
        db.send_create_signal('gis_objects', ['GISBoreholePmeterType'])

        # Adding field 'GISBorehole.has_pmeter'
        db.add_column('gis_objects_gisborehole', 'has_pmeter', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Adding field 'GISBorehole.pmeter_type'
        db.add_column('gis_objects_gisborehole', 'pmeter_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gis_objects.GISBoreholePmeterType'], null=True, blank=True), keep_default=False)

        # Adding field 'GISBorehole.pmeter_length'
        db.add_column('gis_objects_gisborehole', 'pmeter_length', self.gf('django.db.models.fields.FloatField')(null=True, blank=True), keep_default=False)

        # Adding field 'GISBorehole.pmeter_diameter'
        db.add_column('gis_objects_gisborehole', 'pmeter_diameter', self.gf('django.db.models.fields.FloatField')(null=True, blank=True), keep_default=False)

        # Adding field 'GISBorehole.borehole_depth'
        db.add_column('gis_objects_gisborehole', 'borehole_depth', self.gf('django.db.models.fields.FloatField')(null=True, blank=True), keep_default=False)

        # Adding field 'GISBorehole.pipe_depth'
        db.add_column('gis_objects_gisborehole', 'pipe_depth', self.gf('django.db.models.fields.FloatField')(null=True, blank=True), keep_default=False)

        # Adding field 'GISBorehole.water_depth'
        db.add_column('gis_objects_gisborehole', 'water_depth', self.gf('django.db.models.fields.FloatField')(null=True, blank=True), keep_default=False)

        # Adding field 'GISBorehole.value_t'
        db.add_column('gis_objects_gisborehole', 'value_t', self.gf('django.db.models.fields.FloatField')(null=True, blank=True), keep_default=False)

        # Adding field 'GISBorehole.value_s'
        db.add_column('gis_objects_gisborehole', 'value_s', self.gf('django.db.models.fields.FloatField')(null=True, blank=True), keep_default=False)

        # Adding field 'GISBorehole.value_b'
        db.add_column('gis_objects_gisborehole', 'value_b', self.gf('django.db.models.fields.FloatField')(null=True, blank=True), keep_default=False)

        # Adding field 'GISBorehole.value_k'
        db.add_column('gis_objects_gisborehole', 'value_k', self.gf('django.db.models.fields.FloatField')(null=True, blank=True), keep_default=False)

        # Adding field 'GISBorehole.threshold_a'
        db.add_column('gis_objects_gisborehole', 'threshold_a', self.gf('django.db.models.fields.FloatField')(null=True, blank=True), keep_default=False)

        # Adding field 'GISBorehole.threshold_b'
        db.add_column('gis_objects_gisborehole', 'threshold_b', self.gf('django.db.models.fields.FloatField')(null=True, blank=True), keep_default=False)

        # Adding field 'GISBorehole.continuous_stage'
        db.add_column('gis_objects_gisborehole', 'continuous_stage', self.gf('django.db.models.fields.FloatField')(null=True, blank=True), keep_default=False)

        # Adding field 'GISBorehole.test_flow'
        db.add_column('gis_objects_gisborehole', 'test_flow', self.gf('django.db.models.fields.FloatField')(null=True, blank=True), keep_default=False)

        # Adding field 'GISBorehole.test_stage'
        db.add_column('gis_objects_gisborehole', 'test_stage', self.gf('django.db.models.fields.FloatField')(null=True, blank=True), keep_default=False)

        # Adding field 'GISBorehole.begin_works'
        db.add_column('gis_objects_gisborehole', 'begin_works', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True), keep_default=False)

        # Adding field 'GISBorehole.end_works'
        db.add_column('gis_objects_gisborehole', 'end_works', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True), keep_default=False)

        # Adding field 'GISBorehole.drill_type'
        db.add_column('gis_objects_gisborehole', 'drill_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gis_objects.GISBoreholeDrillType'], null=True, blank=True), keep_default=False)

        # Adding field 'GISBorehole.pipe_mat'
        db.add_column('gis_objects_gisborehole', 'pipe_mat', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gis_objects.GISBoreholePipeMat'], null=True, blank=True), keep_default=False)

        # Adding field 'GISBorehole.pump_discharge'
        db.add_column('gis_objects_gisborehole', 'pump_discharge', self.gf('django.db.models.fields.FloatField')(null=True, blank=True), keep_default=False)

        # Adding field 'GISBorehole.pump_ratio'
        db.add_column('gis_objects_gisborehole', 'pump_ratio', self.gf('django.db.models.fields.FloatField')(null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting model 'GISBoreholePipeMat'
        db.delete_table('gis_objects_gisboreholepipemat')

        # Deleting model 'GISBoreholeDrillType'
        db.delete_table('gis_objects_gisboreholedrilltype')

        # Deleting model 'GISBoreholePmeterType'
        db.delete_table('gis_objects_gisboreholepmetertype')

        # Deleting field 'GISBorehole.has_pmeter'
        db.delete_column('gis_objects_gisborehole', 'has_pmeter')

        # Deleting field 'GISBorehole.pmeter_type'
        db.delete_column('gis_objects_gisborehole', 'pmeter_type_id')

        # Deleting field 'GISBorehole.pmeter_length'
        db.delete_column('gis_objects_gisborehole', 'pmeter_length')

        # Deleting field 'GISBorehole.pmeter_diameter'
        db.delete_column('gis_objects_gisborehole', 'pmeter_diameter')

        # Deleting field 'GISBorehole.borehole_depth'
        db.delete_column('gis_objects_gisborehole', 'borehole_depth')

        # Deleting field 'GISBorehole.pipe_depth'
        db.delete_column('gis_objects_gisborehole', 'pipe_depth')

        # Deleting field 'GISBorehole.water_depth'
        db.delete_column('gis_objects_gisborehole', 'water_depth')

        # Deleting field 'GISBorehole.value_t'
        db.delete_column('gis_objects_gisborehole', 'value_t')

        # Deleting field 'GISBorehole.value_s'
        db.delete_column('gis_objects_gisborehole', 'value_s')

        # Deleting field 'GISBorehole.value_b'
        db.delete_column('gis_objects_gisborehole', 'value_b')

        # Deleting field 'GISBorehole.value_k'
        db.delete_column('gis_objects_gisborehole', 'value_k')

        # Deleting field 'GISBorehole.threshold_a'
        db.delete_column('gis_objects_gisborehole', 'threshold_a')

        # Deleting field 'GISBorehole.threshold_b'
        db.delete_column('gis_objects_gisborehole', 'threshold_b')

        # Deleting field 'GISBorehole.continuous_stage'
        db.delete_column('gis_objects_gisborehole', 'continuous_stage')

        # Deleting field 'GISBorehole.test_flow'
        db.delete_column('gis_objects_gisborehole', 'test_flow')

        # Deleting field 'GISBorehole.test_stage'
        db.delete_column('gis_objects_gisborehole', 'test_stage')

        # Deleting field 'GISBorehole.begin_works'
        db.delete_column('gis_objects_gisborehole', 'begin_works')

        # Deleting field 'GISBorehole.end_works'
        db.delete_column('gis_objects_gisborehole', 'end_works')

        # Deleting field 'GISBorehole.drill_type'
        db.delete_column('gis_objects_gisborehole', 'drill_type_id')

        # Deleting field 'GISBorehole.pipe_mat'
        db.delete_column('gis_objects_gisborehole', 'pipe_mat_id')

        # Deleting field 'GISBorehole.pump_discharge'
        db.delete_column('gis_objects_gisborehole', 'pump_discharge')

        # Deleting field 'GISBorehole.pump_ratio'
        db.delete_column('gis_objects_gisborehole', 'pump_ratio')


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
            'entity_type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'exs': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'gisentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gis_objects.GISEntity']", 'unique': 'True'}),
            'gline_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Gline']", 'unique': 'True', 'primary_key': 'True'}),
            'q': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'remarks': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'type_name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'})
        },
        'gis_objects.gisaqueductnode': {
            'Meta': {'ordering': "('name',)", 'object_name': 'GISAqueductNode', '_ormbases': ['hcore.Gpoint', 'gis_objects.GISEntity']},
            'entity_type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'gisentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gis_objects.GISEntity']", 'unique': 'True'}),
            'gpoint_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Gpoint']", 'unique': 'True', 'primary_key': 'True'}),
            'type_name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'})
        },
        'gis_objects.gisborehole': {
            'Meta': {'ordering': "('name',)", 'object_name': 'GISBorehole', '_ormbases': ['gis_objects.GISBoreholeSpring', 'gis_objects.GISEntity']},
            'begin_works': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'borehole_depth': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'code': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'continuous_stage': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'drill_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['gis_objects.GISBoreholeDrillType']", 'null': 'True', 'blank': 'True'}),
            'end_works': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'gisboreholespring_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gis_objects.GISBoreholeSpring']", 'unique': 'True', 'primary_key': 'True'}),
            'gisentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gis_objects.GISEntity']", 'unique': 'True'}),
            'group': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'}),
            'has_pmeter': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'pipe_depth': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'pipe_mat': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['gis_objects.GISBoreholePipeMat']", 'null': 'True', 'blank': 'True'}),
            'pmeter_diameter': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'pmeter_length': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'pmeter_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['gis_objects.GISBoreholePmeterType']", 'null': 'True', 'blank': 'True'}),
            'pump_discharge': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'pump_ratio': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'test_flow': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'test_stage': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'threshold_a': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'threshold_b': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'value_b': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'value_k': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'value_s': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'value_t': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'water_depth': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
        'gis_objects.gisboreholedrilltype': {
            'Meta': {'ordering': "('descr',)", 'object_name': 'GISBoreholeDrillType'},
            'descr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'descr_alt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'gis_objects.gisboreholepipemat': {
            'Meta': {'ordering': "('descr',)", 'object_name': 'GISBoreholePipeMat'},
            'descr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'descr_alt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'gis_objects.gisboreholepmetertype': {
            'Meta': {'ordering': "('descr',)", 'object_name': 'GISBoreholePmeterType'},
            'descr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'descr_alt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
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
            'entity_type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'generator_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'generator_discharge': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'generator_energy': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'generator_num': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'gisentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gis_objects.GISEntity']", 'unique': 'True'}),
            'gpoint_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Gpoint']", 'unique': 'True', 'primary_key': 'True'}),
            'is_generator': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_irrig': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_pump': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'pump_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'pump_discharge': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'pump_energy': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'pump_num': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'pump_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['gis_objects.GISPumpType']", 'null': 'True', 'blank': 'True'}),
            'total_power': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
        'gis_objects.gispumptype': {
            'Meta': {'ordering': "('descr',)", 'object_name': 'GISPumpType'},
            'descr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'descr_alt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
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
            'dead_volume': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'entity_type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'garea_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Garea']", 'unique': 'True', 'primary_key': 'True'}),
            'gisentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gis_objects.GISEntity']", 'unique': 'True'}),
            'inflow_max': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'inflow_mean': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'inflow_min': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'runoff_max': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'runoff_mean': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'runoff_min': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'volume_max': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
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
