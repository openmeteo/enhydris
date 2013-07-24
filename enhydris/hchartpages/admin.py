from enhydris.hchartpages.models import *
from django.contrib import admin

class VariableInline(admin.TabularInline):
    model = Variable
    extra = 1

class ChartInline(admin.TabularInline):
    model = Chart
    extra = 1

class ChartPageAdmin(admin.ModelAdmin):
    inlines = [ChartInline,]
    list_display = ('id', 'name', 'url_name', 'url_int_alias',)

class ChartAdmin(admin.ModelAdmin):
    fieldsets = ( (None, {'fields':
                  ('name', 'order', 'chart_page',
                  'can_zoom', ('display_min', 'display_max'), 
                  ('display_avg', 'display_sum'),
                  'display_lastvalue', 'is_vector',)}), )

    inlines = [VariableInline,]
    list_display = ('id', 'name', 'chart_page', 'order')
    ordering = ('chart_page', 'order')
    list_filter = ('chart_page', )

admin.site.register(Chart, ChartAdmin)
admin.site.register(ChartPage, ChartPageAdmin)
