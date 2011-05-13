from enhydris.hprocessor.models import *
from django.contrib import admin


class VariableInline(admin.TabularInline):
    model = ProcessInputVariable
    extra = 1


class ProcessUnitInline(admin.TabularInline):
    model = ProcessUnit
    extra = 1


class ProcessBatchAdmin(admin.ModelAdmin):
    inlines = [ProcessUnitInline,]
    list_display = ('id', 'name', 'unique_name')


class ProcessUnitAdmin(admin.ModelAdmin):
    fieldsets = ( (None, {'fields':
                  ('name', 'order', 'batch',
                  'method', 'output_timeseries',
                  'append_only',
                  ('aggregation_missing_allowed',
                  'aggregation_missing_flag'))} ),)

    inlines = [VariableInline,]
    list_display = ('id', 'batch', 'order', 'method', 'name')
    ordering = ('batch', 'order')
    list_filter = ('batch', 'method')


admin.site.register(ProcessUnit, ProcessUnitAdmin)
admin.site.register(ProcessBatch, ProcessBatchAdmin)
