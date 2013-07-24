from django.contrib.gis import admin
from enhydris.gis_objects.models import *
from enhydris.hcore.admin import (GentityAltCodeInline, 
               GentityFileInline, GentityGenericDataInline, 
               GentityEventInline, TimeseriesInline,)

for model in (GISBoreholeSpringWaterUse, GISBoreholeSpringWaterUser,
              GISBoreholeSpringLandUse, GISBoreholePmeterType,
              GISBoreholeDrillType, GISBoreholePipeMat,
              GISPumpType, GISSpringDstype, GISSpringHgeoInfo,
              GISEntityType, GISAqueductGroup, GISXSectionType,
              GISDuctSegmentType, GISDuctFlowType,
              GISDuctStatusType, GISRoughnessCoefType,
              GISXSection):
    admin.site.register(model, admin.ModelAdmin)

class EntitiesAdmin(admin.GeoModelAdmin):
    list_display = ('id', 'name', 'gis_id', 'original_gentity_id')
    exclude = ('gtype', )
    inlines = (GentityAltCodeInline, GentityFileInline, 
               GentityGenericDataInline, GentityEventInline,
               TimeseriesInline,)

for model in (GISBorehole, GISPump, GISSpring, GISRefinery,
              GISAqueductNode, GISAqueductLine, GISReservoir,):
    admin.site.register(model, EntitiesAdmin)

