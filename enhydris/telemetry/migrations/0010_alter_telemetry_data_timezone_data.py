from django.db import migrations


def forward(apps, schema_editor):
    Telemetry = apps.get_model("telemetry", "Telemetry")
    Telemetry.objects.filter(data_timezone="").update(data_timezone="UTC")


class Migration(migrations.Migration):
    dependencies = [
        ("telemetry", "0009_alter_telemetry_data_timezone"),
    ]

    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
