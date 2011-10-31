from enhydris.hprocessor.models import *
from django.contrib import admin


class VariableInline(admin.TabularInline):
    model = ProcessInputVariable
    extra = 1


class ProcessUnitInline(admin.TabularInline):
    model = ProcessUnit
    fields = ('name', 'order', 'method', 'output_timeseries',
              'append_only',)
    extra = 1


class ProcessBatchAdmin(admin.ModelAdmin):
    inlines = [ProcessUnitInline,]
    list_display = ('id', 'name', 'unique_name')


class ProcessUnitAdmin(admin.ModelAdmin):
    fieldsets = ( ('Common values', {'fields':
                  ('name', 'order', 'batch',
                  'method', 'output_timeseries',
                  'append_only',
                  ('aggregation_missing_allowed',
                  'aggregation_missing_flag',
                  'aggregation_last_incomplete',
                  'aggregation_all_incomplete'))} ),
                  ('Curve interpolation', {'fields':
                  ('interpol_method', 'curve',
                   'independent_column',
                   'dependent_column',
                  )} ),
                )

    inlines = [VariableInline,]
    list_display = ('id', 'batch', 'order', 'method', 'name')
    ordering = ('batch', 'order')
    list_filter = ('batch', 'method')


admin.site.register(ProcessUnit, ProcessUnitAdmin)
admin.site.register(ProcessBatch, ProcessBatchAdmin)
