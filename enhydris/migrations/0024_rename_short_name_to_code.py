# Generated by Django 2.2.4 on 2019-09-24 10:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("enhydris", "0023_refactor_garea_part_b")]

    operations = [
        migrations.RenameField(
            model_name="gentity", old_name="short_name", new_name="code"
        )
    ]
