from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("enhydris", "0122_remove_parler_part2"),
    ]

    operations = [
        migrations.DeleteModel(
            name="VariableTranslation",
        ),
        migrations.RenameModel(
            old_name="NewVariableTranslation",
            new_name="VariableTranslation",
        ),
    ]
