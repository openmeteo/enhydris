from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("enhydris", "0028_remove_old_time_step")]

    operations = [
        migrations.RemoveField(model_name="timeseries", name="interval_type"),
        migrations.DeleteModel(name="IntervalType"),
    ]
