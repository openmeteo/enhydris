from django.contrib import admin
from django.forms import ModelForm, ValidationError
from django.utils.translation import ugettext_lazy as _

from enhydris import forms, models

##########################################


class LentityAdmin(admin.ModelAdmin):
    pass


class OrganizationAdmin(LentityAdmin):
    list_display = [f.name for f in models.Organization._meta.fields]
    list_display_links = [f.name for f in models.Organization._meta.fields]


class PersonAdmin(LentityAdmin):
    list_display = [f.name for f in models.Person._meta.fields]
    list_display_links = [f.name for f in models.Person._meta.fields]


class GentityAdmin(admin.ModelAdmin):
    pass


class GareaAdmin(GentityAdmin):
    pass


class PoliticalDivisionAdmin(GareaAdmin):
    list_display = [f.name for f in models.PoliticalDivision._meta.fields]
    list_display_links = [f.name for f in models.PoliticalDivision._meta.fields]


class WaterDivisionAdmin(GareaAdmin):
    # TODO: Fill it when the model is ready
    pass


class WaterBasinAdmin(GareaAdmin):
    list_display = [f.name for f in models.WaterBasin._meta.fields]
    list_display_links = [f.name for f in models.WaterBasin._meta.fields]


class GentityFileAdmin(admin.ModelAdmin):
    list_display = [f.name for f in models.GentityFile._meta.fields]


class GentityAltCodeTypeAdmin(admin.ModelAdmin):
    list_display = [f.name for f in models.GentityAltCodeType._meta.fields]


class FileTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "mime_type", "descr")


class EventTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "descr")


class StationTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "descr")


class InstrumentTypeAdmin(admin.ModelAdmin):
    list_display = [f.name for f in models.InstrumentType._meta.fields]


class VariableAdmin(admin.ModelAdmin):
    list_display = [f.name for f in models.Variable._meta.fields]


class IntervalTypeAdmin(admin.ModelAdmin):
    list_display = [f.name for f in models.IntervalType._meta.fields]


class UnitOfMeasurementAdmin(admin.ModelAdmin):
    list_display = [f.name for f in models.UnitOfMeasurement._meta.fields]


class TimeStepAdmin(admin.ModelAdmin):
    form = forms.TimeStepForm
    list_display = [f.name for f in models.TimeStep._meta.fields]


class TimeZoneAdmin(admin.ModelAdmin):
    list_display = [f.name for f in models.TimeZone._meta.fields]


class UserProfileAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.Lentity, LentityAdmin)
admin.site.register(models.Organization, OrganizationAdmin)
admin.site.register(models.Person, PersonAdmin)

admin.site.register(models.Gentity, GentityAdmin)
admin.site.register(models.Garea, GareaAdmin)
admin.site.register(models.PoliticalDivision, PoliticalDivisionAdmin)
admin.site.register(models.WaterDivision, WaterDivisionAdmin)
admin.site.register(models.WaterBasin, WaterBasinAdmin)

admin.site.register(models.GentityAltCodeType, GentityAltCodeTypeAdmin)
admin.site.register(models.GentityFile, GentityFileAdmin)
admin.site.register(models.FileType, FileTypeAdmin)
admin.site.register(models.EventType, EventTypeAdmin)
admin.site.register(models.StationType, StationTypeAdmin)
admin.site.register(models.InstrumentType, InstrumentTypeAdmin)
admin.site.register(models.Variable, VariableAdmin)
admin.site.register(models.UnitOfMeasurement, UnitOfMeasurementAdmin)
admin.site.register(models.TimeStep, TimeStepAdmin)
admin.site.register(models.TimeZone, TimeZoneAdmin)
admin.site.register(models.IntervalType, IntervalTypeAdmin)
admin.site.register(models.UserProfile, UserProfileAdmin)

##########################################


class GentityAltCodeInline(admin.TabularInline):
    model = models.GentityAltCode
    extra = 1


class GentityFileInline(admin.TabularInline):
    model = models.GentityFile
    extra = 1


class GentityEventInline(admin.TabularInline):
    model = models.GentityEvent
    extra = 1


# M2M through Overseer
class OverseerInline(admin.TabularInline):
    model = models.Overseer
    extra = 1


class InstrumentInline(admin.TabularInline):
    model = models.Instrument
    extra = 1


class TimeseriesInline(admin.TabularInline):
    model = models.Timeseries
    extra = 1


class StationAdminForm(ModelForm):
    class Meta:
        model = models.Station
        exclude = []

    def clean_altitude(self):
        value = self.cleaned_data["altitude"]
        if value is not None and (value > 8850 or value < -422):
            raise ValidationError(_("%f is not a valid altitude") % (value,))
        return self.cleaned_data["altitude"]


class StationAdmin(admin.ModelAdmin):
    form = StationAdminForm
    # ChangeList format
    list_display = (
        "id",
        "name",
        "short_name",
        "remarks",
        "water_basin",
        "water_division",
        "political_division",
        "srid",
        "approximate",
        "altitude",
        "asrid",
        "owner",
        "is_automatic",
        "start_date",
        "end_date",
        "show_overseers",
    )
    list_filter = ("is_automatic", "end_date")
    date_hierarchy = "start_date"

    # Inlines for m2m relationships
    inlines = (
        GentityAltCodeInline,
        GentityFileInline,
        GentityEventInline,
        OverseerInline,
        InstrumentInline,
        TimeseriesInline,
    )


admin.site.register(models.Station, StationAdmin)


class InstrumentAdmin(admin.ModelAdmin):
    # ChangeList format
    list_display = (
        "id",
        "name",
        "remarks",
        "station",
        "type",
        "manufacturer",
        "model",
        "start_date",
        "end_date",
    )
    list_filter = ("start_date", "end_date")


admin.site.register(models.Instrument, InstrumentAdmin)


class TimeseriesAdmin(admin.ModelAdmin):
    form = forms.TimeseriesDataForm
    # ChangeList format
    list_display = (
        "id",
        "name",
        "remarks",
        "gentity",
        "variable",
        "unit_of_measurement",
        "precision",
        "time_zone",
        "instrument",
        "time_step",
        "timestamp_rounding_minutes",
        "timestamp_rounding_months",
        "interval_type",
        "timestamp_offset_minutes",
        "timestamp_offset_months",
    )
    list_filter = (
        "unit_of_measurement",
        "precision",
        "time_zone",
        "timestamp_rounding_minutes",
        "timestamp_rounding_months",
        "timestamp_offset_minutes",
        "timestamp_offset_months",
    )


admin.site.register(models.Timeseries, TimeseriesAdmin)
