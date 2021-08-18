from django.db import migrations


def add_users_to_domain(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Group = apps.get_model("auth", "Group")
    Site = apps.get_model("sites", "Site")

    try:
        current_domain = Site.objects.get_current().domain
    except Site.DoesNotExist:
        return
    try:
        group = Group.objects.get(name=current_domain)
    except Group.DoesNotExist:
        group = Group.objects.create(name=current_domain)

    for user in User.objects.all():
        if not user.groups.filter(id=group.id).exists():
            user.groups.add(group)


def add_stations_to_domain(apps, schema_editor):
    Station = apps.get_model("enhydris", "Station")
    Site = apps.get_model("sites", "Site")

    try:
        current_site = Site.objects.get_current()
    except Site.DoesNotExist:
        return

    for station in Station.objects.all():
        if not station.sites.filter(id=current_site.id).exists():
            station.sites.add(current_site)


def dummy(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("enhydris", "0110_sites"),
    ]

    operations = [
        migrations.RunPython(add_users_to_domain, dummy),
        migrations.RunPython(add_stations_to_domain, dummy),
    ]
