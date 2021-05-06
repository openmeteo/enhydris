"""Check that authentication has been correctly setup.

Technically these aren't unit tests, they are functional tests. We don't need
unit tests because authentication is handled by third-party applications (namely
Django, DRF, and dj-rest-auth). But we make these functional tests to ensure
we have the configuration setup correctly.

Since we use Token authentication, "login" doesn't really login; it only provides
the token for a user, creating it if it does not already exist.
"""
import re

import django
from django.contrib.auth import get_user_model
from django.test.utils import override_settings
from rest_framework.test import APITestCase

from allauth.account.models import EmailAddress
from rest_captcha import utils as captcha_utils
from rest_captcha import views as captcha_views


class AuthTestCase(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="alice",
            email="alice@alice.com",
            password="topsecret",
            is_active=True,
        )
        EmailAddress.objects.create(
            user=self.user, email=self.user.email, primary=True, verified=True
        )

    def test_unauthenticated(self):
        response = self.client.get("/api/auth/user/")
        self.assertEqual(response.status_code, 401)

    def test_authenticated(self):
        self.client.force_authenticate(self.user)
        response = self.client.get("/api/auth/user/")
        self.assertEqual(response.status_code, 200)

    def test_login(self):
        response = self.client.post(
            "/api/auth/login/", data={"username": "alice", "password": "topsecret"}
        )
        self.assertEqual(response.status_code, 200)
        token = response.data["key"]
        response = self.client.get(
            "/api/auth/user/", HTTP_AUTHORIZATION="Token " + token
        )
        self.assertEqual(response.status_code, 200)

    def test_fail_login(self):
        response = self.client.post(
            "/api/auth/login/", data={"username": "alice", "password": "wrongpassword"}
        )
        self.assertEqual(response.status_code, 400)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class ResetPasswordTestCase(APITestCase):
    def test_reset_password(self):
        # Create a user
        User = get_user_model()
        self.user = User.objects.create_user(
            username="alice", email="alice@example.com", password="topsecret1"
        )

        # Ooops... I thought my password was topsecret2, but apparently I
        # forgot it...
        r = self.client.login(username="alice", password="topsecret2")
        self.assertFalse(r)

        # No problem, let me submit the password reset form
        response = self.client.post(
            "/api/auth/password/reset/", data={"email": "alice@example.com"}
        )
        self.assertEqual(response.status_code, 200)

        # Did I receive an email?
        self.assertEqual(len(django.core.mail.outbox), 1)

        # Get the link from the email
        m = re.search(r"http://[^/]+(\S+)", django.core.mail.outbox[0].body)
        reset_link = m.group(1)

        # Visit the link and submit the form
        response = self.client.get(reset_link)
        self.assertEqual(response.status_code, 302)
        response = self.client.post(
            response["Location"],
            {"new_password1": "topsecret2", "new_password2": "topsecret2"},
        )
        self.assertEqual(response.status_code, 302)

        # Cool, now let me log in
        r = self.client.login(username="alice", password="topsecret2")
        self.assertTrue(r)


_settings_for_registration_open = {
    "ENHYDRIS_REGISTRATION_OPEN": True,
    "ACCOUNT_EMAIL_REQUIRED": True,
    "ACCOUNT_EMAIL_VERIFICATION": "mandatory",
}

_settings_for_registration_closed = {
    "ENHYDRIS_REGISTRATION_OPEN": False,
    "ACCOUNT_EMAIL_REQUIRED": False,
    "ACCOUNT_EMAIL_VERIFICATION": "optional",
}


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class RegisterTestCase(APITestCase):
    @override_settings(**_settings_for_registration_open)
    def test_register(self):
        # Get a captcha
        response = self.client.post("/api/captcha/")
        self.assertEqual(response.status_code, 200)
        captcha_key = response.data["captcha_key"]
        captcha_cache_key = captcha_utils.get_cache_key(captcha_key)
        captcha_solution = captcha_views.cache.get(captcha_cache_key)

        # Submit registration form
        response = self.client.post(
            "/api/auth/registration/",
            data={
                "username": "alice",
                "email": "alice@alice.com",
                "password1": "topsecret",
                "password2": "topsecret",
                "captcha_key": captcha_key,
                "captcha_value": captcha_solution,
            },
        )
        self.assertEqual(response.status_code, 201)

        # We shouldn't be able to login yet
        response = self.client.post(
            "/api/auth/login/", data={"username": "alice", "password": "topsecret"}
        )
        self.assertEqual(response.status_code, 400)

        # Did I receive an email?
        self.assertEqual(len(django.core.mail.outbox), 1)

        # Get the key from the link in the email
        m = re.search(r"http://.*/([^/]+)/", django.core.mail.outbox[0].body)
        registration_key = m.group(1)

        # Submit it
        response = self.client.post(
            "/api/auth/registration/verify-email/", data={"key": registration_key}
        )
        self.assertEqual(response.status_code, 200)

        # We should now be able to login
        response = self.client.post(
            "/api/auth/login/", data={"username": "alice", "password": "topsecret"}
        )
        self.assertEqual(response.status_code, 200)

    @override_settings(**_settings_for_registration_open)
    def test_wrong_captcha(self):
        # Get a captcha
        response = self.client.post("/api/captcha/")
        self.assertEqual(response.status_code, 200)
        captcha_key = response.data["captcha_key"]

        # Submit registration form
        response = self.client.post(
            "/api/auth/registration/",
            data={
                "username": "alice",
                "email": "alice@alice.com",
                "password1": "topsecret",
                "password2": "topsecret",
                "captcha_key": captcha_key,
                "captcha_value": "wrong",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(django.core.mail.outbox), 0)

    @override_settings(**_settings_for_registration_closed)
    def test_registration_returns_404(self):
        # Submit registration form
        response = self.client.post(
            "/api/auth/registration/",
            data={
                "username": "alice",
                "email": "alice@alice.com",
                "password1": "topsecret",
                "password2": "topsecret",
            },
        )
        self.assertEqual(response.status_code, 404)
