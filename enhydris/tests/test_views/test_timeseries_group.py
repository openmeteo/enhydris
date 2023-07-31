from django.test import TestCase

from model_mommy import mommy

from enhydris.models import Timeseries
from enhydris.tests import TimeseriesDataMixin


class RedirectOldUrlsTestCase(TestCase):
    def test_old_timeseries_url_redirects(self):
        mommy.make(
            Timeseries,
            id=1169,
            timeseries_group__id=100174,
            timeseries_group__gentity__id=200348,
        )
        r = self.client.get("/timeseries/d/1169/")
        self.assertRedirects(
            r,
            "/stations/200348/timeseriesgroups/100174/",
            status_code=301,
            fetch_redirect_response=False,
        )

    def test_old_timeseries_url_for_nonexistent_timeseries_returns_404(self):
        r = self.client.get("/timeseries/d/1169/")
        self.assertEqual(r.status_code, 404)


class TimeseriesGroupDetailTestCase(TimeseriesDataMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_timeseries(publicly_available=True)

    def _get_response(self):
        self.response = self.client.get(
            f"/stations/{self.station.id}/timeseriesgroups/{self.timeseries_group.id}/"
        )

    def test_timeseries_group_without_timeseries(self):
        self.timeseries_group.timeseries_set.all().delete()
        self._get_response()
        self.assertNotContains(self.response, "form-item-download")
        self.assertContains(self.response, "alert-info")  # "No data" message

    def test_timeseries_group_with_timeseries(self):
        self._get_response()
        self.assertContains(self.response, "form-item-download")
        self.assertNotContains(self.response, "alert-info")  # "No data" message

    def test_timeseries_group_with_all_timeseries_inaccessible(self):
        self.timeseries.publicly_available = False
        self.timeseries.save()
        self._get_response()
        self.assertNotContains(self.response, "form-item-download")
        self.assertContains(self.response, "alert-info")  # "No data" message

    def test_title(self):
        self._get_response()
        self.assertContains(
            self.response, "<title>Beauty — Komboti — Enhydris</title>", html=True
        )

    def test_heading(self):
        self._get_response()
        self.assertContains(
            self.response, "<h2>Beauty <span>(beauton)</span></h2>", html=True
        )

    def test_download_form(self):
        self._get_response()
        self.assertContains(
            self.response, '<label for="id_timeseries_id_0">Initial</label>', html=True
        )
