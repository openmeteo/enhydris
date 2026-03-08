from typing import TYPE_CHECKING

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from enhydris import models

from .garea import GareaAdmin  # NOQA  # type: ignore
from .station import StationAdmin  # NOQA  # type: ignore

admin.site.site_header = _("Enhydris dashboard")

if TYPE_CHECKING:
    LentityAdminBase = admin.ModelAdmin[models.Lentity]
    EventTypeAdminBase = admin.ModelAdmin[models.EventType]
    VariableTranslationInlineBase = admin.TabularInline[
        models.VariableTranslation, models.Variable
    ]
    VariableAdminBase = admin.ModelAdmin[models.Variable]
    UnitOfMeasurementAdminBase = admin.ModelAdmin[models.UnitOfMeasurement]
else:
    LentityAdminBase = admin.ModelAdmin
    EventTypeAdminBase = admin.ModelAdmin
    VariableTranslationInlineBase = admin.TabularInline
    VariableAdminBase = admin.ModelAdmin
    UnitOfMeasurementAdminBase = admin.ModelAdmin


@admin.register(models.Lentity)
class LentityAdmin(LentityAdminBase):
    pass


@admin.register(models.Organization)
class OrganizationAdmin(LentityAdmin):
    list_display = [f.name for f in models.Organization._meta.fields]


@admin.register(models.Person)
class PersonAdmin(LentityAdmin):
    list_display = [f.name for f in models.Person._meta.fields]


@admin.register(models.EventType)
class EventTypeAdmin(EventTypeAdminBase):
    list_display = ("id", "descr")


class VariableTranslationInline(VariableTranslationInlineBase):
    model = models.VariableTranslation
    extra = 1


@admin.register(models.Variable)
class VariableAdmin(VariableAdminBase):
    list_display = ("id", "descr", "last_modified")
    inlines = (VariableTranslationInline,)


@admin.register(models.UnitOfMeasurement)
class UnitOfMeasurementAdmin(UnitOfMeasurementAdminBase):
    list_display = [f.name for f in models.UnitOfMeasurement._meta.fields]
