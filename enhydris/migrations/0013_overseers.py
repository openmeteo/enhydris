from django.db import migrations, models


def move_overseers(apps, schema_editor):
    Overseer = apps.get_model("enhydris", "Overseer")
    for overseer in Overseer.objects.all():
        value = overseer.person.last_name + " " + overseer.person.first_name
        if overseer.station.overseer:
            raise RuntimeError(
                (
                    "Overseers are being changed so that only one may be stored per "
                    "station. Apparently station with id={} has more than one "
                    "overseers. Manually fix that, then try again."
                ).format(overseer.station.id)
            )
        overseer.station.overseer = value
        overseer.station.save()


def reverse_move_overseers(apps, schema_editor):
    Overseer = apps.get_model("enhydris", "Overseer")
    Station = apps.get_model("enhydris", "Station")
    Person = apps.get_model("enhydris", "Person")
    for station in Station.objects.exclude(overseer=""):
        last_name, _, first_name = station.overseer.partition(" ")
        person, created = Person.objects.get_or_create(
            last_name=last_name,
            first_name=first_name,
            ordering_string="{} {}".format(last_name, first_name),
        )
        Overseer.objects.create(station=station, person=person)


def remove_persons(apps, schema_editor):
    Person = apps.get_model("enhydris", "Person")
    Person.objects.filter(owned_stations=None).delete()


def dummy_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [("enhydris", "0012_simplify_coordinates")]

    operations = [
        migrations.AddField(
            model_name="station",
            name="overseer",
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.RunPython(move_overseers, reverse_move_overseers),
        migrations.RemoveField(model_name="station", name="overseers"),
        migrations.DeleteModel(name="Overseer"),
        migrations.RunPython(remove_persons, dummy_reverse),
    ]
