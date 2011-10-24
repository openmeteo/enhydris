# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'GISAqueductNode.group'
        db.add_column('gis_objects_gisaqueductnode', 'group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gis_objects.GISAqueductGroup'], null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'GISAqueductNode.group'
        db.delete_column('gis_objects_gisaqueductnode', 'group_id')


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
        'gis_objects.gisaqueductgroup': {
            'Meta': {'ordering': "('descr',)", 'object_name': 'GISAqueductGroup'},
            'descr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'descr_alt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'gis_objects.gisaqueductline': {
            'Meta': {'ordering': "('name',)", 'object_name': 'GISAqueductLine', '_ormbases': ['hcore.Gline', 'gis_objects.GISEntity']},
            'alt1': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'alt2': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'area': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'bank_slope': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'depth': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'discharge_capacity': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'duct_flow_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['gis_objects.GISDuctFlowType']", 'null': 'True', 'blank': 'True'}),
            'duct_segment_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['gis_objects.GISDuctSegmentType']", 'null': 'True', 'blank': 'True'}),
            'duct_status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['gis_objects.GISDuctStatusType']", 'null': 'True', 'blank': 'True'}),
            'end_position': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'entity_type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'exs': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'gisentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gis_objects.GISEntity']", 'unique': 'True'}),
            'gline_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Gline']", 'unique': 'True', 'primary_key': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['gis_objects.GISAqueductGroup']", 'null': 'True', 'blank': 'True'}),
            'leakage_coef': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'measure_discharge': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'measure_stage': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'pipe_mat': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['gis_objects.GISBoreholePipeMat']", 'null': 'True', 'blank': 'True'}),
            'q': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'remarks': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'repers': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'repers_en': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'roughness_coef': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'roughness_coef_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['gis_objects.GISRoughnessCoefType']", 'null': 'True', 'blank': 'True'}),
            'slope': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'start_position': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'type_name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'}),
            'width': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'xsection': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['gis_objects.GISXSection']", 'null': 'True', 'blank': 'True'})
        },
        'gis_objects.gisaqueductnode': {
            'Meta': {'ordering': "('name',)", 'object_name': 'GISAqueductNode', '_ormbases': ['hcore.Gpoint', 'gis_objects.GISEntity']},
            'duct_segment_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['gis_objects.GISDuctSegmentType']", 'null': 'True', 'blank': 'True'}),
            'duct_status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['gis_objects.GISDuctStatusType']", 'null': 'True', 'blank': 'True'}),
            'end_position': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'entity_type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'gisentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gis_objects.GISEntity']", 'unique': 'True'}),
            'gpoint_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hcore.Gpoint']", 'unique': 'True', 'primary_key': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['gis_objects.GISAqueductGroup']", 'null': 'True', 'blank': 'True'}),
            'measure_discharge': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'measure_stage': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'repers': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'repers_en': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'start_position': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
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
        'gis_objects.gisductflowtype': {
            'Meta': {'ordering': "('descr',)", 'object_name': 'GISDuctFlowType'},
            'descr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'descr_alt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'gis_objects.gisductsegmenttype': {
            'Meta': {'ordering': "('descr',)", 'object_name': 'GISDuctSegmentType'},
            'descr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'descr_alt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'gis_objects.gisductstatustype': {
            'Meta': {'ordering': "('descr',)", 'object_name': 'GISDuctStatusType'},
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
        'gis_objects.gisroughnesscoeftype': {
            'Meta': {'ordering': "('descr',)", 'object_name': 'GISRoughnessCoefType'},
            'descr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'descr_alt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
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
        'gis_objects.gisxsection': {
            'Meta': {'object_name': 'GISXSection'},
            'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'dimensions': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'drawing_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'xsection_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['gis_objects.GISXSectionType']", 'null': 'True', 'blank': 'True'})
        },
        'gis_objects.gisxsectiontype': {
            'Meta': {'ordering': "('descr',)", 'object_name': 'GISXSectionType'},
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
