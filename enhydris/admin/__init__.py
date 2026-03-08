from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from enhydris import models

from .garea import GareaAdmin  # NOQA
from .station import StationAdmin  # NOQA

admin.site.site_header = _("Enhydris dashboard")


@admin.register(models.Lentity)
class LentityAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Organization)
class OrganizationAdmin(LentityAdmin):
    list_display = [f.name for f in models.Organization._meta.fields]


@admin.register(models.Person)
class PersonAdmin(LentityAdmin):
    list_display = [f.name for f in models.Person._meta.fields]


@admin.register(models.EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "descr")


class VariableTranslationInline(admin.TabularInline):
    model = models.VariableTranslation
    extra = 1


@admin.register(models.Variable)
class VariableAdmin(admin.ModelAdmin):
    list_display = ("id", "descr", "last_modified")
    inlines = [VariableTranslationInline]


@admin.register(models.UnitOfMeasurement)
class UnitOfMeasurementAdmin(admin.ModelAdmin):
    list_display = [f.name for f in models.UnitOfMeasurement._meta.fields]
