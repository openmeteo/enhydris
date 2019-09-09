import django.contrib.gis.db.models.fields
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("enhydris", "0022_refactor_garea")]

    operations = [
        migrations.RemoveField(model_name="waterbasin", name="garea_ptr"),
        migrations.RemoveField(model_name="waterbasin", name="parent"),
        migrations.RemoveField(model_name="waterdivision", name="garea_ptr"),
        migrations.RemoveField(model_name="gentity", name="political_division"),
        migrations.RemoveField(model_name="gentity", name="water_basin"),
        migrations.RemoveField(model_name="gentity", name="water_division"),
        migrations.DeleteModel(name="PoliticalDivision"),
        migrations.DeleteModel(name="WaterBasin"),
        migrations.DeleteModel(name="WaterDivision"),
        migrations.RemoveField(model_name="garea", name="area"),
        migrations.RenameField(
            model_name="garea", old_name="mpoly", new_name="geometry"
        ),
        migrations.AlterField(
            model_name="garea",
            name="geometry",
            field=django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326),
        ),
        migrations.AddField(
            model_name="garea",
            name="category",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="enhydris.GareaCategory"
            ),
        ),
    ]
