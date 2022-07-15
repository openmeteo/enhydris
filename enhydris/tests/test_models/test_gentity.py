import datetime as dt

from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.contrib.sites.models import Site
from django.test import TestCase, override_settings

from model_mommy import mommy

from enhydris import models
from enhydris.tests import ClearCacheMixin


class GentityFileTestCase(TestCase):
    def test_create(self):
        station = mommy.make(models.Station)
        gentity_file = models.GentityFile(gentity=station, descr="North view")
        gentity_file.save()
        self.assertEqual(models.GentityFile.objects.first().descr, "North view")

    def test_update(self):
        mommy.make(models.GentityFile)
        gentity_file = models.GentityFile.objects.first()
        gentity_file.descr = "North view"
        gentity_file.save()
        self.assertEqual(models.GentityFile.objects.first().descr, "North view")

    def test_delete(self):
        mommy.make(models.GentityFile)
        gentity_file = models.GentityFile.objects.first()
        gentity_file.delete()
        self.assertEqual(models.GentityFile.objects.count(), 0)

    def test_str(self):
        gentity_file = mommy.make(models.GentityFile, descr="North view")
        self.assertEqual(str(gentity_file), "North view")

    def test_related_station(self):
        station = mommy.make(models.Station)
        gentity_file = mommy.make(models.GentityFile, gentity=station)
        self.assertEqual(gentity_file.related_station, station)

    def test_related_station_is_empty_when_gentity_is_not_station(self):
        garea = mommy.make(models.Garea)
        gentity_file = mommy.make(models.GentityFile, gentity=garea)
        self.assertIsNone(gentity_file.related_station)


class GentityImageTestCase(TestCase):
    def test_str_desc(self):
        image = mommy.make(models.GentityImage, descr="hello")
        self.assertEqual(str(image), "hello")

    def test_str_date(self):
        image = mommy.make(models.GentityImage, descr="", date=dt.datetime(2021, 1, 22))
        self.assertEqual(str(image), "2021-01-22")

    def test_str_id(self):
        image = mommy.make(models.GentityImage, descr="", date=None, id=85)
        self.assertEqual(str(image), "85")


class GentityEventTestCase(TestCase):
    def test_create(self):
        station = mommy.make(models.Station)
        type = mommy.make(models.EventType)
        gentity_event = models.GentityEvent(
            gentity=station,
            type=type,
            date=dt.datetime.now(),
            user="Alice",
            report="Station exploded",
        )
        gentity_event.save()
        self.assertEqual(models.GentityEvent.objects.first().report, "Station exploded")

    def test_update(self):
        mommy.make(models.GentityEvent)
        gentity_event = models.GentityEvent.objects.first()
        gentity_event.report = "Station exploded"
        gentity_event.save()
        self.assertEqual(models.GentityEvent.objects.first().report, "Station exploded")

    def test_delete(self):
        mommy.make(models.GentityEvent)
        gentity_event = models.GentityEvent.objects.first()
        gentity_event.delete()
        self.assertEqual(models.GentityEvent.objects.count(), 0)

    def test_str(self):
        gentity_event = mommy.make(
            models.GentityEvent, date="2018-11-14", type__descr="Explosion"
        )
        self.assertEqual(str(gentity_event), "2018-11-14 Explosion")

    def test_related_station(self):
        station = mommy.make(models.Station)
        gentity_event = mommy.make(models.GentityEvent, gentity=station)
        self.assertEqual(gentity_event.related_station, station)

    def test_related_station_is_empty_when_gentity_is_not_station(self):
        garea = mommy.make(models.Garea)
        gentity_event = mommy.make(models.GentityEvent, gentity=garea)
        self.assertIsNone(gentity_event.related_station)


class GareaTestCase(TestCase):
    def test_create(self):
        category = mommy.make(models.GareaCategory)
        garea = models.Garea(
            name="Esgalduin",
            category=category,
            geom=MultiPolygon(Polygon(((30, 20), (45, 40), (10, 40), (30, 20)))),
        )
        garea.save()
        self.assertEqual(models.Garea.objects.first().name, "Esgalduin")

    def test_update(self):
        mommy.make(models.Garea)
        garea = models.Garea.objects.first()
        garea.name = "Esgalduin"
        garea.save()
        self.assertEqual(models.Garea.objects.first().name, "Esgalduin")

    def test_delete(self):
        mommy.make(models.Garea)
        garea = models.Garea.objects.first()
        garea.delete()
        self.assertEqual(models.Garea.objects.count(), 0)

    def test_str(self):
        garea = mommy.make(models.Garea, name="Esgalduin")
        self.assertEqual(str(garea), "Esgalduin")


class StationTestCase(TestCase):
    def test_create(self):
        person = mommy.make(models.Person)
        station = models.Station(
            owner=person,
            name="Hobbiton",
            geom=Point(x=21.06071, y=39.09518, srid=4326),
        )
        station.save()
        self.assertEqual(models.Station.objects.first().name, "Hobbiton")

    def test_update(self):
        mommy.make(models.Station)
        station = models.Station.objects.first()
        station.name = "Hobbiton"
        station.save()
        self.assertEqual(models.Station.objects.first().name, "Hobbiton")

    def test_delete(self):
        mommy.make(models.Station)
        station = models.Station.objects.first()
        station.delete()
        self.assertEqual(models.Station.objects.count(), 0)

    def test_str(self):
        station = mommy.make(models.Station, name="Hobbiton")
        self.assertEqual(str(station), "Hobbiton")


class StationOriginalCoordinatesTestCase(TestCase):
    def setUp(self):
        mommy.make(
            models.Station,
            name="Komboti",
            geom=Point(x=21.06071, y=39.09518, srid=4326),
            original_srid=2100,
        )
        self.station = models.Station.objects.get(name="Komboti")

    def test_original_abscissa(self):
        self.assertAlmostEqual(self.station.original_abscissa(), 245648.96, places=1)

    def test_original_ordinate(self):
        self.assertAlmostEqual(self.station.original_ordinate(), 4331165.20, places=1)


class StationOriginalCoordinatesWithNullSridTestCase(TestCase):
    def setUp(self):
        mommy.make(
            models.Station,
            name="Komboti",
            geom=Point(x=21.06071, y=39.09518, srid=4326),
            original_srid=None,
        )
        self.station = models.Station.objects.get(name="Komboti")

    def test_original_abscissa(self):
        self.assertAlmostEqual(self.station.original_abscissa(), 21.06071)

    def test_original_ordinate(self):
        self.assertAlmostEqual(self.station.original_ordinate(), 39.09518)


class StationLastUpdateTestCase(ClearCacheMixin, TestCase):
    def setUp(self):
        self.station = mommy.make(models.Station)
        self.time_zone = mommy.make(models.TimeZone, code="EET", utc_offset=120)
        self.timeseries_group = mommy.make(
            models.TimeseriesGroup,
            gentity=self.station,
            time_zone=self.time_zone,
            variable__descr="irrelevant",
            precision=2,
        )

    def _create_timeseries(
        self,
        ye=None,
        mo=None,
        da=None,
        ho=None,
        mi=None,
        type=models.Timeseries.INITIAL,
    ):
        if ye:
            end_date_utc = dt.datetime(ye, mo, da, ho, mi, tzinfo=dt.timezone.utc)
        else:
            end_date_utc = None
        timeseries = mommy.make(
            models.Timeseries, timeseries_group=self.timeseries_group, type=type
        )
        if end_date_utc:
            timeseries.timeseriesrecord_set.create(
                timestamp=end_date_utc, value=0, flags=""
            )

    def test_last_update_naive_when_all_timeseries_have_end_date(self):
        self._create_timeseries(2019, 7, 24, 11, 26, type=models.Timeseries.INITIAL)
        self._create_timeseries(2019, 7, 23, 5, 10, type=models.Timeseries.CHECKED)
        self.assertEqual(
            self.station.last_update_naive, dt.datetime(2019, 7, 24, 13, 26)
        )

    def test_last_update_naive_when_one_timeseries_has_no_data(self):
        self._create_timeseries(2019, 7, 24, 11, 26, type=models.Timeseries.INITIAL)
        self._create_timeseries(type=models.Timeseries.CHECKED)
        self.assertEqual(
            self.station.last_update_naive, dt.datetime(2019, 7, 24, 13, 26)
        )

    def test_last_update_naive_when_all_timeseries_has_no_data(self):
        self._create_timeseries(type=models.Timeseries.INITIAL)
        self._create_timeseries(type=models.Timeseries.CHECKED)
        self.assertIsNone(self.station.last_update_naive)

    def test_last_update_naive_when_no_timeseries(self):
        self.assertIsNone(self.station.last_update_naive)

    def test_last_update(self):
        self._create_timeseries(2019, 7, 24, 11, 26, type=models.Timeseries.INITIAL)
        tzinfo = dt.timezone(dt.timedelta(hours=2), "EET")
        self.assertEqual(
            self.station.last_update, dt.datetime(2019, 7, 24, 13, 26, tzinfo=tzinfo)
        )

    def test_last_update_cache_when_atleast_one_timeseries_has_end_date(self):
        # Since it's not possible to cache `None` values, ensure to create
        # at least one timeseries with an end date value.
        self._create_timeseries(2019, 7, 24, 11, 26, type=models.Timeseries.INITIAL)

        # Make sure to fetch the `end_date` value of the timeseries
        timeseries = models.Timeseries.objects.filter(
            timeseries_group__gentity_id=self.station.id
        )
        for t in timeseries:
            t.end_date

        with self.assertNumQueries(1):
            self.station.last_update

        station = models.Station.objects.get(id=self.station.id)
        with self.assertNumQueries(0):
            station.last_update

    def test_last_update_naive_cace_when_atleast_one_timeseries_has_end_date(self):
        # Since it's not possible to cache `None` values, ensure to create
        # at least one timeseries with an end date value.
        self._create_timeseries(2019, 7, 24, 11, 26, type=models.Timeseries.INITIAL)

        # Make sure to fetch the `end_date` value of the timeseries
        timeseries = models.Timeseries.objects.filter(
            timeseries_group__gentity_id=self.station.id
        )
        for t in timeseries:
            t.end_date

        with self.assertNumQueries(1):
            self.station.last_update_naive

        station = models.Station.objects.get(id=self.station.id)
        with self.assertNumQueries(0):
            station.last_update_naive


@override_settings(SITE_ID=4)
class StationSitesTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.site3 = mommy.make(Site, id=3, domain="hello.com", name="hello")
        cls.site4 = mommy.make(Site, id=4, domain="beautiful.com", name="beautiful")
        cls.site5 = mommy.make(Site, id=5, domain="world.com", name="world")

    def test_creating_station_puts_it_in_the_active_site(self):
        station = models.Station(
            owner=mommy.make(models.Organization),
            geom=Point(x=21.06071, y=39.09518, srid=4326),
        )
        station.save()
        self.assertEqual(
            list(models.Station.objects.first().sites.values("id")), [{"id": 4}]
        )

    def test_updating_station_does_not_touch_its_sites(self):
        # Create station and put it in site5
        station = models.Station(
            owner=mommy.make(models.Organization),
            geom=Point(x=21.06071, y=39.09518, srid=4326),
        )
        station.save()
        station.sites.set([Site.objects.get(id=5)])

        # Update station
        station.name = "hello"
        station.save()

        # Should still be in site5
        self.assertEqual(
            list(models.Station.objects.first().sites.values("id")), [{"id": 5}]
        )

    @override_settings(ENHYDRIS_SITES_FOR_NEW_STATIONS={5})
    def test_creating_station_puts_it_in_sites_for_new_stations(self):
        station = models.Station(
            owner=mommy.make(models.Organization),
            geom=Point(x=21.06071, y=39.09518, srid=4326),
        )
        station.save()
        self.assertEqual(
            list(models.Station.objects.first().sites.values("id")),
            [{"id": 4}, {"id": 5}],
        )
