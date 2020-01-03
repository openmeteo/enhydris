from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("enhydris", "0025_gentity_geom"),
    ]

    operations = [
        migrations.AddField(
            model_name="timeseries",
            name="new_time_step",
            field=models.CharField(
                blank=True,
                help_text=(
                    'E.g. "10min", "H" (hourly), "D" (daily), "M" (monthly), "Y" '
                    "(yearly). More specifically, it's an optional number plus a unit, "
                    "with no space in between. The units available are min, H, D, M, "
                    "Y. Leave empty if the time series is irregular."
                ),
                max_length=7,
            ),
        ),
    ]
