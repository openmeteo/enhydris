from django.conf import settings
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from parler.admin import TranslatableAdmin

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


@admin.register(models.Variable)
class VariableAdmin(TranslatableAdmin):
    list_display = ("id", "descr", "last_modified")

    def get_queryset(self, request):
        return models.Variable.objects.translated(settings.LANGUAGE_CODE).order_by(
            "translations__descr"
        )


@admin.register(models.UnitOfMeasurement)
class UnitOfMeasurementAdmin(admin.ModelAdmin):
    list_display = [f.name for f in models.UnitOfMeasurement._meta.fields]


@admin.register(models.TimeZone)
class TimeZoneAdmin(admin.ModelAdmin):
    list_display = [f.name for f in models.TimeZone._meta.fields]
