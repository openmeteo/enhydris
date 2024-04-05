from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings


@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=True)
class AuthenticationRequiredTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_user("alice", password="topsecret", is_superuser=True)

    def test_simple_view(self):
        response = self.client.get("/nonexistent/")
        self.assertRedirects(response, f"{settings.LOGIN_URL}?next=/nonexistent/")

    def test_password_reset(self):
        response = self.client.get("/accounts/password/reset/")
        self.assertEqual(response.status_code, 200)
