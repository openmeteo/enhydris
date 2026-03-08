from typing import Any

from django.apps.registry import Apps
from django.db import migrations


def forward(apps: Apps, _: Any) -> None:
    VariableTranslation = apps.get_model("enhydris", "VariableTranslation")
    NewVariableTranslation = apps.get_model("enhydris", "NewVariableTranslation")

    for vt in VariableTranslation.objects.all():
        NewVariableTranslation.objects.create(
            variable_id=vt.master_id,
            language_code=vt.language_code,
            descr=vt.descr,
        )


def backward(apps: Apps, _: Any) -> None:
    VariableTranslation = apps.get_model("enhydris", "VariableTranslation")
    NewVariableTranslation = apps.get_model("enhydris", "NewVariableTranslation")
    for nvt in NewVariableTranslation.objects.all():
        VariableTranslation.objects.create(
            master_id=nvt.variable_id,
            language_code=nvt.language_code,
            descr=nvt.descr,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("enhydris", "0121_remove_parler_part1"),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
