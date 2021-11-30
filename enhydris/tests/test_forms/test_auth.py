from django.test import TestCase, override_settings

from enhydris.forms import MyRegistrationForm


@override_settings(REGISTRATION_OPEN=True)
class RegistrationFormTestCase(TestCase):
    def test_registration_form_submission(self):
        post_data = {"usename": "bob", "password": "topsecret"}
        r = self.client.post("/accounts/register/", post_data)
        self.assertEqual(r.status_code, 200)

    def test_registation_form_fails_blank_submission(self):
        r = self.client.post("/accounts/register/", {})
        self.assertFormError(r, "form", "password1", "This field is required.")

    def test_registration_form_username_help_text(self):
        """Check that username help_text is not Django's default.

        Django's default username help_text is inappropriate for this, because it starts
        with the word "Required". This is confusing because actually all form's fields
        are required.
        """
        myform = MyRegistrationForm()
        self.assertEqual(
            myform.fields["username"].help_text[:3],
            "150",  # "150 characters or less..."
        )

    def test_registration_form_requires_agreement_to_tos(self):
        r = self.client.get("/accounts/register/")
        self.assertContains(r, "I have read and agree to the Terms of Service")
