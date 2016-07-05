from datetime import datetime, timedelta
from six import StringIO
import textwrap

from django.test import TestCase

from model_mommy import mommy

from enhydris.hcore.models import Station, Timeseries, timezone


class TimeseriesTestCase(TestCase):

    def setUp(self):
        self.station_komboti = mommy.make(Station, name='Komboti')
        self.ts_komboti_rain = mommy.make(
            Timeseries, gentity=self.station_komboti, name='Rain',
            unit_of_measurement__symbol='mm', time_zone__code='EET',
            time_zone__utc_offset=120)

        self.ts_komboti_rain.set_data(StringIO(textwrap.dedent(
            """\
            2015-10-22 15:00,0,
            2015-10-22 15:10,0.1,
            2015-10-22 15:20,0.2,
            """)))

    def test_get_all_data(self):
        adataframe = self.ts_komboti_rain.get_data()
        self.assertEqual(len(adataframe), 3)
        self.assertAlmostEqual(adataframe.ix['2015-10-22 15:00'].value, 0)
        self.assertAlmostEqual(adataframe.ix['2015-10-22 15:10'].value, 0.1)
        self.assertAlmostEqual(adataframe.ix['2015-10-22 15:20'].value, 0.2)

    def test_get_data_with_start_date(self):
        adataframe = self.ts_komboti_rain.get_data(
            start_date='2015-10-22 15:10')
        self.assertEqual(len(adataframe), 2)
        self.assertAlmostEqual(adataframe.ix['2015-10-22 15:10'].value, 0.1)
        self.assertAlmostEqual(adataframe.ix['2015-10-22 15:20'].value, 0.2)

    def test_get_data_with_end_date(self):
        adataframe = self.ts_komboti_rain.get_data(
            end_date=datetime(2015, 10, 22, 15, 10))
        self.assertEqual(len(adataframe), 2)
        self.assertAlmostEqual(adataframe.ix['2015-10-22 15:00'].value, 0)
        self.assertAlmostEqual(adataframe.ix['2015-10-22 15:10'].value, 0.1)

    def test_get_data_with_start_and_end_date(self):
        adataframe = self.ts_komboti_rain.get_data(
            start_date='2015-10-22 15:05', end_date='2015-10-22 15:15')
        self.assertEqual(len(adataframe), 1)
        self.assertAlmostEqual(adataframe.ix['2015-10-22 15:10'].value, 0.1)

    def test_start_date_end_date(self):
        atzinfo = timezone(timedelta(minutes=120), 'EET')
        start_date = datetime(2015, 10, 22, 15, 0, tzinfo=atzinfo)
        end_date = datetime(2015, 10, 22, 15, 20, tzinfo=atzinfo)

        self.assertEqual(self.ts_komboti_rain.start_date, start_date)
        self.assertEqual(
            self.ts_komboti_rain.start_date.tzinfo.utcoffset(start_date),
            timedelta(minutes=120))
        self.assertEqual(self.ts_komboti_rain.end_date, end_date)
        self.assertEqual(
            self.ts_komboti_rain.end_date.tzinfo.utcoffset(end_date),
            timedelta(minutes=120))

        # Reload from database to make sure results are the same
        t = Timeseries.objects.get(pk=self.ts_komboti_rain.id)
        self.assertEqual(t.start_date, start_date)
        self.assertEqual(t.start_date.tzinfo.utcoffset(start_date),
                         timedelta(minutes=120))
        self.assertEqual(t.end_date, end_date)
        self.assertEqual(t.start_date.tzinfo.utcoffset(end_date),
                         timedelta(minutes=120))

        # Empty the time series and try again
        self.ts_komboti_rain.set_data(StringIO(''))
        self.assertIsNone(self.ts_komboti_rain.start_date)
        self.assertIsNone(self.ts_komboti_rain.end_date)
        t = Timeseries.objects.get(pk=self.ts_komboti_rain.id)
        self.assertIsNone(t.start_date)
        self.assertIsNone(t.end_date)
