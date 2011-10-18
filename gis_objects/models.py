from django.contrib.gis.db import models
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
    def gis_model(self):
        model = getattr(sys.modules[__name__], models_lst[self.gtype.id-1])
        try:
            return model.objects.get(gisentity_ptr=self.id)
        except model.DoesNotExist:
            return None

class GISEntityType(Lookup): pass

class GISBoreholeSpring(Gpoint):
    pass

class GISBorehole(GISBoreholeSpring, GISEntity):
    code = models.IntegerField(blank=True)
    group = models.CharField(max_length=80, blank=True)
    objects = models.GeoManager()
    def __unicode__(self):
        return self.name or 'id=%d'%(self.id,)
    def save(self, *args, **kwargs):
        self.gtype = GISEntityType.objects.get(pk=1)
        super(GISBorehole, self).save(*args, **kwargs)

class GISPump(Gpoint, GISEntity):
    entity_type = models.IntegerField(blank=True)
    objects = models.GeoManager()
    def __unicode__(self):
        return self.name or 'id=%d'%(self.id,)
    def save(self, *args, **kwargs):
        self.gtype = GISEntityType.objects.get(pk=2)
        super(GISPump, self).save(*args, **kwargs)

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

class GISSpring(GISBoreholeSpring, GISEntity):
    objects = models.GeoManager()
    def __unicode__(self):
        return self.name or 'id=%d'%(self.id,)
    def save(self, *args, **kwargs):
        self.gtype = GISEntityType.objects.get(pk=4)
        super(GISSpring, self).save(*args, **kwargs)

class GISAqueductNode(Gpoint, GISEntity):
    entity_type = models.IntegerField(blank=True)
    type_name = models.CharField(max_length=80, blank=True)
    objects = models.GeoManager()
    def __unicode__(self):
        return self.name or 'id=%d'%(self.id,)
    def save(self, *args, **kwargs):
        self.gtype = GISEntityType.objects.get(pk=5)
        super(GISAqueductNode, self).save(*args, **kwargs)

class GISAqueductLine(Gline, GISEntity):
    entity_type = models.IntegerField(blank=True)
    q = models.FloatField(blank=True)
    exs = models.IntegerField(blank=True)
    remarks = models.TextField(blank=True)
    type_name = models.CharField(max_length=80, blank=True)
    objects = models.GeoManager()
    def __unicode__(self):
        return self.name or 'id=%d'%(self.id,)
    def save(self, *args, **kwargs):
        self.gtype = GISEntityType.objects.get(pk=6)
        super(GISAqueductLine, self).save(*args, **kwargs)

class GISReservoir(Garea, GISEntity):
    entity_type = models.IntegerField(blank=True)
    def __unicode__(self):
        return self.name or 'id=%d'%(self.id,)
    def save(self, *args, **kwargs):
        self.gtype = GISEntityType.objects.get(pk=7)
        super(GISReservoir, self).save(*args, **kwargs)

