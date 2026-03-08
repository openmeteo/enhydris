import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("enhydris", "0120_remove_gpoint_original_srid"),
    ]

    operations = [
        migrations.CreateModel(
            name="NewVariableTranslation",
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
                    models.CharField(max_length=15, verbose_name="Language"),
                ),
                ("descr", models.CharField(max_length=200, verbose_name="Description")),
                (
                    "variable",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="translations",
                        to="enhydris.variable",
                        verbose_name="Variable",
                    ),
                ),
            ],
            options={
                "unique_together": {("variable", "language_code")},
            },
        ),
    ]
