# -*- coding: utf-8 -*-
# UTF8 Encoded
from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from enhydris.hcore.models import *
from enhydris.hcore.forms import *

##########################################

class LentityAdmin(admin.ModelAdmin):
    pass

class OrganizationAdmin(LentityAdmin):
    list_display = [f.name for f in Organization._meta.fields]
    list_display_links = [f.name for f in Organization._meta.fields]

class PersonAdmin(LentityAdmin):
    list_display = [f.name for f in Person._meta.fields]
    list_display_links = [f.name for f in Person._meta.fields]

class GentityAdmin(admin.ModelAdmin):
    pass

class GareaAdmin(GentityAdmin):
    pass

class PoliticalDivisionAdmin(GareaAdmin):
    list_display = [f.name for f in PoliticalDivision._meta.fields]
    list_display_links = [f.name for f in PoliticalDivision._meta.fields]

class WaterDivisionAdmin(GareaAdmin):
    # TODO: Fill it when the model is ready
    pass

class WaterBasinAdmin(GareaAdmin):
    list_display = [f.name for f in WaterBasin._meta.fields]
    list_display_links = [f.name for f in WaterBasin._meta.fields]

class GentityFileAdmin(admin.ModelAdmin):
    list_display = [f.name for f in GentityFile._meta.fields]

class GentityGenericDataAdmin(admin.ModelAdmin):
    list_display = [f.name for f in GentityGenericData._meta.fields]

class GentityAltCodeTypeAdmin(admin.ModelAdmin):
    list_display = [f.name for f in GentityAltCodeType._meta.fields]

class FileTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'mime_type', 'descr',)

class GentityGenericDataTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'descr', 'file_extension', )

class EventTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'descr',)

class StationTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'descr',)

class InstrumentTypeAdmin(admin.ModelAdmin):
    list_display = [f.name for f in InstrumentType._meta.fields]

class VariableAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Variable._meta.fields]

class IntervalTypeAdmin(admin.ModelAdmin):
    list_display = [f.name for f in IntervalType._meta.fields]

class UnitOfMeasurementAdmin(admin.ModelAdmin):
    list_display = [f.name for f in UnitOfMeasurement._meta.fields]

class TimeStepAdmin(admin.ModelAdmin):
    form = TimeStepForm
    list_display = [f.name for f in TimeStep._meta.fields]

class TimeZoneAdmin(admin.ModelAdmin):
    list_display = [f.name for f in TimeZone._meta.fields]

class UserProfileAdmin(admin.ModelAdmin):
    pass

admin.site.register(Lentity, LentityAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Person, PersonAdmin)

admin.site.register(Gentity, GentityAdmin)
admin.site.register(Garea, GareaAdmin)
admin.site.register(PoliticalDivision, PoliticalDivisionAdmin)
admin.site.register(WaterDivision, WaterDivisionAdmin)
admin.site.register(WaterBasin, WaterBasinAdmin)

admin.site.register(GentityAltCodeType, GentityAltCodeTypeAdmin)
admin.site.register(GentityFile, GentityFileAdmin)
admin.site.register(GentityGenericData, GentityGenericDataAdmin)
admin.site.register(FileType, FileTypeAdmin)
admin.site.register(GentityGenericDataType, GentityGenericDataTypeAdmin)
admin.site.register(EventType, EventTypeAdmin)
admin.site.register(StationType, StationTypeAdmin)
admin.site.register(InstrumentType, InstrumentTypeAdmin)
admin.site.register(Variable, VariableAdmin)
admin.site.register(UnitOfMeasurement, UnitOfMeasurementAdmin)
admin.site.register(TimeStep, TimeStepAdmin)
admin.site.register(TimeZone, TimeZoneAdmin)
admin.site.register(IntervalType, IntervalTypeAdmin)
admin.site.register(UserProfile, UserProfileAdmin)

##########################################

class GentityAltCodeInline(admin.TabularInline):
    model = GentityAltCode
    extra = 1

class GentityFileInline(admin.TabularInline):
    model = GentityFile
    extra = 1

class GentityGenericDataInline(admin.TabularInline):
    model = GentityGenericData
    extra = 1
 
class GentityEventInline(admin.TabularInline):
    model = GentityEvent
    extra = 1

# M2M through Overseer
class OverseerInline(admin.TabularInline):
    model = Overseer
    extra = 1

class InstrumentInline(admin.TabularInline):
    model = Instrument
    extra = 1

class TimeseriesInline(admin.TabularInline):
    model = Timeseries
    extra = 1


class StationAdminForm(forms.ModelForm):

    class Meta:
        model = Station
        exclude = []
    def clean_altitude(self):
        value = self.cleaned_data['altitude']
        if not value == None and (value > 8850 or value < -422):
            raise forms.ValidationError(_("%f is not a valid altitude") %
            (value,))
        return self.cleaned_data['altitude']


class StationAdmin(admin.ModelAdmin):
    form = StationAdminForm
    # ChangeList format
    list_display = ('id', 'name', 'short_name', 'remarks', 'water_basin',
        'water_division', 'political_division', 'srid',
        'approximate', 'altitude', 'asrid', 'owner', 'is_automatic',
        'start_date', 'end_date','show_overseers')
    list_filter = ('is_automatic', 'end_date',)
    date_hierarchy = 'start_date'

    # Inlines for m2m relationships
    inlines = (GentityAltCodeInline, GentityFileInline, 
                GentityGenericDataInline, GentityEventInline,
                OverseerInline, InstrumentInline, TimeseriesInline,)

admin.site.register(Station, StationAdmin)

class InstrumentAdmin(admin.ModelAdmin):
    # ChangeList format
    list_display = ('id', 'name', 'remarks', 'station', 'type', 'manufacturer',
        'model', 'start_date', 'end_date' )
    list_filter = ('start_date', 'end_date',)

admin.site.register(Instrument, InstrumentAdmin)

class TimeseriesAdmin(admin.ModelAdmin):
    form = TimeseriesDataForm
    # ChangeList format
    list_display = ('id', 'name', 'remarks', 'gentity', 'variable', 
        'unit_of_measurement', 'precision', 'time_zone', 'instrument',
        'time_step', 'timestamp_rounding_minutes', 'timestamp_rounding_months', 
        'interval_type', 'timestamp_offset_minutes', 'timestamp_offset_months')
    list_filter = ('unit_of_measurement','precision', 'time_zone', 
                    'timestamp_rounding_minutes', 'timestamp_rounding_months',
                    'timestamp_offset_minutes', 'timestamp_offset_months')


admin.site.register(Timeseries, TimeseriesAdmin)
