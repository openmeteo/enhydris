from django.db import migrations


def populate_new_time_step(apps, schema_editor):
    NewTimeStep(apps, schema_editor).populate()


def populate_old_time_step(apps, schema_editor):
    OldTimeStep(apps, schema_editor).populate()


direct_conversion = {
    (5, 0): "5min",
    (10, 0): "10min",
    (15, 0): "15min",
    (30, 0): "30min",
    (60, 0): "H",
    (1440, 0): "D",
    (0, 1): "M",
    (0, 12): "Y",
}


reverse_conversion = {v: k for k, v in direct_conversion.items()}


class NewTimeStep:
    def __init__(self, apps, schema_editor):
        self.Timeseries = apps.get_model("enhydris", "Timeseries")

    def populate(self):
        for timeseries in self.Timeseries.objects.filter(time_step__isnull=False):
            self._populate_for_timeseries(timeseries)

    def _populate_for_timeseries(self, timeseries):
        step = timeseries.time_step
        minutes, months = step.length_minutes, step.length_months
        timeseries.new_time_step = direct_conversion[minutes, months]
        timeseries.save()


class OldTimeStep:
    def __init__(self, apps, schema_editor):
        self.Timeseries = apps.get_model("enhydris", "Timeseries")
        self.TimeStep = apps.get_model("enhydris", "TimeStep")

    def populate(self):
        for timeseries in self.Timeseries.objects.exclude(new_time_step=""):
            self._populate_for_timeseries(timeseries)

    def _populate_for_timeseries(self, timeseries):
        new_step = timeseries.new_time_step
        mins, months = reverse_conversion[new_step]
        time_step, created = self.TimeStep.objects.get_or_create(
            length_minutes=mins, length_months=months
        )
        timeseries.time_step = time_step
        timeseries.save()


class Migration(migrations.Migration):

    dependencies = [
        ("enhydris", "0026_add_new_time_step"),
    ]

    operations = [migrations.RunPython(populate_new_time_step, populate_old_time_step)]
