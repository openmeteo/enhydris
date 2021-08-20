import django.contrib.sites.managers
import django.db.models.manager
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sites", "0002_alter_domain_unique"),
        ("enhydris", "0109_remove_is_automatic"),
    ]

    operations = [
        migrations.AddField(
            model_name="gentity",
            name="sites",
            field=models.ManyToManyField(to="sites.Site"),
        ),
        migrations.AlterModelManagers(
            name="station",
            managers=[
                ("objects", django.db.models.manager.Manager()),
                ("on_site", django.contrib.sites.managers.CurrentSiteManager()),
            ],
        ),
    ]
