import django.contrib.gis.db.models.fields
from django.contrib.gis.geos import Point
from django.db import migrations


def copy_geometries_to_gentity(apps, schema_editor):
    Gpoint = apps.get_model("enhydris", "Gpoint")
    for gpoint in Gpoint.objects.all():
        gpoint.geom = gpoint.geometry
        gpoint.save()

    Garea = apps.get_model("enhydris", "Garea")
    for garea in Garea.objects.all():
        garea.geom = garea.geometry
        garea.save()


def copy_geometries_from_gentity(apps, schema_editor):
    Gpoint = apps.get_model("enhydris", "Gpoint")
    for gpoint in Gpoint.objects.all():
        gpoint.geometry = gpoint.geom
        gpoint.save()

    Garea = apps.get_model("enhydris", "Garea")
    for garea in Garea.objects.all():
        garea.geometry = garea.geom
        garea.save()


class Migration(migrations.Migration):

    dependencies = [("enhydris", "0024_rename_short_name_to_code")]

    operations = [
        migrations.AlterField(
            model_name="gpoint",
            name="geometry",
            field=django.contrib.gis.db.models.fields.PointField(
                default=Point(x=0, y=0, srid=4326), srid=4326
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="garea",
            name="geometry",
            field=django.contrib.gis.db.models.fields.PointField(
                default=Point(x=0, y=0, srid=4326), srid=4326
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="gentity",
            name="geom",
            field=django.contrib.gis.db.models.fields.GeometryField(
                default=Point(x=0, y=0, srid=4326), srid=4326
            ),
            preserve_default=False,
        ),
        migrations.RunPython(copy_geometries_to_gentity, copy_geometries_from_gentity),
        migrations.RemoveField(model_name="garea", name="geometry"),
        migrations.RemoveField(model_name="gpoint", name="geometry"),
        migrations.DeleteModel(name="Gline"),
    ]
