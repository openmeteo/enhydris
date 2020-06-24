from django.test import TestCase

from enhydris.forms import DownloadDataForm
from enhydris.tests import TimeseriesDataMixin


class DownloadDataFormTestCase(TestCase, TimeseriesDataMixin):
    def setUp(self):
        self.create_timeseries()

    def test_timeseries_choices(self):
        form = DownloadDataForm(timeseries_group=self.timeseries_group)
        self.assertIn(
            '<input type="radio" name="timeseries_id" value="42" '
            'required id="id_timeseries_id_0">\n Raw',
            form.as_p(),
        )

    def test_initial_timeseries_group_id(self):
        form = DownloadDataForm(timeseries_group=self.timeseries_group)
        self.assertEqual(form.fields["timeseries_group_id"].initial, 31)

    def test_initial_station_id(self):
        form = DownloadDataForm(timeseries_group=self.timeseries_group)
        self.assertEqual(form.fields["station_id"].initial, 20)
