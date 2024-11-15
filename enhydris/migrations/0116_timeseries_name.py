# Generated by Django 3.2.24 on 2024-11-12 13:29

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("enhydris", "0115_timeseries_publicly_available"),
    ]

    operations = [
        migrations.AddField(
            model_name="timeseries",
            name="name",
            field=models.CharField(
                blank=True,
                default="",
                help_text=(
                    "You can leave this empty, unless you have many time series for "
                    "this group with the same type and time step (for example, if you "
                    "have a time series aggregated on the mean and another aggregated "
                    "on the max value)."
                ),
                max_length=100,
                verbose_name="Name",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="timeseries",
            unique_together={("timeseries_group", "type", "time_step", "name")},
        ),
    ]
