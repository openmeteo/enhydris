from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("enhydris", "0005_remove_gentity_generic_data")]

    operations = [
        migrations.AlterModelOptions(
            name="gentityaltcode", options={"ordering": ("type__descr", "value")}
        ),
        migrations.AlterModelOptions(
            name="gentityfile", options={"ordering": ("descr",)}
        ),
        migrations.AlterModelOptions(
            name="overseer",
            options={
                "ordering": ("start_date", "person__last_name", "person__first_name")
            },
        ),
    ]
