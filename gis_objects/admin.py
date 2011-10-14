from gis_objects.models import *
from django.contrib import admin

admin.site.register(GISGentityType, admin.ModelAdmin)
admin.site.register(GISBorehole, admin.ModelAdmin)
admin.site.register(GISPump, admin.ModelAdmin)
admin.site.register(GISSpring, admin.ModelAdmin)
admin.site.register(GISRefinery, admin.ModelAdmin)
admin.site.register(GISAqueductNode, admin.ModelAdmin)
admin.site.register(GISAqueductLine, admin.ModelAdmin)
admin.site.register(GISReservoir, admin.ModelAdmin)
