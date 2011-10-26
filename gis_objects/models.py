from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from enhydris.hcore.models import Gpoint, Gline, Garea
import sys

models_lst = ['GISBorehole', 'GISPump', 'GISRefinery',
              'GISSpring', 'GISAqueductNode',
              'GISAqueductLine', 'GISReservoir',]

class Lookup(models.Model):
    descr = models.CharField(max_length=200, blank=True)
    descr_alt = models.CharField(max_length=200, blank=True)
    class Meta:
        abstract = True
        ordering = ('descr',)

    def __unicode__(self):
        return self.descr or self.descr_alt

class GISEntity(models.Model):
    gis_id = models.IntegerField(blank=True, null=True)
    original_gentity_id = models.IntegerField(blank=True, null=True)
    gtype = models.ForeignKey('GISEntityType', blank=True, null=True)
#   Geo manager is needed for some geo filtering operations
    objects = models.GeoManager()
    def gis_model(self):
        model = getattr(sys.modules[__name__], models_lst[self.gtype.id-1])
        try:
            return model.objects.get(gisentity_ptr=self.id)
        except model.DoesNotExist:
            return None
    def name(self):
        self.gis_model().name

class GISEntityType(Lookup): pass

class GISBoreholeSpring(Gpoint):
    water_use = models.ForeignKey('GISBoreholeSpringWaterUse',
                                  blank=True, null=True)
    water_user = models.ForeignKey('GISBoreholeSpringWaterUser',
                                  blank=True, null=True)
    land_use = models.ForeignKey('GISBoreholeSpringLandUse',
                                  blank=True, null=True)
    continuous_flow = models.FloatField(blank=True, null=True)

class GISBoreholeSpringWaterUse(Lookup):  pass
class GISBoreholeSpringWaterUser(Lookup): pass
class GISBoreholeSpringLandUse(Lookup):   pass

class GISBorehole(GISBoreholeSpring, GISEntity):
    code = models.IntegerField(blank=True, null=True)
    group = models.CharField(max_length=80, blank=True)
    objects = models.GeoManager()
    has_pmeter = models.BooleanField(default=False)
    pmeter_type = models.ForeignKey('GISBoreholePmeterType',
                                    blank=True, null=True)
    pmeter_length = models.FloatField(blank=True, null=True)
    pmeter_diameter = models.FloatField(blank=True, null=True)
    borehole_depth = models.FloatField(blank=True, null=True)
    pipe_depth = models.FloatField(blank=True, null=True)
    water_depth = models.FloatField(blank=True, null=True)
    value_t = models.FloatField(blank=True, null=True)
    value_s = models.FloatField(blank=True, null=True)
    value_b = models.FloatField(blank=True, null=True)
    value_k = models.FloatField(blank=True, null=True)
    threshold_a = models.FloatField(blank=True, null=True)
    threshold_b = models.FloatField(blank=True, null=True)
    continuous_stage = models.FloatField(blank=True, null=True)
    test_flow = models.FloatField(blank=True, null=True)
    test_stage = models.FloatField(blank=True, null=True)
    begin_works = models.DateTimeField(blank=True, null=True)
    end_works = models.DateTimeField(blank=True, null=True)
    drill_type = models.ForeignKey('GISBoreholeDrillType',
                                   blank=True, null=True)
    pipe_mat = models.ForeignKey('GISBoreholePipeMat',
                                 blank=True, null=True)
    pump_discharge = models.FloatField(blank=True, null=True)
    pump_ratio = models.FloatField(blank=True, null=True)

    def __unicode__(self):
        return self.name or 'id=%d'%(self.id,)
    def save(self, *args, **kwargs):
        self.gtype = GISEntityType.objects.get(pk=1)
        super(GISBorehole, self).save(*args, **kwargs)
    def extra_info(self):
        return _('Borehole group: ')+self.group

class GISBoreholePmeterType(Lookup): pass
class GISBoreholeDrillType(Lookup): pass
class GISBoreholePipeMat(Lookup): pass

class GISPump(Gpoint, GISEntity):
    entity_type = models.IntegerField(blank=True, null=True)
    pump_type = models.ForeignKey('GISPumpType', blank=True, null=True);
    is_irrig = models.BooleanField(default=False)
    is_pump = models.BooleanField(default=False)
    pump_active = models.BooleanField(default=False)
    is_generator = models.BooleanField(default=False)
    generator_active = models.BooleanField(default=False)
    pump_num = models.IntegerField(blank=True, null=True)
    pump_discharge = models.FloatField(blank=True, null=True)
    generator_num = models.IntegerField(blank=True, null=True)
    total_power = models.FloatField(blank=True, null=True)
    generator_discharge = models.FloatField(blank=True, null=True)
    pump_energy = models.FloatField(blank=True, null=True)
    generator_energy = models.FloatField(blank=True, null=True)
    objects = models.GeoManager()
    def __unicode__(self):
        return self.name or 'id=%d'%(self.id,)
    def save(self, *args, **kwargs):
        self.gtype = GISEntityType.objects.get(pk=2)
        super(GISPump, self).save(*args, **kwargs)
    def extra_info(self):
        return _('Pump active') if self.pump_active else ''

class GISPumpType(Lookup): pass

class GISRefinery(Gpoint, GISEntity):
    capacity = models.FloatField(blank=True, null=True)
    peak_capacity = models.FloatField(blank=True, null=True)
    storage = models.FloatField(blank=True, null=True)
    overflow_stage = models.FloatField(blank=True, null=True)
    outlet_level = models.FloatField(blank=True, null=True)
    objects = models.GeoManager()
    def __unicode__(self):
        return self.name or 'id=%d'%(self.id,)
    def save(self, *args, **kwargs):
        self.gtype = GISEntityType.objects.get(pk=3)
        super(GISRefinery, self).save(*args, **kwargs)
    def extra_info(self):
        return _('Capacity: ')+str(self.capacity)

class GISSpring(GISBoreholeSpring, GISEntity):
    dstype = models.ForeignKey('GISSpringDstype', 
                               null=True, blank=True)
    hgeo_info = models.ForeignKey('GISSpringHgeoInfo',
                               null=True, blank=True)
    is_continuous = models.BooleanField(default=False)
    objects = models.GeoManager()
    def __unicode__(self):
        return self.name or 'id=%d'%(self.id,)
    def save(self, *args, **kwargs):
        self.gtype = GISEntityType.objects.get(pk=4)
        super(GISSpring, self).save(*args, **kwargs)
    def extra_info(self):
        return _('Spring type: ')+self.dstype.descr

class GISSpringDstype(Lookup): pass
class GISSpringHgeoInfo(Lookup): pass

class GISAqueductNode(Gpoint, GISEntity):
    entity_type = models.IntegerField(blank=True, null=True)
    type_name = models.CharField(max_length=80, blank=True)
    measure_discharge = models.BooleanField(default=False)
    measure_stage = models.BooleanField(default=False)
    start_position = models.FloatField(blank=True, null=True)
    end_position = models.FloatField(blank=True, null=True)
    duct_segment_type = models.ForeignKey('GISDuctSegmentType',
                                          blank=True, null=True)
    duct_status = models.ForeignKey('GISDuctStatusType',
                                    blank=True, null=True)
    repers = models.CharField(max_length=40, blank=True)
    repers_en = models.CharField(max_length=40, blank=True)
    group = models.ForeignKey('GISAqueductGroup', blank=True,
                              null=True)
    objects = models.GeoManager()
    def __unicode__(self):
        return self.name or 'id=%d'%(self.id,)
    def save(self, *args, **kwargs):
        self.gtype = GISEntityType.objects.get(pk=5)
        super(GISAqueductNode, self).save(*args, **kwargs)
    def extra_info(self):
        if self.group:
            return _('In aqueduct group: ')+self.group.descr
        else:
            return ''

class GISAqueductLine(Gline, GISEntity):
    entity_type = models.IntegerField(blank=True, null=True)
    q = models.FloatField(blank=True, null=True)
    exs = models.IntegerField(blank=True, null=True)
    remarks = models.TextField(blank=True)
    type_name = models.CharField(max_length=80, blank=True)
    group = models.ForeignKey('GISAqueductGroup', blank=True,
                              null=True)
    xsection = models.ForeignKey('GISXSection', blank=True,
                                 null=True)
    area = models.FloatField(blank=True, null=True)
    width = models.FloatField(blank=True, null=True)
    depth = models.FloatField(blank=True, null=True)
    slope = models.FloatField(blank=True, null=True)
    roughness_coef = models.FloatField(blank=True, null=True)
    roughness_coef_type = models.ForeignKey('GISRoughnessCoefType',
                                            blank=True, null=True)
    bank_slope = models.FloatField(blank=True, null=True)
    leakage_coef = models.FloatField(blank=True, null=True)
    measure_discharge = models.BooleanField(default=False)
    measure_stage = models.BooleanField(default=False)
    start_position = models.FloatField(blank=True, null=True)
    end_position = models.FloatField(blank=True, null=True)
    duct_segment_type = models.ForeignKey('GISDuctSegmentType',
                                          blank=True, null=True)
    discharge_capacity = models.FloatField(blank=True, null=True)
    duct_flow_type = models.ForeignKey('GISDuctFlowType',
                                       blank=True, null=True)
    duct_status = models.ForeignKey('GISDuctStatusType',
                                    blank=True, null=True)
    repers = models.CharField(max_length=40, blank=True)
    repers_en = models.CharField(max_length=40, blank=True)
    pipe_mat = models.ForeignKey('GISBoreholePipeMat',
                                 blank=True, null=True)
    alt1 = models.FloatField(blank=True, null=True)
    alt2 = models.FloatField(blank=True, null=True)
    objects = models.GeoManager()
    def __unicode__(self):
        return self.name or 'id=%d'%(self.id,)
    def save(self, *args, **kwargs):
        self.gtype = GISEntityType.objects.get(pk=6)
        super(GISAqueductLine, self).save(*args, **kwargs)
    def extra_info(self):
        if self.group:
            return _('In aqueduct group: ')+self.group.descr
        else:
            return ''

GENTITYFILEDIR = settings.GENTITYFILE_DIR

class GISXSection(models.Model):
    xsection_type = models.ForeignKey('GISXSectionType', blank=True,
                                      null=True)
    closed = models.BooleanField(default=False)
    dimensions = models.CharField(blank=True, max_length=40)
    drawing_file = models.FileField(upload_to=GENTITYFILEDIR)
    def __unicode__(self):
        return 'XSection with id=%d, %s, %s'%(self.id, 
                            self.xsection_type.descr, self.dimensions)

class GISAqueductGroup(Lookup): pass
class GISXSectionType(Lookup): pass
class GISDuctSegmentType(Lookup): pass
class GISDuctFlowType(Lookup): pass
class GISDuctStatusType(Lookup): pass
class GISRoughnessCoefType(Lookup): pass

class GISReservoir(Garea, GISEntity):
    entity_type = models.IntegerField(blank=True, null=True)
    inflow_mean = models.FloatField(blank=True, null=True)
    inflow_max = models.FloatField(blank=True, null=True)
    inflow_min = models.FloatField(blank=True, null=True)
    runoff_mean = models.FloatField(blank=True, null=True)
    runoff_max = models.FloatField(blank=True, null=True)
    runoff_min = models.FloatField(blank=True, null=True)
    volume_max = models.FloatField(blank=True, null=True)
    dead_volume = models.FloatField(blank=True, null=True)
    objects = models.GeoManager()
    def __unicode__(self):
        return self.name or 'id=%d'%(self.id,)
    def save(self, *args, **kwargs):
        self.gtype = GISEntityType.objects.get(pk=7)
        super(GISReservoir, self).save(*args, **kwargs)
    def extra_info(self):
        return _('Area: ')+str(self.area)

