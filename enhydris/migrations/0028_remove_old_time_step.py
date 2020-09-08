from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("enhydris", "0027_populate_new_time_step"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="timesteptranslation", unique_together=None
        ),
        migrations.RemoveField(model_name="timesteptranslation", name="master"),
        migrations.RemoveField(model_name="timeseries", name="time_step"),
        migrations.DeleteModel(name="TimeStep"),
        migrations.DeleteModel(name="TimeStepTranslation"),
        migrations.RenameField(
            model_name="timeseries", old_name="new_time_step", new_name="time_step"
        ),
        migrations.RemoveField(
            model_name="timeseries", name="timestamp_offset_minutes"
        ),
        migrations.RemoveField(model_name="timeseries", name="timestamp_offset_months"),
        migrations.RemoveField(
            model_name="timeseries", name="timestamp_rounding_minutes"
        ),
        migrations.RemoveField(
            model_name="timeseries", name="timestamp_rounding_months"
        ),
    ]
