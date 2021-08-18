import os
from configparser import ParsingError
from io import TextIOWrapper

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.sites.models import Site
from django.db.models import Q, TextField
from django.utils.translation import ugettext_lazy as _

import nested_admin
import pandas as pd
from crequest.middleware import CrequestMiddleware
from geowidgets import LatLonField
from htimeseries import HTimeseries
from rules.contrib.admin import ObjectPermissionsModelAdmin

from enhydris import models, tasks
from enhydris.models import check_time_step


class StationAdminForm(forms.ModelForm):
    code = forms.CharField(
        required=False,
        label=_("Code"),
        help_text=_(
            "If the station has a code (e.g. one given by another agency), you "
            "can enter it here."
        ),
    )
    geom = LatLonField(
        label=_("Co-ordinates"),
        help_text=_("Longitude and latitude in decimal degrees"),
    )
    original_srid = forms.IntegerField(
        label=_("Original SRID"),
        required=False,
        help_text=_(
            "Set this to 4326 if you have no idea what we're talking about. "
            "If the latitude and longitude has been converted from another co-ordinate "
            "system, enter the SRID of the original co-ordinate system."
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

    def has_add_permission(self, request, obj):
        if settings.ENHYDRIS_USERS_CAN_ADD_CONTENT:
            return True
        else:
            return super().has_add_permission(request, obj)

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


class ImageInline(InlinePermissionsMixin, nested_admin.NestedStackedInline):
    model = models.GentityImage
    classes = ("collapse",)
    fields = (("descr", "date"), ("content"), "remarks", "featured")
    extra = 0


class GentityFileInline(InlinePermissionsMixin, nested_admin.NestedStackedInline):
    model = models.GentityFile
    classes = ("collapse",)
    fields = (("descr", "date"), ("content"), "remarks")


class GentityEventInline(InlinePermissionsMixin, nested_admin.NestedStackedInline):
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
        if self.cleaned_data.get("data") is not None:
            self._check_submitted_data(self.cleaned_data["data"])
        return result

    def clean_time_step(self):
        try:
            result = self.cleaned_data.get("time_step", "")
            check_time_step(result)
            return result
        except ValueError as e:
            raise forms.ValidationError(str(e))

    def _check_submitted_data(self, datastream):
        try:
            ahtimeseries = self._get_timeseries_without_moving_file_position(datastream)
        except (ParsingError, EOFError, pd.errors.ParserError, ValueError) as e:
            raise forms.ValidationError(str(e))
        if self._we_are_appending_data(ahtimeseries):
            self._check_timeseries_for_appending(ahtimeseries)

    def _get_timeseries_without_moving_file_position(self, datastream):
        original_position = datastream.tell()
        wrapped_datastream = TextIOWrapper(datastream, encoding="utf-8", newline="\n")
        result = self._read_timeseries_from_stream(wrapped_datastream)
        wrapped_datastream.detach()  # If we don't do this the datastream will be closed
        datastream.seek(original_position)
        return result

    def _read_timeseries_from_stream(self, stream):
        try:
            return HTimeseries(stream)
        except UnicodeDecodeError as e:
            raise forms.ValidationError(
                _("The file does not seem to be a valid UTF-8 file: " + str(e))
            )

    def _we_are_appending_data(self, ahtimeseries):
        data_exists = bool(self.instance and self.instance.start_date)
        submitted_data_exists = len(ahtimeseries.data) > 0
        user_wants_to_append = self.cleaned_data.get("replace_or_append") == "APPEND"
        return data_exists and submitted_data_exists and user_wants_to_append

    def _check_timeseries_for_appending(self, ahtimeseries):
        if self.instance.end_date.replace(tzinfo=None) >= ahtimeseries.data.index.min():
            raise forms.ValidationError(
                _(
                    "Can't append; the first record of the time series to append is "
                    "earlier than the last record of the existing time series."
                )
            )

    def save(self, *args, **kwargs):
        result = super().save(*args, **kwargs)
        if self.cleaned_data.get("data") is not None:
            self._save_timeseries_data()
        return result

    def _save_timeseries_data(self):
        request = CrequestMiddleware.get_request()

        # Create a hard link to the temporary uploaded file with the data
        # so that it's not automatically deleted and can be used by the celery
        # worker
        tmpfilename = self.cleaned_data["data"].temporary_file_path()
        datafilename = tmpfilename + ".1"
        os.link(tmpfilename, datafilename)

        tasks.save_timeseries_data.delay(
            id=self.instance.id,
            replace_or_append=self.cleaned_data["replace_or_append"],
            datafilename=datafilename,
            username=request.user.username,
        )
        messages.add_message(
            request,
            messages.INFO,
            _(
                'The data for the time series "{} - {} - {}" will be imported '
                "soon. You will be notified by email when the importing finishes."
            ).format(
                self.instance.timeseries_group.gentity.name,
                str(self.instance.timeseries_group),
                str(self.instance),
            ),
        )


class TimeseriesInlineFormSet(nested_admin.formsets.NestedInlineFormSet):
    def clean(self):
        super().clean()
        self._check_only_one_timeseries_with_type(models.Timeseries.INITIAL)
        self._check_only_one_timeseries_with_type(models.Timeseries.CHECKED)
        self._check_only_one_timeseries_with_type(models.Timeseries.REGULARIZED)

    def _check_only_one_timeseries_with_type(self, type):
        """Check for duplicate time series.

        Ensures that there is only one time series with the given type.
        """
        occurrences = [
            form for form in self.forms if type == form.cleaned_data.get("type")
        ]
        if len(occurrences) > 1:
            raise forms.ValidationError(
                _(
                    "There can be only one {} time series in each time series group."
                ).format(dict(models.Timeseries.TIMESERIES_TYPES)[type].lower())
            )


class TimeseriesInline(InlinePermissionsMixin, nested_admin.NestedStackedInline):
    form = TimeseriesInlineAdminForm
    formset = TimeseriesInlineFormSet
    model = models.Timeseries
    classes = ("collapse",)
    extra = 1
    fields = (
        ("type", "time_step"),
        ("data", "replace_or_append"),
    )


class TimeseriesGroupInline(InlinePermissionsMixin, nested_admin.NestedStackedInline):
    model = models.TimeseriesGroup
    classes = ("collapse",)
    inlines = [TimeseriesInline]
    extra = 1
    fieldsets = [
        (
            _("Metadata"),
            {
                "fields": (
                    "name",
                    ("variable", "unit_of_measurement"),
                    "precision",
                    "time_zone",
                    "hidden",
                    "remarks",
                ),
                "classes": ("collapse",),
            },
        )
    ]

    class Media:
        css = {"all": ("css/extra_admin.css",)}


class SiteFilter(admin.SimpleListFilter):
    title = _("Site")

    parameter_name = "site"

    def lookups(self, request, model_admin):
        if not request.user.is_superuser:
            return ()
        else:
            return ((s.id, s.domain) for s in Site.objects.all())

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(sites__id=self.value())


@admin.register(models.Station)
class StationAdmin(ObjectPermissionsModelAdmin, nested_admin.NestedModelAdmin):
    form = StationAdminForm
    formfield_overrides = {
        TextField: {"widget": forms.Textarea(attrs={"rows": 4, "cols": 40})}
    }
    inlines = [
        ImageInline,
        GentityFileInline,
        GentityEventInline,
        TimeseriesGroupInline,
    ]
    search_fields = ("id", "name", "code", "owner__ordering_string")
    list_display = ("name", "owner")
    list_filter = (SiteFilter,)

    def get_queryset(self, request):
        if request.user.is_superuser:
            result = super().get_queryset(request)
        else:
            result = models.Station.on_site
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
        self._fieldsets = [
            (
                _("General information"),
                {
                    "fields": [
                        ("name", "code"),
                        "owner",
                        ("geom", "original_srid"),
                        "altitude",
                        "remarks",
                        ("start_date", "end_date"),
                    ],
                },
            ),
        ]
        self._get_permissions_fields(request, obj)
        self._get_sites_fields(request, obj)
        return self._fieldsets

    def _get_permissions_fields(self, request, obj):
        permissions_fields = []
        if request.user.has_perm("enhydris.change_station_creator", obj):
            permissions_fields.append("creator")
        if request.user.has_perm("enhydris.change_station_maintainers", obj):
            permissions_fields.append("maintainers")
        if permissions_fields:
            self._fieldsets.append(
                (
                    _("Permissions"),
                    {"fields": permissions_fields, "classes": ("collapse",)},
                )
            )

    def _get_sites_fields(self, request, obj):
        if obj is not None and request.user.is_superuser and Site.objects.count() > 1:
            self._fieldsets[0][1]["fields"].append("sites")

    def save_model(self, request, obj, form, change):
        if obj.creator is None:
            obj.creator = request.user
        super().save_model(request, obj, form, change)
