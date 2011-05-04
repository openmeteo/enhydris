from enhydris.contourplot.models import *
from django.contrib import admin

class CPointInline(admin.TabularInline):
    model = CPoint
    extra = 1

class ChartPageAdmin(admin.ModelAdmin):
    inlines = [CPointInline,]
    fieldsets = ( (None, {'fields': (('name', 'url_name', 'description'),
                    ('chart_bounds_bl_x', 'chart_bounds_bl_y',
                     'chart_bounds_tr_x', 'chart_bounds_tr_y',
                     'chart_bounds_srid'),
                    ('show_mean_value'),
                    ('time_step', 'ts_offset_minutes', 
                     'ts_offset_months'))}),)

    list_display = ('id', 'name', 'url_name')

class CPointAdmin(admin.ModelAdmin):
    fieldsets = ( (None, {'fields': (('display_name', 'chart_page',
                   'point', 'timeseries', 'weight'),
                   ('display_point_on_map', 'display_point_label'))
                   }),)

    list_display = ('id', 'display_name', 'chart_page')

admin.site.register(CPoint, CPointAdmin)
admin.site.register(ChartPage, ChartPageAdmin)
