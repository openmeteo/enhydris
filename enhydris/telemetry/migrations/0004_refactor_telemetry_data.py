from copy import copy

from django.db import migrations


def direct(apps, schema_editor):
    Telemetry = apps.get_model("telemetry", "Telemetry")
    Sensor = apps.get_model("telemetry", "Sensor")
    TimeseriesGroup = apps.get_model("enhydris", "TimeseriesGroup")

    for telemetry in Telemetry.objects.all():
        telemetry.username = telemetry.additional_config["email"]
        telemetry.password = telemetry.additional_config["api_key"]
        telemetry.remote_station_id = telemetry.additional_config["station"]
        del telemetry.additional_config["email"]
        del telemetry.additional_config["api_key"]
        del telemetry.additional_config["station"]

        assert telemetry.additional_config["station_id"] == telemetry.station.id
        del telemetry.additional_config["station_id"]

        for key, value in copy(telemetry.additional_config).items():
            assert key.startswith("sensor_")
            sensor_id = key[7:]
            timeseries_group = TimeseriesGroup.objects.get(pk=int(value))
            Sensor.objects.create(
                telemetry=telemetry,
                sensor_id=sensor_id,
                timeseries_group=timeseries_group,
            )
            del telemetry.additional_config[key]

        assert telemetry.additional_config == {}

        telemetry.save()


def reverse(apps, schema_editor):
    Telemetry = apps.get_model("telemetry", "Telemetry")
    Sensor = apps.get_model("telemetry", "Sensor")

    for telemetry in Telemetry.objects.all():
        telemetry.additional_config["email"] = telemetry.username
        telemetry.additional_config["api_key"] = telemetry.password
        telemetry.additional_config["station"] = telemetry.remote_station_id
        telemetry.additional_config["station_id"] = telemetry.station.id
        for sensor in Sensor.objects.filter(telemetry=telemetry):
            value = f"{sensor.timeseries_group.id}"
            telemetry.additional_config[f"sensor_{sensor.sensor_id}"] = value
        telemetry.save()


class Migration(migrations.Migration):

    dependencies = [
        ("telemetry", "0003_refactor_telemetry"),
    ]

    operations = [
        migrations.RunPython(direct, reverse),
    ]
