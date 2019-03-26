from django import forms
from django.conf import settings
from django.contrib import admin
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from rules.contrib.admin import ObjectPermissionsModelAdmin

from enhydris.models import Station


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
        model = Station
        exclude = ()


@admin.register(Station)
class StationAdmin(ObjectPermissionsModelAdmin):
    form = StationAdminForm
    formfield_overrides = {
        models.TextField: {"widget": forms.Textarea(attrs={"rows": 4, "cols": 40})}
    }

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
                    )
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
                    )
                },
            ),
            (_("Other details"), {"fields": ("remarks", ("start_date", "end_date"))}),
        ]
        permissions_fields = []
        if request.user.has_perm("enhydris.change_station_creator", obj):
            permissions_fields.append("creator")
        if request.user.has_perm("enhydris.change_station_maintainers", obj):
            permissions_fields.append("maintainers")
        if permissions_fields:
            fieldsets.append((_("Permissions"), {"fields": permissions_fields}))
        return fieldsets
