import django.contrib.gis.db.models.fields
from django.contrib.gis.geos import Point
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("enhydris", "0006_lint")]

    operations = [
        migrations.AlterField(
            model_name="gpoint",
            name="point",
            field=django.contrib.gis.db.models.fields.PointField(
                default=Point(0.0, 0.0), srid=4326
            ),
            preserve_default=False,
        )
    ]
