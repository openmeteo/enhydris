from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("enhydris", "0031_change_unitofmeasurement_meta"),
    ]

    operations = [
        migrations.RemoveField(model_name="gentityfile", name="file_type"),
        migrations.DeleteModel(name="FileType"),
    ]
