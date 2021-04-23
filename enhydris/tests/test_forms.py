from django.test import TestCase, override_settings

from enhydris.forms import DownloadDataForm, MyRegistrationForm
from enhydris.tests import TimeseriesDataMixin


class DownloadDataFormTestCase(TestCase, TimeseriesDataMixin):
    def setUp(self):
        self.create_timeseries()

    def test_timeseries_choices(self):
        form = DownloadDataForm(timeseries_group=self.timeseries_group)
        self.assertIn(
            f'<input type="radio" name="timeseries_id" value="{self.timeseries.id}" '
            'required id="id_timeseries_id_0">\n Initial',
            form.as_p(),
        )

    def test_initial_timeseries_group_id(self):
        form = DownloadDataForm(timeseries_group=self.timeseries_group)
        self.assertEqual(
            form.fields["timeseries_group_id"].initial, self.timeseries_group.id
        )

    def test_initial_station_id(self):
        form = DownloadDataForm(timeseries_group=self.timeseries_group)
        self.assertEqual(form.fields["station_id"].initial, self.station.id)


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
