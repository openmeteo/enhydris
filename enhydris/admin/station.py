from io import TextIOWrapper

from django import forms
from django.conf import settings
from django.contrib import admin
from django.db.models import Q, TextField
from django.utils.translation import ugettext_lazy as _

from htimeseries import HTimeseries
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


class TimeseriesInlineAdminForm(forms.ModelForm):
    data = forms.FileField(label=_("Data file"), required=False)
    replace_or_append = forms.ChoiceField(
        label=_("What to do"),
        required=False,
        initial="APPEND",
        choices=(
            ("APPEND", _("Append this file's data to the already existing")),
            (
                "REPLACE",
                _("Discard any already existing data and replace them with this file"),
            ),
        ),
    )

    class Meta:
        model = models.Timeseries
        exclude = ()

    def clean(self):
        result = super().clean()
        self._check_timestep()
        if self.cleaned_data.get("data") is not None:
            self._check_submitted_data(self.cleaned_data["data"])
        return result

    def _check_timestep(self):
        self._check_rounding_and_offset_are_none_when_timestep_is_none()
        self._check_offset_is_not_none_when_timestep_is_not_none()

    def _check_rounding_and_offset_are_none_when_timestep_is_none(self):
        has_error = self.cleaned_data.get("time_step") is None and (
            self.cleaned_data.get("timestamp_rounding_minutes") is not None
            or self.cleaned_data.get("timestamp_rounding_months") is not None
            or self.cleaned_data.get("timestamp_offset_minutes") is not None
            or self.cleaned_data.get("timestamp_offset_months") is not None
        )
        if has_error:
            raise forms.ValidationError(
                _("When the time step is empty, the rounding and offset must be empty.")
            )

    def _check_offset_is_not_none_when_timestep_is_not_none(self):
        has_error = self.cleaned_data.get("time_step") is not None and (
            self.cleaned_data.get("timestamp_offset_minutes") is None
            or self.cleaned_data.get("timestamp_offset_months") is None
        )
        if has_error:
            raise forms.ValidationError(
                _("When a time step is specified, the offset must have a value.")
            )

    def _check_submitted_data(self, datastream):
        ahtimeseries = self._get_timeseries_without_moving_file_position(datastream)
        if self._we_are_appending_data(ahtimeseries):
            self._check_timeseries_for_appending(ahtimeseries)

    def _get_timeseries_without_moving_file_position(self, datastream):
        original_position = datastream.tell()
        wrapped_datastream = TextIOWrapper(datastream, encoding="utf-8", newline="\n")
        result = HTimeseries.read(wrapped_datastream)
        wrapped_datastream.detach()  # If we don't do this the datastream will be closed
        datastream.seek(original_position)
        return result

    def _we_are_appending_data(self, ahtimeseries):
        data_exists = bool(self.instance and self.instance.start_date)
        submitted_data_exists = len(ahtimeseries.data) > 0
        user_wants_to_append = self.cleaned_data.get("replace_or_append") == "APPEND"
        return data_exists and submitted_data_exists and user_wants_to_append

    def _check_timeseries_for_appending(self, ahtimeseries):
        if self.instance.end_date.replace(tzinfo=None) >= ahtimeseries.data.index[0]:
            raise forms.ValidationError(
                _(
                    "Can't append; the first record of the time series to append is "
                    "earlier than the last record of the existing time series."
                )
            )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.cleaned_data.get("data") is not None:
            self._save_timeseries_data()

    def _save_timeseries_data(self):
        data = TextIOWrapper(self.cleaned_data["data"], encoding="utf-8", newline="\n")
        if self.cleaned_data["replace_or_append"] == "APPEND":
            self.instance.append_data(data)
        else:
            self.instance.set_data(data)


class TimeseriesInline(InlinePermissionsMixin, admin.StackedInline):
    form = TimeseriesInlineAdminForm
    model = models.Timeseries
    classes = ("collapse",)
    fieldsets = [
        (
            _("Essential information"),
            {
                "fields": ("name", ("variable", "unit_of_measurement")),
                "classes": ("collapse",),
            },
        ),
        (
            _("Other details"),
            {
                "fields": ("hidden", "instrument", "precision", "remarks"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Time step"),
            {
                "fields": (
                    "interval_type",
                    ("time_step", "time_zone"),
                    ("timestamp_rounding_months", "timestamp_rounding_minutes"),
                    ("timestamp_offset_months", "timestamp_offset_minutes"),
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Data"),
            {"fields": (("data", "replace_or_append"),), "classes": ("collapse",)},
        ),
    ]

    class Media:
        css = {"all": ("css/extra_admin.css",)}


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
        TimeseriesInline,
    ]
    search_fields = (
        "id",
        "name",
        "short_name",
        "stype__descr",
        "water_basin__name",
        "owner__ordering_string",
    )
    list_display = ("name", "water_basin", "owner")

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
