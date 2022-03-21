from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def add_current_site_group_to_new_users(sender, instance, created, **kwargs):
    """Automatically give permissions on site to new users.

    When a user is created, he is automatically put in a group whose name is the same as
    the domain of the current django.contrib.sites.models.Site. The custom
    authentication of Enhydris will then allow him to login on that site, but not on
    other sites (unless an admin subsequently also adds him to more groups).
    """
    if created:
        current_domain = Site.objects.get_current().domain
        try:
            group = Group.objects.get(name=current_domain)
        except Group.DoesNotExist:
            group = Group.objects.create(name=current_domain)
        instance.groups.add(group)
