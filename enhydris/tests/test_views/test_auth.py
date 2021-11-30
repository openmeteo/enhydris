import re

import django
from django.test import TransactionTestCase, override_settings


# NOTE: For an explanation of how captchas work in the tests, see CAPTCHA_TEST_MODE
# in settings.py.
class RegisterTestCase(TransactionTestCase):
    available_apps = [
        "django.contrib.auth",
        "enhydris",
        "registration",
        "captcha",
        "bootstrap4",
    ]

    @override_settings(REGISTRATION_OPEN=True)
    def test_register(self):
        # Submit registration form
        response = self.client.post(
            "/accounts/register/",
            data={
                "username": "alice",
                "email": "alice@alice.com",
                "password1": "topsecret",
                "password2": "topsecret",
                "tos": "on",
                "captcha_0": "irrelevant",
                "captcha_1": "PASSED",
            },
        )
        self.assertEqual(response.status_code, 302)

        # We shouldn't be able to login yet
        response = self.client.post(
            "/api/auth/login/", data={"username": "alice", "password": "topsecret"}
        )
        self.assertEqual(response.status_code, 400)

        # Did I receive an email?
        self.assertEqual(len(django.core.mail.outbox), 1)

        # Get the key from the link in the email
        m = re.search(r"http://([^/]+)(.*)", django.core.mail.outbox[0].body)
        path = m.group(2)

        # Submit it
        response = self.client.get(path)
        self.assertEqual(response.status_code, 302)

        # We should now be able to login
        response = self.client.post(
            "/api/auth/login/", data={"username": "alice", "password": "topsecret"}
        )
        self.assertEqual(response.status_code, 200)

    @override_settings(REGISTRATION_OPEN=True)
    def test_wrong_captcha(self):
        response = self.client.post(
            "/accounts/register/",
            data={
                "username": "alice",
                "email": "alice@alice.com",
                "password1": "topsecret",
                "password2": "topsecret",
                "tos": "on",
                "captcha_0": "irrelevant",
                "captcha_1": "WRONG CAPTCHA",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(django.core.mail.outbox), 0)

    @override_settings(REGISTRATION_OPEN=False)
    def test_registration_fails_when_registration_is_closed(self):
        response = self.client.post(
            "/accounts/register/",
            data={
                "username": "alice",
                "email": "alice@alice.com",
                "password1": "topsecret",
                "password2": "topsecret",
                "captcha_0": "irrelevant",
                "captcha_1": "PASSED",
            },
        )
        self.assertRedirects(response, expected_url="/accounts/register/closed/")
        self.assertEqual(len(django.core.mail.outbox), 0)

    @override_settings(REGISTRATION_OPEN=True)
    def test_has_sign_up_link_when_registration_is_open(self):
        response = self.client.get("/")
        self.assertContains(response, "register")

    @override_settings(REGISTRATION_OPEN=False)
    def test_has_no_sign_up_link_when_registration_is_open(self):
        response = self.client.get("/")
        self.assertNotContains(response, "register")
