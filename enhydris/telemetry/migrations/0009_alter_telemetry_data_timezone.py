import zoneinfo

from django.db import migrations, models


def fix_zone_name(timezone):
    if timezone.startswith("Etc/GMT+"):
        return "UTC-" + timezone[8:]
    elif timezone.startswith("Etc/GMT-"):
        return "UTC+" + timezone[8:]
    else:
        return timezone


timezones = zoneinfo.available_timezones()
timezone_choices = [(zone, fix_zone_name(zone)) for zone in timezones]
timezone_choices.sort()


class Migration(migrations.Migration):
    dependencies = [
        ("telemetry", "0008_remove_telemetry_fetch_offset_timezone"),
    ]

    operations = [
        migrations.AlterField(
            model_name="telemetry",
            name="data_timezone",
            field=models.CharField(
                choices=timezone_choices,
                default="UTC",
                help_text=(
                    'The time zone of the data, like "Europe/Athens" or "Etc/GMT".'
                ),
                max_length=35,
                verbose_name="Time zone of the timestamps",
            ),
        ),
    ]
