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

    def test_api_view(self):
        response = self.client.get("/api/nonexistent/")
        self.assertEqual(response.status_code, 401)

    def test_api_view_with_login(self):
        login_successful = self.client.login(username="alice", password="topsecret")
        assert login_successful
        response = self.client.get("/nonexistent/")
        self.assertEqual(response.status_code, 404)

    def test_login_api_view(self):
        response = self.client.options("/api/auth/login/")
        self.assertEqual(response.status_code, 200)

    def test_api_password_reset(self):
        response = self.client.options("/api/auth/password/reset/")
        self.assertEqual(response.status_code, 200)
