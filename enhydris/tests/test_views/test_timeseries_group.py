from django.test import TestCase, override_settings

from enhydris.tests import TimeseriesDataMixin


@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
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
