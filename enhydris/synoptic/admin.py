from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from enhydris.models import TimeseriesGroup
from enhydris.synoptic.models import (
    EarlyWarningEmail,
    RateOfChangeThreshold,
    SynopticGroup,
    SynopticGroupStation,
    SynopticTimeseriesGroup,
)


class StationInline(admin.TabularInline):
    model = SynopticGroup.stations.through

    def get_formset(self, request, obj=None, **kwargs):
        """
        Override the get_formset method to remove the add/change buttons beside the
        foreign key pull-down menus in the inline.
        """
        formset = super().get_formset(request, obj, **kwargs)
        form = formset.form
        widget = form.base_fields["station"].widget
        widget.can_add_related = False
        widget.can_change_related = False
        return formset


class EmailInline(admin.TabularInline):
    model = EarlyWarningEmail
    extra = 1


@admin.register(SynopticGroup)
class GroupAdmin(admin.ModelAdmin):
    inlines = [StationInline, EmailInline]
    exclude = ["stations"]


class SynopticTimeseriesGroupForm(forms.ModelForm):
    roc_thresholds = forms.CharField(
        required=False,
        widget=forms.Textarea,
        label=_("Thresholds"),
        help_text=_(
            'The allowed differences, one per line, like "10min 7.3" (without the '
            "quotes). This example means that any change higher than 7.3 within 10 "
            "minutes will trigger an early warning. The time length is specified as an "
            "optional number plus a unit, with no space in between. The units "
            "available are min (minutes), H (hours) and D (days)."
        ),
    )

    class Meta:
        model = SynopticTimeseriesGroup
        fields = "__all__"

    # Untested rate-of-change stuff (see comment in models.py)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["roc_thresholds"].initial = (
            self.instance.get_roc_thresholds_as_text()
        )

    def clean_roc_thresholds(self):
        data = self.cleaned_data["roc_thresholds"]
        for line in data.splitlines():
            self._check_thresholds_line(line)
        return data

    def _check_thresholds_line(self, line):
        try:
            delta_t, allowed_diff = line.split()
            float(allowed_diff)  # Raise ValueError if problem
            if not RateOfChangeThreshold.is_delta_t_valid(delta_t):
                raise ValueError()
        except ValueError:
            raise forms.ValidationError(
                _(f'"{line}" is not a valid (delta_t, allowed_diff) pair')
            )

    def save(self, *args, **kwargs):
        result = super().save(*args, **kwargs)
        self.instance.set_roc_thresholds(self.cleaned_data["roc_thresholds"])
        return result


class SynopticTimeseriesGroupInline(admin.StackedInline):
    form = SynopticTimeseriesGroupForm
    model = SynopticGroupStation.timeseries_groups.through
    extra = 0
    fields = (
        ("timeseries_group", "order", "title"),
        ("low_limit", "high_limit"),
        ("group_with", "subtitle"),
        ("default_chart_min", "default_chart_max"),
        ("roc_thresholds", "symmetric_rocc"),
    )

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name in ("timeseries_group", "group_with"):
            synopticgroupstation_id = int(request.resolver_match.kwargs["object_id"])
            station = SynopticGroupStation.objects.get(
                id=synopticgroupstation_id
            ).station
            kwargs["queryset"] = TimeseriesGroup.objects.filter(gentity_id=station)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    class Media:
        css = {"all": ("css/extra_admin.css",)}


@admin.register(SynopticGroupStation)
class GroupStationAdmin(admin.ModelAdmin):
    inlines = [SynopticTimeseriesGroupInline]
    exclude = ["synoptic_group", "station", "order", "timeseries_group"]
    list_filter = ["synoptic_group"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
