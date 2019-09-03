from django import forms
from django.conf import settings
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from parler.admin import TranslatableAdmin

from enhydris import models

from .station import StationAdmin  # NOQA


@admin.register(models.Lentity)
class LentityAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Organization)
class OrganizationAdmin(LentityAdmin):
    list_display = [f.name for f in models.Organization._meta.fields]


@admin.register(models.Person)
class PersonAdmin(LentityAdmin):
    list_display = [f.name for f in models.Person._meta.fields]


@admin.register(models.Gentity)
class GentityAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Garea)
class GareaAdmin(GentityAdmin):
    pass


@admin.register(models.PoliticalDivision)
class PoliticalDivisionAdmin(GareaAdmin):
    list_display = [f.name for f in models.PoliticalDivision._meta.fields]


@admin.register(models.WaterDivision)
class WaterDivisionAdmin(GareaAdmin):
    list_display = ("id", "last_modified", "name", "short_name")


@admin.register(models.WaterBasin)
class WaterBasinAdmin(GareaAdmin):
    list_display = [f.name for f in models.WaterBasin._meta.fields]


@admin.register(models.FileType)
class FileTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "mime_type", "descr")


@admin.register(models.EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "descr")


@admin.register(models.InstrumentType)
class InstrumentTypeAdmin(admin.ModelAdmin):
    list_display = [f.name for f in models.InstrumentType._meta.fields]


@admin.register(models.Variable)
class VariableAdmin(TranslatableAdmin):
    list_display = ("id", "descr", "last_modified")

    def get_queryset(self, request):
        return models.Variable.objects.translated(settings.LANGUAGE_CODE).order_by(
            "translations__descr"
        )


@admin.register(models.IntervalType)
class IntervalTypeAdmin(admin.ModelAdmin):
    list_display = [f.name for f in models.IntervalType._meta.fields]


@admin.register(models.UnitOfMeasurement)
class UnitOfMeasurementAdmin(admin.ModelAdmin):
    list_display = [f.name for f in models.UnitOfMeasurement._meta.fields]


class TimeStepForm(forms.ModelForm):
    class Meta:
        model = models.TimeStep
        exclude = []

    def clean(self):
        """Ensure that exactly one of minutes and months is non-zero.
        """
        length_minutes = self.cleaned_data.get("length_minutes", None)
        length_months = self.cleaned_data.get("length_months", None)
        if bool(length_minutes) == bool(length_months):
            raise forms.ValidationError(
                _("Invalid timestep: exactly one of minutes and months must be zero")
            )
        return self.cleaned_data


@admin.register(models.TimeStep)
class TimeStepAdmin(TranslatableAdmin):
    form = TimeStepForm
    list_display = [f.name for f in models.TimeStep._meta.fields]


@admin.register(models.TimeZone)
class TimeZoneAdmin(admin.ModelAdmin):
    list_display = [f.name for f in models.TimeZone._meta.fields]
