from django.db import migrations


def check_that_generic_data_is_empty(apps, schema_editor):
    GentityGenericData = apps.get_model("enhydris", "GentityGenericData")
    if GentityGenericData.objects.exists():
        raise RuntimeError(
            "GentityGenericData has been abolished, and upgrading involves deleting "
            "the database table. In this case, the table appears to have data. "
            "Cowardly refusing to proceed. Manually delete the contents of the table, "
            "then try again."
        )


def do_nothing(*args, **kwargs):
    pass


class Migration(migrations.Migration):

    dependencies = [("enhydris", "0003_user_name")]

    operations = [
        migrations.RunPython(check_that_generic_data_is_empty, do_nothing),
        migrations.RemoveField(model_name="gentitygenericdata", name="data_type"),
        migrations.RemoveField(model_name="gentitygenericdata", name="gentity"),
        migrations.DeleteModel(name="GentityGenericData"),
        migrations.DeleteModel(name="GentityGenericDataType"),
    ]
