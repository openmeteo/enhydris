from django.contrib.auth.models import User
from django.test import TestCase

from bs4 import BeautifulSoup


class SiteHeaderTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice",
            password="topsecret",
            is_active=True,
            is_staff=True,
            is_superuser=False,
        )
        self.client.login(username="alice", password="topsecret")
        self.response = self.client.get("/admin/")

    def test_site_name(self):
        self.soup = BeautifulSoup(self.response.content, "html.parser")
        value = self.soup.find(id="site-name").a.contents[0]
        self.assertEqual(value, "Enhydris dashboard")
