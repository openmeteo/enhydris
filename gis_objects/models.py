from django.contrib.gis.db import models
from enhydris.hcore.models import Gpoint, Gline, Garea

class GISEntity(models.Model):
    gis_id = models.IntegerField(blank=True, null=True)
    original_gentity_id = models.IntegerField(blank=True, null=True)
    gtype = models.ForeignKey('GISEntityType', blank=True, null=True)

class GISEntityType(models.Model):
    descr = models.CharField(max_length=100, blank=False)
    descr_alt = models.CharField(max_length=100, blank=False)
    def __unicode__(self):
        return self.descr

class GISBorehole(Gpoint, GISEntity):
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
    objects = models.GeoManager()
    def __unicode__(self):
        return self.name or 'id=%d'%(self.id,)
    def save(self, *args, **kwargs):
        self.gtype = GISEntityType.objects.get(pk=3)
        super(GISRefinery, self).save(*args, **kwargs)

class GISSpring(Gpoint, GISEntity):
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

