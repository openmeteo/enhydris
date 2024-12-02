from io import StringIO

from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _

import nested_admin

from enhydris.admin.station import (
    InlinePermissionsMixin,
    StationAdmin,
    TimeseriesGroupInline,
)
from enhydris.models import TimeseriesGroup, check_time_step

from .models import (
    Aggregation,
    Checks,
    CurveInterpolation,
    CurvePeriod,
    RangeCheck,
    RateOfChangeCheck,
    RateOfChangeThreshold,
)

# We override StationAdmin's render_change_form method in order to specify a custom
# template. We do this in order to offer some model-wide help (help_text is only
# available for fields).


def render_change_form(self, *args, **kwargs):
    self.change_form_template = "enhydris_autoprocess/station_change_form.html"
    return super(StationAdmin, self).render_change_form(*args, **kwargs)


StationAdmin.render_change_form = render_change_form


class TimeseriesGroupForm(forms.ModelForm):
    lower_bound = forms.FloatField(required=False, label=_("Lower bound"))
    soft_lower_bound = forms.FloatField(required=False, label=_("Soft lower bound"))
    soft_upper_bound = forms.FloatField(required=False, label=_("Soft upper bound"))
    upper_bound = forms.FloatField(required=False, label=_("Upper bound"))
    rocc_thresholds = forms.CharField(
        required=False,
        widget=forms.Textarea,
        label=_("Thresholds"),
        help_text=_(
            'The allowed differences, one per line, like "10min 7.3" (without the '
            "quotes). This example "
            "means that any change higher than 7.3 within 10 minutes will be "
            "considered an error. The time length is specified as a number "
            "plus a unit, with no space in between. The units available are min "
            "(minutes), h (hours) and D (days)."
        ),
    )
    rocc_symmetric = forms.BooleanField(
        required=False,
        label=_("Symmetric"),
        help_text=RateOfChangeCheck._meta.get_field("symmetric").help_text,
    )

    class Meta:
        model = TimeseriesGroup
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.range_check_subform = _RangeCheckSubform(self)
        self.roc_check_subform = _RocCheckSubform(self)

    def clean(self):
        self.range_check_subform.check_that_bounds_are_present_or_absent()
        return super().clean()

    def clean_rocc_thresholds(self):
        return self.roc_check_subform.clean_rocc_thresholds()

    def save(self, *args, **kwargs):
        result = super().save(*args, **kwargs)
        self.range_check_subform.save()
        self.roc_check_subform.save()
        return result


class _RangeCheckSubform:
    def __init__(self, parent_form):
        self.parent_form = parent_form
        self._populate_fields()

    def _populate_fields(self):
        pf = self.parent_form
        if not getattr(pf, "instance", None) or pf.instance.id is None:
            return
        try:
            range_check = RangeCheck.objects.get(checks__timeseries_group=pf.instance)
            pf.fields["lower_bound"].initial = range_check.lower_bound
            pf.fields["soft_lower_bound"].initial = range_check.soft_lower_bound
            pf.fields["soft_upper_bound"].initial = range_check.soft_upper_bound
            pf.fields["upper_bound"].initial = range_check.upper_bound
        except RangeCheck.DoesNotExist:
            pass

    def check_that_bounds_are_present_or_absent(self):
        pf = self.parent_form
        hard_bounds = [
            pf.cleaned_data[x] is not None for x in ("lower_bound", "upper_bound")
        ]
        soft_bounds = [
            pf.cleaned_data[f"soft_{x}_bound"] is not None for x in ("lower", "upper")
        ]
        if all(hard_bounds) or (not any(hard_bounds) and not any(soft_bounds)):
            return
        raise forms.ValidationError(
            _(
                "To perform a range check, lower and upper bound must be specified; "
                "otherwise, all four bounds must be empty."
            )
        )

    def save(self):
        if self.parent_form.cleaned_data["lower_bound"] is None:
            self._delete_range_check()
        else:
            self._create_or_update_range_check()

    def _delete_range_check(self):
        try:
            checks = Checks.objects.get(timeseries_group=self.parent_form.instance)
            range_check = RangeCheck.objects.get(checks=checks)
            range_check.delete()
        except (Checks.DoesNotExist, RangeCheck.DoesNotExist):
            pass

    def _create_or_update_range_check(self):
        checks, created = Checks.objects.get_or_create(
            timeseries_group=self.parent_form.instance
        )
        try:
            self._save_existing_range_check(checks)
        except RangeCheck.DoesNotExist:
            self._save_new_range_check(checks)

    def _save_existing_range_check(self, checks):
        range_check = RangeCheck.objects.get(checks=checks)
        range_check.lower_bound = self.parent_form.cleaned_data["lower_bound"]
        range_check.soft_lower_bound = self.parent_form.cleaned_data["soft_lower_bound"]
        range_check.soft_upper_bound = self.parent_form.cleaned_data["soft_upper_bound"]
        range_check.upper_bound = self.parent_form.cleaned_data["upper_bound"]
        range_check.save()

    def _save_new_range_check(self, checks):
        RangeCheck.objects.create(
            checks=checks,
            lower_bound=self.parent_form.cleaned_data["lower_bound"],
            soft_lower_bound=self.parent_form.cleaned_data["soft_lower_bound"],
            soft_upper_bound=self.parent_form.cleaned_data["soft_upper_bound"],
            upper_bound=self.parent_form.cleaned_data["upper_bound"],
        )


class _RocCheckSubform:
    def __init__(self, parent_form):
        self.parent_form = parent_form
        self._populate_fields()

    def _populate_fields(self):
        pf = self.parent_form
        if not getattr(self.parent_form, "instance", None) or pf.instance.id is None:
            return
        try:
            roc_check = RateOfChangeCheck.objects.get(
                checks__timeseries_group=pf.instance
            )
            pf.fields["rocc_symmetric"].initial = roc_check.symmetric
            pf.fields["rocc_thresholds"].initial = roc_check.get_thresholds_as_text()
        except RateOfChangeCheck.DoesNotExist:
            pass

    def clean_rocc_thresholds(self):
        data = self.parent_form.cleaned_data["rocc_thresholds"]
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

    def save(self):
        if not self.parent_form.cleaned_data["rocc_thresholds"]:
            self._delete_roc_check()
        else:
            self._create_or_update_roc_check()

    def _delete_roc_check(self):
        try:
            checks = Checks.objects.get(timeseries_group=self.parent_form.instance)
            roc_check = RateOfChangeCheck.objects.get(checks=checks)
            roc_check.delete()
        except (Checks.DoesNotExist, RateOfChangeCheck.DoesNotExist):
            pass

    def _create_or_update_roc_check(self):
        checks, created = Checks.objects.get_or_create(
            timeseries_group=self.parent_form.instance
        )
        try:
            rocc_check = self._save_existing_roc_check(checks)
        except RateOfChangeCheck.DoesNotExist:
            rocc_check = self._save_new_roc_check(checks)
        rocc_check.set_thresholds(self.parent_form.cleaned_data["rocc_thresholds"])

    def _save_existing_roc_check(self, checks):
        rocc_check = RateOfChangeCheck.objects.get(checks=checks)
        rocc_check.symmetric = self.parent_form.cleaned_data["rocc_symmetric"]
        rocc_check.save()
        return rocc_check

    def _save_new_roc_check(self, checks):
        return RateOfChangeCheck.objects.create(
            checks=checks, symmetric=self.parent_form.cleaned_data["rocc_symmetric"]
        )


TimeseriesGroupInline.form = TimeseriesGroupForm
TimeseriesGroupInline.fieldsets.append(
    (
        _("Range check"),
        {
            "fields": (
                "lower_bound",
                "soft_lower_bound",
                "soft_upper_bound",
                "upper_bound",
            ),
            "classes": ("collapse",),
        },
    ),
)
TimeseriesGroupInline.fieldsets.append(
    (
        _("Time consistency check"),
        {
            "fields": (("rocc_thresholds", "rocc_symmetric"),),
            "classes": ("collapse",),
        },
    ),
)


class CurvePeriodForm(forms.ModelForm):
    points = forms.CharField(
        widget=forms.Textarea,
        help_text=_(
            "The points that form the curve. You can copy/paste them from a "
            "spreadsheet, two columns: X and Y. Copy and paste the points only, "
            "without headings. If you key them in instead, they must be one point "
            "per line, first X then Y, separated by tab or comma."
        ),
        label=_("Points"),
    )

    class Meta:
        model = CurvePeriod
        fields = ("start_date", "end_date", "points")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            point_queryset = self.instance.curvepoint_set.order_by("x")
            lines = ["{}\t{}".format(p.x, p.y) for p in point_queryset]
            self.initial["points"] = "\n".join(lines)

    def clean_points(self):
        data = self.cleaned_data["points"]
        for i, row in enumerate(StringIO(data)):
            row = row.replace("\t", ",")
            try:
                x, y = [float(item) for item in row.split(",")]
            except ValueError:
                raise forms.ValidationError(
                    'Error in line {}: "{}" is not a valid pair of numbers'.format(
                        i + 1, row
                    )
                )
        return data

    def save(self, *args, **kwargs):
        result = super().save(*args, **kwargs)
        self.instance.set_curve(self.cleaned_data["points"])
        return result


class CurvePeriodInline(InlinePermissionsMixin, nested_admin.NestedTabularInline):
    model = CurvePeriod
    form = CurvePeriodForm
    points = models.CharField()
    extra = 1


class CurveInterpolationForm(forms.ModelForm):
    class Meta:
        model = CurveInterpolation
        fields = "__all__"


class CurveInterpolationInline(
    InlinePermissionsMixin, nested_admin.NestedTabularInline
):
    model = CurveInterpolation
    fk_name = "timeseries_group"
    classes = ("collapse",)
    form = CurveInterpolationForm
    inlines = [CurvePeriodInline]
    extra = 1

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "target_timeseries_group":
            try:
                station_id = request.path.strip("/").split("/")[-2]
                kwargs["queryset"] = TimeseriesGroup.objects.filter(gentity=station_id)
            except ValueError:
                kwargs["queryset"] = TimeseriesGroup.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


TimeseriesGroupInline.inlines.append(CurveInterpolationInline)


class AggregationForm(forms.ModelForm):
    class Meta:
        model = Aggregation
        fields = (
            "target_time_step",
            "method",
            "max_missing",
            "resulting_timestamp_offset",
        )
        widgets = {"resulting_timestamp_offset": forms.TextInput(attrs={"size": 7})}

    def clean_target_time_step(self):
        try:
            result = self.cleaned_data.get("target_time_step", "")
            check_time_step(result)
            return result
        except ValueError as e:
            raise forms.ValidationError(str(e))


class AggregationInline(InlinePermissionsMixin, nested_admin.NestedTabularInline):
    model = Aggregation
    classes = ("collapse",)
    form = AggregationForm
    verbose_name = _("Aggregation")
    verbose_name_plural = _("Aggregations")
    extra = 1


TimeseriesGroupInline.inlines.append(AggregationInline)
