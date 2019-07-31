import django.db.models.deletion
from django.db import migrations, models

import parler.fields
import parler.models

from .helpers.parler import Migrator


def move_variable_descr(apps, schema_editor):
    Migrator(apps, schema_editor, "Variable").migrate()


def reverse_move_variable_descr(apps, schema_editor):
    Migrator(apps, schema_editor, "Variable").reverse_migrate()


class Migration(migrations.Migration):

    dependencies = [("enhydris", "0013_overseers")]

    operations = [
        migrations.CreateModel(
            name="VariableTranslation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "language_code",
                    models.CharField(
                        db_index=True, max_length=15, verbose_name="Language"
                    ),
                ),
                ("descr", models.CharField(blank=True, max_length=200)),
                (
                    "master",
                    parler.fields.TranslationsForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="translations",
                        to="enhydris.Variable",
                    ),
                ),
            ],
            options={
                "verbose_name": "variable Translation",
                "db_table": "enhydris_variable_translation",
                "db_tablespace": "",
                "managed": True,
                "default_permissions": (),
                "unique_together": {("language_code", "master")},
            },
        ),
        migrations.RunPython(move_variable_descr, reverse_move_variable_descr),
        migrations.AlterModelOptions(name="variable", options={}),
        migrations.RemoveField(model_name="variable", name="descr"),
    ]
