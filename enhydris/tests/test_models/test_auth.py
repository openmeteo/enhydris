from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site
from django.test import TestCase, override_settings

from model_mommy import mommy


class AddCurrentSiteGroupToNewUsersTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.site1 = mommy.make(Site, id=1, domain="hello.com", name="hello")
        cls.site2 = mommy.make(Site, id=2, domain="world.com", name="world")

    @override_settings(SITE_ID=2)
    def test_creating_user_creates_group_and_puts_him_in_it(self):
        user = User.objects.create_user(username="alice", password="topsecret")
        self.assertTrue(user.groups.filter(name="world.com").exists())

    @override_settings(SITE_ID=2)
    def test_creating_user_puts_him_in_existing_group(self):
        Group.objects.create(name="world.com")
        user = User.objects.create_user(username="alice", password="topsecret")
        self.assertTrue(user.groups.filter(name="world.com").exists())

    @override_settings(SITE_ID=1)
    def test_updating_user_does_not_touch_groups(self):
        user = User.objects.create_user(username="alice", password="topsecret")
        user.groups.all().delete()
        user.is_staff = True
        user.save()
        self.assertFalse(user.groups.filter(name="world.com").exists())
