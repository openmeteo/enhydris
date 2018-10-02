from django.contrib.auth.models import User
from django.test import TestCase

from model_mommy import mommy

from enhydris.models import Station, Timeseries


class TimeseriesFormTestCase(TestCase):
    def test_no_dates(self):
        """Test that start_date and end_date are excluded

        start_date_utc and end_date_utc are derived fields; they should not be
        shown in the model form.
        """
        self.user = User.objects.create_superuser(
            "test", email="test@test.com", password="test"
        )
        self.user.save()
        self.station = mommy.make(Station, name="mystation", creator=self.user)
        self.ts = mommy.make(Timeseries, name="tstest", gentity=self.station)

        self.client.login(username="test", password="test")
        response = self.client.get("/timeseries/edit/{}/".format(self.ts.id))
        self.assertNotContains(response, "start_date")
        self.assertNotContains(response, "end_date")
