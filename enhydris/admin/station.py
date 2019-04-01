from django import forms
from django.conf import settings
from django.contrib import admin
from django.db.models import Q, TextField
from django.utils.translation import ugettext_lazy as _

from rules.contrib.admin import ObjectPermissionsModelAdmin

from enhydris import models


class LatLonWidget(forms.MultiWidget):
    """A simple widget showing latitude and longitude."""

    def __init__(self, *args, **kwargs):
        widgets = forms.TextInput(), forms.TextInput()
        super().__init__(widgets, *args, **kwargs)

    def decompress(self, value):
        if value:
            return [round(x, 6) for x in value.coords]
        return (None, None)


class LatLonField(forms.MultiValueField):
    widget = LatLonWidget
    require_all_fields = True

    def __init__(self, *args, **kwargs):
        fields = (
            forms.FloatField(min_value=-180, max_value=180),
            forms.FloatField(min_value=-90, max_value=90),
        )
        super().__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        return "SRID=4326;POINT({} {})".format(*data_list)


class StationAdminForm(forms.ModelForm):
    point = LatLonField(
        label=_("Co-ordinates"),
        help_text=_("Longitude and latitude in decimal degrees"),
    )
    srid = forms.IntegerField(
        label=_("Original SRID"),
        required=False,
        help_text=_(
            "Set this to 4326 if you have no idea what we're talking about. "
            "If the latitude and longitude has been converted from another co-ordinate "
            "system, enter the SRID of the original co-ordinate system."
        ),
    )
    asrid = forms.IntegerField(
        label=_("Altitude SRID"),
        required=False,
        help_text=_(
            "Leave this empty if unsure. Set it to the SRID of the reference system "
            "used for the altitude. Empty means mean sea level."
        ),
    )

    class Meta:
        model = models.Station
        exclude = ()


class InlinePermissionsMixin:
    """Permissions relaxing mixin.
    The admin is using some complicated permissions stuff to determine which inlines
    will show on the form, whether they'll have the "delete" checkbox, and so on.
    Among other things it's doing strange things such as checking whether a nonexistent
    object has delete permission. This is causing trouble for our django-rules system.

    What we do is specify that (for ENHYDRIS_USERS_CAN_ADD_CONTENT=True), users
    always have permission to add, change, delete and view inlines. This will
    (hopefully) take effect only when the user has permission to edit the parent object
    (i.e. the station).

    The truth is that this hasn't been exhaustively tested (but it should).
    """

    def has_add_permission(self, request):
        if settings.ENHYDRIS_USERS_CAN_ADD_CONTENT:
            return True
        else:
            return super().has_add_permission(request)

    def has_change_permission(self, request, obj):
        if settings.ENHYDRIS_USERS_CAN_ADD_CONTENT:
            return True
        else:
            return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj):
        if settings.ENHYDRIS_USERS_CAN_ADD_CONTENT:
            return True
        else:
            return super().has_delete_permission(request, obj)

    def has_view_permission(self, request, obj):
        if settings.ENHYDRIS_USERS_CAN_ADD_CONTENT:
            return True
        else:
            return super().has_view_permission(request, obj)


class GentityAltCodeInline(InlinePermissionsMixin, admin.TabularInline):
    model = models.GentityAltCode
    classes = ("collapse",)


class InstrumentInline(InlinePermissionsMixin, admin.StackedInline):
    model = models.Instrument
    classes = ("collapse",)
    fields = (
        "name",
        "type",
        ("manufacturer", "model"),
        ("start_date", "end_date"),
        "remarks",
    )


class GentityFileInline(InlinePermissionsMixin, admin.StackedInline):
    model = models.GentityFile
    classes = ("collapse",)
    fields = (("descr", "date"), ("content", "file_type"), "remarks")


class GentityEventInline(InlinePermissionsMixin, admin.StackedInline):
    model = models.GentityEvent
    classes = ("collapse",)
    fields = (("user", "date"), "type", "report")


@admin.register(models.Station)
class StationAdmin(ObjectPermissionsModelAdmin):
    form = StationAdminForm
    formfield_overrides = {
        TextField: {"widget": forms.Textarea(attrs={"rows": 4, "cols": 40})}
    }
    inlines = [
        GentityAltCodeInline,
        InstrumentInline,
        GentityFileInline,
        GentityEventInline,
    ]

    def get_queryset(self, request):
        result = super().get_queryset(request)
        if request.user.has_perm("enhydris.change_station"):
            return result
        elif settings.ENHYDRIS_USERS_CAN_ADD_CONTENT:
            return result.filter(
                Q(id__in=request.user.maintaining_stations.all())
                | Q(id__in=request.user.created_stations.all())
            )
        else:
            return result.none()

    def get_fieldsets(self, request, obj):
        fieldsets = [
            (
                _("Essential information"),
                {
                    "fields": (
                        ("name", "short_name"),
                        "stype",
                        "owner",
                        ("copyright_years", "copyright_holder"),
                    ),
                    "classes": ("collapse",),
                },
            ),
            (
                _("Location"),
                {
                    "fields": (
                        "political_division",
                        "water_division",
                        "water_basin",
                        ("point", "srid", "approximate"),
                        ("altitude", "asrid"),
                    ),
                    "classes": ("collapse",),
                },
            ),
            (
                _("Other details"),
                {
                    "fields": ("remarks", ("start_date", "end_date")),
                    "classes": ("collapse",),
                },
            ),
        ]
        permissions_fields = []
        if request.user.has_perm("enhydris.change_station_creator", obj):
            permissions_fields.append("creator")
        if request.user.has_perm("enhydris.change_station_maintainers", obj):
            permissions_fields.append("maintainers")
        if permissions_fields:
            fieldsets.append(
                (
                    _("Permissions"),
                    {"fields": permissions_fields, "classes": ("collapse",)},
                )
            )
        return fieldsets
