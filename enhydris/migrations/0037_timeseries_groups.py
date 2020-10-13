import textwrap

import django.db.models.deletion
import django.utils.timezone
from django.core.exceptions import MultipleObjectsReturned
from django.db import migrations, models
from django.db.models import Q


class TimeseriesAnalyzer:
    """Determine the group and type for a time series.

    Call TimeseriesAnalyzer(timeseries_group_migrator, timeseries), where "timeseries"
    is a Timeseries object, to determine the group and type. If enhydris_autoprocess is
    not installed, the group is always a new group and the type is "raw". Otherwise the
    data from enhydris_autoprocess is investigated to find or create an appropriate
    group.
    """

    ATTRIBUTES_TO_MOVE = [
        "last_modified",
        "name",
        "hidden",
        "remarks",
        "gentity",
        "time_zone",
        "unit_of_measurement",
        "variable",
        "precision",
    ]

    def __init__(self, timeseries_group_migrator, timeseries):
        tgm = timeseries_group_migrator
        self.Timeseries = tgm.Timeseries
        self.TimeseriesGroup = tgm.TimeseriesGroup
        self.enhydris_autoprocess_is_installed = tgm.enhydris_autoprocess_is_installed
        if self.enhydris_autoprocess_is_installed:
            self.AutoProcess = tgm.AutoProcess
        self.timeseries = timeseries

        self.timeseries_group = self._get_timeseries_group()
        self.timeseries_type = self._get_type()

    def _get_timeseries_group(self):
        if self.enhydris_autoprocess_is_installed:
            return self._get_timeseries_group_from_enhydris_autoprocess()
        else:
            return self._get_new_timeseries_group(self.timeseries)

    def _get_timeseries_group_from_enhydris_autoprocess(self):
        self._get_all_sibling_timeseries()
        try:
            return self.TimeseriesGroup.objects.get(
                timeseries__in=self.sibling_timeseries
            )
        except self.TimeseriesGroup.DoesNotExist:
            return self._get_new_timeseries_group(self.sibling_timeseries[0])

    def _get_all_sibling_timeseries(self):
        self.sibling_timeseries = (
            self._get_left_siblings(self.timeseries)
            + [self.timeseries]
            + self._get_right_siblings(self.timeseries)
        )

    def _get_left_siblings(self, timeseries):
        try:
            auto_process = self.AutoProcess.objects.filter(
                Q(rangecheck__isnull=False) | Q(aggregation__isnull=False)
            ).get(target_timeseries=timeseries)
            return self._get_left_siblings(auto_process.source_timeseries) + [
                auto_process.source_timeseries
            ]
        except self.AutoProcess.DoesNotExist:
            return []

    def _get_right_siblings(self, timeseries):
        try:
            auto_process = self.AutoProcess.objects.filter(
                Q(rangecheck__isnull=False) | Q(aggregation__isnull=False)
            ).get(source_timeseries=timeseries)
            return [auto_process.target_timeseries] + self._get_right_siblings(
                auto_process.target_timeseries
            )
        except self.AutoProcess.DoesNotExist:
            return []

    def _get_new_timeseries_group(self, timeseries):
        attrs = {attr: getattr(timeseries, attr) for attr in self.ATTRIBUTES_TO_MOVE}
        timeseries_group = self.TimeseriesGroup(**attrs)
        timeseries_group.save()
        return timeseries_group

    def _get_type(self):
        if not self.enhydris_autoprocess_is_installed:
            return self._get_types()["RAW"]
        else:
            return self._get_type_when_autoprocess_is_installed()

    def _get_type_when_autoprocess_is_installed(self):
        try:
            auto_process = self.AutoProcess.objects.get(
                target_timeseries=self.timeseries
            )
            return self._get_type_from_auto_process(auto_process)
        except self.AutoProcess.DoesNotExist:
            return self._get_types()["RAW"]

    def _get_type_from_auto_process(self, auto_process):
        if hasattr(auto_process, "rangecheck"):
            return self._get_types()["CHECKED"]
        elif hasattr(auto_process, "aggregation"):
            return self._get_types()["AGGREGATED"]
        else:
            return self._get_types()["RAW"]

    def _get_types(self):
        from enhydris.models import Timeseries

        return {
            "RAW": Timeseries.RAW,
            "CHECKED": Timeseries.CHECKED,
            "AGGREGATED": Timeseries.AGGREGATED,
        }


class TimeseriesGroupMigrator:
    def __init__(self, apps, schema_editor):
        self.Timeseries = apps.get_model("enhydris", "Timeseries")
        self.TimeseriesGroup = apps.get_model("enhydris", "TimeseriesGroup")
        try:
            self.AutoProcess = apps.get_model("enhydris_autoprocess", "AutoProcess")
            self.enhydris_autoprocess_is_installed = True
        except LookupError:
            self.enhydris_autoprocess_is_installed = False

    def forward(self):
        for timeseries in self.Timeseries.objects.all():
            analyzer = TimeseriesAnalyzer(self, timeseries)
            timeseries.timeseries_group = analyzer.timeseries_group
            timeseries.type = analyzer.timeseries_type
            timeseries.save()

    def reverse(self):
        # The reverse migration actually does not work because of
        # https://code.djangoproject.com/ticket/26739
        for timeseries_group in self.TimeseriesGroup.objects.all():
            timeseries = self._get_only_timeseries(timeseries_group)
            for attr in self.ATTRIBUTES_TO_MOVE:
                setattr(timeseries, attr, getattr(timeseries_group, attr))
            timeseries.save()

    def _get_only_timeseries(self, timeseries_group):
        try:
            return self.Timeseries.objects.get(timeseries_group=timeseries_group)
        except MultipleObjectsReturned:
            self.error(timeseries_group)

    def _error(self, timeseries_group):
        msg = f"""\
            The time series group with id={timeseries_group.id} has either zero time
            series or more than one time series. This migration is reversible only if
            each time series group has exactly one time series.
            """
        raise ValueError(textwrap.dedent(msg))


def copy_data_from_Timeseries_to_TimeseriesGroup(apps, schema_editor):
    TimeseriesGroupMigrator(apps, schema_editor).forward()


def reverse_copy_data_from_Timeseries_to_TimeseriesGroup(apps, schema_editor):
    TimeseriesGroupMigrator(apps, schema_editor).reverse()


class Migration(migrations.Migration):

    dependencies = [
        ("enhydris", "0036_remove_timeseries_datafile_and_bounding_dates"),
    ]

    operations = [
        migrations.CreateModel(
            name="TimeseriesGroup",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "last_modified",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False, null=True
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        blank=True,
                        help_text=(
                            "In most cases, you want to leave this blank, and the name "
                            "of the time series group will be the name of the "
                            'variable, such as "Temperature". However, if you have two '
                            "groups with the same variable (e.g. if you have two "
                            "temperature sensors), specify a name to tell them apart."
                        ),
                        max_length=200,
                    ),
                ),
                ("hidden", models.BooleanField(default=False)),
                (
                    "precision",
                    models.SmallIntegerField(
                        help_text=(
                            "The number of decimal digits to which the values of the "
                            "time series will be rounded. It's usually positive, but "
                            "it can be zero or negative; for example, for humidity it "
                            "is usually zero; for wind direction in degrees, depending "
                            "on the sensor, you might want to specify precision -1, "
                            "which means the value will be 10, or 20, or 30, etc. This "
                            "only affects the rounding of values when the time series "
                            "is retrieved; values are always stored with all the "
                            "decimal digits provided."
                        )
                    ),
                ),
                ("remarks", models.TextField(blank=True)),
                (
                    "gentity",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="enhydris.Gentity",
                    ),
                ),
                (
                    "time_zone",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="enhydris.TimeZone",
                    ),
                ),
                (
                    "unit_of_measurement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="enhydris.UnitOfMeasurement",
                    ),
                ),
                (
                    "variable",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="enhydris.Variable",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="timeseries",
            name="timeseries_group",
            field=models.ForeignKey(
                default=0,
                on_delete=django.db.models.deletion.CASCADE,
                to="enhydris.TimeseriesGroup",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="timeseries",
            name="type",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (100, "Raw"),
                    (150, "Processed"),
                    (200, "Checked"),
                    (300, "Regularized"),
                    (400, "Aggregated"),
                ],
                default=100,
            ),
            preserve_default=False,
        ),
        migrations.RunPython(
            copy_data_from_Timeseries_to_TimeseriesGroup,
            reverse_copy_data_from_Timeseries_to_TimeseriesGroup,
        ),
        migrations.AlterModelOptions(
            name="timeseries",
            options={
                "ordering": ("type",),
                "verbose_name": "Time series",
                "verbose_name_plural": "Time series",
            },
        ),
        migrations.AlterUniqueTogether(
            name="timeseries",
            unique_together={("timeseries_group", "type", "time_step")},
        ),
        migrations.AddConstraint(
            model_name="timeseries",
            constraint=models.UniqueConstraint(
                condition=models.Q(type=100),
                fields=("timeseries_group",),
                name="only_one_raw_timeseries_per_group",
            ),
        ),
        migrations.AddConstraint(
            model_name="timeseries",
            constraint=models.UniqueConstraint(
                condition=models.Q(type=200),
                fields=("timeseries_group",),
                name="only_one_checked_timeseries_per_group",
            ),
        ),
        migrations.AddConstraint(
            model_name="timeseries",
            constraint=models.UniqueConstraint(
                condition=models.Q(type=300),
                fields=("timeseries_group",),
                name="only_one_regularized_timeseries_per_group",
            ),
        ),
        migrations.RemoveField(model_name="timeseries", name="gentity"),
        migrations.RemoveField(model_name="timeseries", name="hidden"),
        migrations.RemoveField(model_name="timeseries", name="name"),
        migrations.RemoveField(model_name="timeseries", name="precision"),
        migrations.RemoveField(model_name="timeseries", name="remarks"),
        migrations.RemoveField(model_name="timeseries", name="time_zone"),
        migrations.RemoveField(model_name="timeseries", name="unit_of_measurement"),
        migrations.RemoveField(model_name="timeseries", name="variable"),
    ]
