from datetime import datetime, timedelta
from six import StringIO
import shutil
import tempfile
import textwrap

from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.test import TestCase
from django.test.utils import override_settings

from model_mommy import mommy

from enhydris.models import Instrument, Station, Timeseries, timezone


class RandomEnhydrisTimeseriesDataDir(override_settings):
    """
    Override ENHYDRIS_TIMESERIES_DATA_DIR to a temporary directory.

    Specifying "@RandomEnhydrisTimeseriesDataDir()" as a decorator is the same
    as "@override_settings(ENHYDRIS_TIMESERIES_DATA_DIR=tempfile.mkdtemp())",
    except that in the end it removes the temporary directory.
    """

    def __init__(self):
        self.tmpdir = tempfile.mkdtemp()
        super(RandomEnhydrisTimeseriesDataDir, self).__init__(
            ENHYDRIS_TIMESERIES_DATA_DIR=self.tmpdir
        )

    def disable(self):
        super(RandomEnhydrisTimeseriesDataDir, self).disable()
        shutil.rmtree(self.tmpdir)


@RandomEnhydrisTimeseriesDataDir()
class TimeseriesTestCase(TestCase):
    def setUp(self):
        self.station_komboti = mommy.make(Station, name="Komboti")
        self.ts_komboti_rain = mommy.make(
            Timeseries,
            gentity=self.station_komboti,
            name="Rain",
            unit_of_measurement__symbol="mm",
            time_zone__code="EET",
            time_zone__utc_offset=120,
        )

        self.ts_komboti_rain.set_data(
            StringIO(
                textwrap.dedent(
                    """\
            2015-10-22 15:00,0,
            2015-10-22 15:10,0.1,
            2015-10-22 15:20,0.2,
            """
                )
            )
        )

    def test_get_all_data(self):
        adataframe = self.ts_komboti_rain.get_data()
        self.assertEqual(len(adataframe), 3)
        self.assertAlmostEqual(adataframe.ix["2015-10-22 15:00"].value, 0)
        self.assertAlmostEqual(adataframe.ix["2015-10-22 15:10"].value, 0.1)
        self.assertAlmostEqual(adataframe.ix["2015-10-22 15:20"].value, 0.2)

    def test_get_data_with_start_date(self):
        adataframe = self.ts_komboti_rain.get_data(start_date="2015-10-22 15:10")
        self.assertEqual(len(adataframe), 2)
        self.assertAlmostEqual(adataframe.ix["2015-10-22 15:10"].value, 0.1)
        self.assertAlmostEqual(adataframe.ix["2015-10-22 15:20"].value, 0.2)

    def test_get_data_with_end_date(self):
        adataframe = self.ts_komboti_rain.get_data(
            end_date=datetime(2015, 10, 22, 15, 10)
        )
        self.assertEqual(len(adataframe), 2)
        self.assertAlmostEqual(adataframe.ix["2015-10-22 15:00"].value, 0)
        self.assertAlmostEqual(adataframe.ix["2015-10-22 15:10"].value, 0.1)

    def test_get_data_with_start_and_end_date(self):
        adataframe = self.ts_komboti_rain.get_data(
            start_date="2015-10-22 15:05", end_date="2015-10-22 15:15"
        )
        self.assertEqual(len(adataframe), 1)
        self.assertAlmostEqual(adataframe.ix["2015-10-22 15:10"].value, 0.1)

    def test_start_date_end_date(self):
        atzinfo = timezone(timedelta(minutes=120), "EET")
        start_date = datetime(2015, 10, 22, 15, 0, tzinfo=atzinfo)
        end_date = datetime(2015, 10, 22, 15, 20, tzinfo=atzinfo)

        self.assertEqual(self.ts_komboti_rain.start_date, start_date)
        self.assertEqual(
            self.ts_komboti_rain.start_date.tzinfo.utcoffset(start_date),
            timedelta(minutes=120),
        )
        self.assertEqual(self.ts_komboti_rain.end_date, end_date)
        self.assertEqual(
            self.ts_komboti_rain.end_date.tzinfo.utcoffset(end_date),
            timedelta(minutes=120),
        )

        # Reload from database to make sure results are the same
        t = Timeseries.objects.get(pk=self.ts_komboti_rain.id)
        self.assertEqual(t.start_date, start_date)
        self.assertEqual(
            t.start_date.tzinfo.utcoffset(start_date), timedelta(minutes=120)
        )
        self.assertEqual(t.end_date, end_date)
        self.assertEqual(
            t.start_date.tzinfo.utcoffset(end_date), timedelta(minutes=120)
        )

        # Empty the time series and try again
        self.ts_komboti_rain.set_data(StringIO(""))
        self.assertIsNone(self.ts_komboti_rain.start_date)
        self.assertIsNone(self.ts_komboti_rain.end_date)
        t = Timeseries.objects.get(pk=self.ts_komboti_rain.id)
        self.assertIsNone(t.start_date)
        self.assertIsNone(t.end_date)


class StationTestCase(TestCase):
    def test_original_coordinates(self):
        station_komboti = mommy.make(
            Station,
            name="Komboti",
            point=Point(x=21.06071, y=39.09518, srid=4326),
            srid=2100,
        )
        s = Station.objects.get(name="Komboti")
        self.assertAlmostEqual(s.original_abscissa(), 245648.96, places=1)
        self.assertAlmostEqual(s.original_ordinate(), 4331165.20, places=1)

    def test_original_coordinates_with_null_srid(self):
        station_komboti = mommy.make(
            Station,
            name="Komboti",
            point=Point(x=21.06071, y=39.09518, srid=4326),
            srid=None,
        )
        s = Station.objects.get(name="Komboti")
        self.assertAlmostEqual(s.original_abscissa(), 21.06071)
        self.assertAlmostEqual(s.original_ordinate(), 39.09518)


class RulesTestCase(TestCase):
    def setUp(self):
        self.alice = mommy.make(User, username="alice")
        self.bob = mommy.make(User, username="bob")
        self.charlie = mommy.make(User, username="charlie")

        self.station = mommy.make(Station, creator=self.alice, maintainers=[self.bob])
        self.instrument = mommy.make(Instrument, station=self.station)
        self.timeseries = mommy.make(Timeseries, gentity=self.station)

    def test_creator_can_edit_station(self):
        self.assertTrue(self.alice.has_perm("enhydris.change_station", self.station))

    def test_maintainer_can_edit_station(self):
        self.assertTrue(self.bob.has_perm("enhydris.change_station", self.station))

    def test_irrelevant_user_cannot_edit_station(self):
        self.assertFalse(self.charlie.has_perm("enhydris.change_station", self.station))

    def test_creator_can_delete_station(self):
        self.assertTrue(self.alice.has_perm("enhydris.delete_station", self.station))

    def test_maintainer_cannot_delete_station(self):
        self.assertFalse(self.bob.has_perm("enhydris.delete_station", self.station))

    def test_irrelevant_user_cannot_delete_station(self):
        self.assertFalse(self.charlie.has_perm("enhydris.change_station", self.station))

    def test_creator_can_edit_timeseries(self):
        self.assertTrue(
            self.alice.has_perm("enhydris.change_timeseries", self.timeseries)
        )

    def test_maintainer_can_edit_timeseries(self):
        self.assertTrue(
            self.bob.has_perm("enhydris.change_timeseries", self.timeseries)
        )

    def test_irrelevant_user_cannot_edit_timeseries(self):
        self.assertFalse(
            self.charlie.has_perm("enhydris.change_timeseries", self.timeseries)
        )

    def test_creator_can_delete_timeseries(self):
        self.assertTrue(
            self.alice.has_perm("enhydris.delete_timeseries", self.timeseries)
        )

    def test_maintainer_can_delete_timeseries(self):
        self.assertTrue(
            self.bob.has_perm("enhydris.delete_timeseries", self.timeseries)
        )

    def test_irrelevant_user_cannot_delete_timeseries(self):
        self.assertFalse(
            self.charlie.has_perm("enhydris.change_timeseries", self.timeseries)
        )

    def test_creator_can_edit_instrument(self):
        self.assertTrue(
            self.alice.has_perm("enhydris.change_instrument", self.instrument)
        )

    def test_maintainer_can_edit_instrument(self):
        self.assertTrue(
            self.bob.has_perm("enhydris.change_instrument", self.instrument)
        )

    def test_irrelevant_user_cannot_edit_instrument(self):
        self.assertFalse(
            self.charlie.has_perm("enhydris.change_instrument", self.instrument)
        )

    def test_creator_can_delete_instrument(self):
        self.assertTrue(
            self.alice.has_perm("enhydris.delete_instrument", self.instrument)
        )

    def test_maintainer_can_delete_instrument(self):
        self.assertTrue(
            self.bob.has_perm("enhydris.delete_instrument", self.instrument)
        )

    def test_irrelevant_user_cannot_delete_instrument(self):
        self.assertFalse(
            self.charlie.has_perm("enhydris.change_instrument", self.instrument)
        )
