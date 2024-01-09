from django.test import TestCase, override_settings

from enhydris.tests import TimeseriesDataMixin


@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class TimeseriesDownloadButtonTestCase(TimeseriesDataMixin, TestCase):
    def setUp(self):
        self.download_button = (
            '<button type="submit" class="btn form-btn-download">download</button>'
        )

    def _get_response(self):
        self.response = self.client.get(
            f"/stations/{self.station.id}/timeseriesgroups/{self.timeseries_group.id}/"
        )

    def test_contains_download_button_when_timeseries_data_is_available(self):
        self.create_timeseries(publicly_available=True)
        self._get_response()
        self.assertContains(self.response, self.download_button)

    def test_has_no_download_link_when_timeseries_data_is_not_available(self):
        self.create_timeseries(publicly_available=False)
        self._get_response()
        self.assertNotContains(self.response, self.download_button)

    def test_has_no_unavailability_message_when_timeseries_data_is_available(self):
        self.create_timeseries(publicly_available=True)
        self._get_response()
        self.assertNotContains(self.response, "No data is available for downloading")

    def test_shows_unavailability_message_when_timeseries_data_is_unavailable(self):
        self.create_timeseries(publicly_available=False)
        self._get_response()
        self.assertContains(self.response, "No data is available for downloading")


@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class DownloadDataTestCase(TimeseriesDataMixin, TestCase):
    def setUp(self):
        self.create_timeseries(publicly_available=True)

    def _make_request(self, station_id, timeseries_group_id, timeseries_id):
        self.response = self.client.get(
            f"/downloaddata/?station_id={station_id}"
            f"&timeseries_group_id={timeseries_group_id}"
            f"&timeseries_id={timeseries_id}&format=csv"
        )

    def test_redirects(self):
        self._make_request(
            self.station.id, self.timeseries_group.id, self.timeseries.id
        )
        self.assertRedirects(
            self.response,
            expected_url=(
                f"/api/stations/{self.station.id}/timeseriesgroups"
                f"/{self.timeseries_group.id}/timeseries/{self.timeseries.id}"
                "/data/?fmt=csv"
            ),
            fetch_redirect_response=False,
        )

    def test_returns_404_on_total_garbage(self):
        self.response = self.client.get("/downloaddata/?hello=world")
        self.assertEqual(self.response.status_code, 404)

    def test_returns_404_on_garbage_timeseries_group(self):
        self.response = self.client.get(
            "/downloaddata/?station_id=hello&timeseries_group_id=world"
            "&timeseries_id=earth&format=CSV"
        )
        self.assertEqual(self.response.status_code, 404)

    def test_returns_404_on_garbage_station(self):
        self.response = self.client.get(
            "/downloaddata/?station_id=hello&timeseries_group_id=50"
            "&timeseries_id=earth&format=CSV"
        )
        self.assertEqual(self.response.status_code, 404)

    def test_returns_404_on_no_data(self):
        self.response = self.client.get("/downloaddata/")
        self.assertEqual(self.response.status_code, 404)
