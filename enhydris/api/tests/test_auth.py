"""Check that authentication has been correctly setup.

Technically these aren't unit tests, they are functional tests. We don't need
unit tests because authentication is handled by third-party applications (namely
Django, DRF, and dj-rest-auth). But we make these functional tests to ensure
we have the configuration setup correctly.

Since we use Token authentication, "login" doesn't really login; it only provides
the token for a user, creating it if it does not already exist.
"""

import re
from typing import cast

import django.core.mail
from django.contrib.auth import get_user_model
from django.contrib.auth.models import UserManager
from django.test.utils import override_settings
from rest_framework.test import APITestCase


@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class AuthTestCase(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = cast(UserManager[User], User.objects).create_user(
            username="alice",
            email="alice@alice.com",
            password="topsecret",
            is_active=True,
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
        self.user = cast(UserManager[User], User.objects).create_user(
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
        body = django.core.mail.outbox[0].body
        assert isinstance(body, str)
        m = re.search(r"http://[^/]+(\S+)", body)
        assert m is not None
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
