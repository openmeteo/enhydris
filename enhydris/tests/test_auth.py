from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site
from django.test import TestCase, override_settings

from model_mommy import mommy


@override_settings(SITE_ID=1)
class AuthTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.site1 = mommy.make(Site, id=1, domain="hello.com", name="hello")
        cls.site2 = mommy.make(Site, id=2, domain="world.com", name="world")
        cls.alice = User.objects.create_user(
            username="alice", password="topsecret", is_staff=True, is_superuser=True
        )
        cls.bob = User.objects.create_user(
            username="bob", password="topsecret", is_staff=True, is_superuser=False
        )
        cls.alice.groups.all().delete()
        cls.bob.groups.all().delete()

    def test_superuser_can_login(self):
        self.assertTrue(self.client.login(username="alice", password="topsecret"))

    def test_normal_user_cannot_login(self):
        self.assertFalse(self.client.login(username="bob", password="topsecret"))

    def test_normal_user_can_login_when_in_appropriate_group(self):
        hello_group = Group.objects.create(name="hello.com")
        self.bob.groups.add(hello_group)
        self.assertTrue(self.client.login(username="bob", password="topsecret"))
