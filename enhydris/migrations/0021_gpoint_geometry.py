# Generated by Django 2.2.4 on 2019-09-08 05:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("enhydris", "0020_abolish_station_type")]

    operations = [
        migrations.RenameField(
            model_name="gpoint", old_name="point", new_name="geometry"
        )
    ]