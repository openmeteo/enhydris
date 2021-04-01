from django.db import migrations


def check_that_is_automatic_has_the_same_value_everywhere(apps, schema_editor):
    Station = apps.get_model("enhydris", "Station")
    true_instances = Station.objects.filter(is_automatic=True).count()
    false_instances = Station.objects.filter(is_automatic=False).count()
    if true_instances and false_instances:
        raise RuntimeError(
            "Station.is_automatic has been abolished, and upgrading involves deleting "
            "the field. I would do so if it had the same value for all stations, "
            "however it seems it's true for some stations and false for some other "
            "stations. So maybe it's holding some useful information. Cowardly "
            "refusing to proceed. Manually make all stations have the same "
            "value in is_automatic, then try again."
        )


def do_nothing(*args, **kwargs):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("enhydris", "0108_gentity_images_data"),
    ]

    operations = [
        migrations.RunPython(
            check_that_is_automatic_has_the_same_value_everywhere, do_nothing
        ),
        migrations.RemoveField(
            model_name="station",
            name="is_automatic",
        ),
    ]
