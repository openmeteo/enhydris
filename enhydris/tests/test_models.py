from datetime import date, datetime, timedelta, timezone
from io import StringIO
import shutil
import tempfile
import textwrap
from unittest.mock import Mock, MagicMock, mock_open, patch

from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.db import IntegrityError
from django.test import TestCase
from django.test.utils import override_settings

from model_mommy import mommy

from enhydris import models


class PersonTestCase(TestCase):
    def test_create(self):
        person = models.Person(last_name="Brown", first_name="Alice", initials="A.")
        person.save()
        self.assertEqual(models.Person.objects.first().last_name, "Brown")

    def test_update(self):
        mommy.make(models.Person)
        person = models.Person.objects.first()
        person.first_name = "Bob"
        person.save()
        self.assertEqual(models.Person.objects.first().first_name, "Bob")

    def test_delete(self):
        mommy.make(models.Person)
        person = models.Person.objects.first()
        person.delete()
        self.assertEqual(models.Person.objects.count(), 0)

    def test_str(self):
        person = mommy.make(
            models.Person, last_name="Brown", first_name="Alice", initials="A."
        )
        self.assertEqual(str(person), "Brown A.")

    def test_ordering_string(self):
        mommy.make(models.Person, last_name="Brown", first_name="Alice", initials="A.")
        person = models.Person.objects.first()
        self.assertEqual(person.ordering_string, "Brown Alice")


class OrganizationTestCase(TestCase):
    def test_create(self):
        organization = models.Organization(name="Crooks Intl", acronym="Crooks")
        organization.save()
        self.assertEqual(models.Organization.objects.first().name, "Crooks Intl")

    def test_update(self):
        mommy.make(models.Organization)
        organization = models.Organization.objects.first()
        organization.acronym = "Crooks"
        organization.save()
        self.assertEqual(models.Organization.objects.first().acronym, "Crooks")

    def test_delete(self):
        mommy.make(models.Organization)
        organization = models.Organization.objects.first()
        organization.delete()
        self.assertEqual(models.Organization.objects.count(), 0)

    def test_str(self):
        org = mommy.make(models.Organization, name="Crooks Intl", acronym="Crooks")
        self.assertEqual(str(org), "Crooks")

    def test_ordering_string(self):
        mommy.make(models.Organization, name="Crooks Intl", acronym="Crooks")
        organization = models.Organization.objects.first()
        self.assertEqual(organization.ordering_string, "Crooks Intl")


class PoliticalDivisionTestCase(TestCase):
    # We don't assume we start with a clean table, because a data migration creates
    # countries.

    def test_create(self):
        poldiv = models.PoliticalDivision(name="Attica")
        poldiv.save()
        self.assertEqual(
            models.PoliticalDivision.objects.get(pk=poldiv.pk).name, "Attica"
        )

    def test_update(self):
        mommy.make(models.PoliticalDivision)
        poldiv = models.PoliticalDivision.objects.first()
        poldiv.name = "Attica"
        poldiv.save()
        self.assertEqual(
            models.PoliticalDivision.objects.get(pk=poldiv.pk).name, "Attica"
        )

    def test_delete(self):
        mommy.make(models.PoliticalDivision)
        n = models.PoliticalDivision.objects.count()
        poldiv = models.PoliticalDivision.objects.first()
        poldiv.delete()
        self.assertEqual(models.PoliticalDivision.objects.count(), n - 1)

    def test_str(self):
        poldiv = mommy.make(models.PoliticalDivision, name="Attica")
        self.assertEqual(str(poldiv), "Attica")

    def test_str_nested(self):
        greece = mommy.make(models.PoliticalDivision, name="Greece")
        attica = mommy.make(models.PoliticalDivision, name="Attica", parent=greece)
        self.assertEqual(str(attica), "Attica, Greece")


class WaterDivisionTestCase(TestCase):
    def test_create(self):
        watdiv = models.WaterDivision(name="Attica")
        watdiv.save()
        self.assertEqual(models.WaterDivision.objects.first().name, "Attica")

    def test_update(self):
        mommy.make(models.WaterDivision)
        watdiv = models.WaterDivision.objects.first()
        watdiv.name = "Attica"
        watdiv.save()
        self.assertEqual(models.WaterDivision.objects.first().name, "Attica")

    def test_delete(self):
        mommy.make(models.WaterDivision)
        watdiv = models.WaterDivision.objects.first()
        watdiv.delete()
        self.assertEqual(models.WaterDivision.objects.count(), 0)

    def test_str(self):
        watdiv = mommy.make(models.WaterDivision, name="Attica")
        self.assertEqual(str(watdiv), "Attica")


class WaterBasinTestCase(TestCase):
    def test_create(self):
        water_basin = models.WaterBasin(name="Baranduin")
        water_basin.save()
        self.assertEqual(models.WaterBasin.objects.first().name, "Baranduin")

    def test_update(self):
        mommy.make(models.WaterBasin)
        water_basin = models.WaterBasin.objects.first()
        water_basin.name = "Baranduin"
        water_basin.save()
        self.assertEqual(models.WaterBasin.objects.first().name, "Baranduin")

    def test_delete(self):
        mommy.make(models.WaterBasin)
        water_basin = models.WaterBasin.objects.first()
        water_basin.delete()
        self.assertEqual(models.WaterBasin.objects.count(), 0)

    def test_str(self):
        water_basin = mommy.make(models.WaterBasin, name="Baranduin")
        self.assertEqual(str(water_basin), "Baranduin")


class GentityAltCodeTypeTestCase(TestCase):
    """Test lookups.

    We test GentityAltCodeType as an example of Lookup. We don't test
    GentityGenericDataType, EventType, StationType, InstrumentType, Variable and
    IntervalType, because they are trivial Lookup descendants.
    """

    def test_create(self):
        gact = models.GentityAltCodeType(descr="Old")
        gact.save()
        self.assertEqual(models.GentityAltCodeType.objects.first().descr, "Old")

    def test_update(self):
        mommy.make(models.GentityAltCodeType)
        gact = models.GentityAltCodeType.objects.first()
        gact.descr = "Old"
        gact.save()
        self.assertEqual(models.GentityAltCodeType.objects.first().descr, "Old")

    def test_delete(self):
        mommy.make(models.GentityAltCodeType)
        gact = models.GentityAltCodeType.objects.first()
        gact.delete()
        self.assertEqual(models.GentityAltCodeType.objects.count(), 0)

    def test_str(self):
        gact = mommy.make(models.GentityAltCodeType, descr="Old")
        self.assertEqual(str(gact), "Old")


class GentityAltCodeTestCase(TestCase):
    def test_create(self):
        station = mommy.make(models.Station)
        gact = mommy.make(models.GentityAltCodeType)
        gac = models.GentityAltCode(gentity=station, value="18765", type=gact)
        gac.save()
        self.assertEqual(models.GentityAltCode.objects.first().value, "18765")

    def test_update(self):
        mommy.make(models.GentityAltCode)
        gac = models.GentityAltCode.objects.first()
        gac.value = "18765"
        gac.save()
        self.assertEqual(models.GentityAltCode.objects.first().value, "18765")

    def test_delete(self):
        mommy.make(models.GentityAltCode)
        gac = models.GentityAltCode.objects.first()
        gac.delete()
        self.assertEqual(models.GentityAltCode.objects.count(), 0)

    def test_str(self):
        gac = mommy.make(models.GentityAltCode, value="18765", type__descr="Old")
        self.assertEqual(str(gac), "Old 18765")

    def test_related_station(self):
        station = mommy.make(models.Station)
        gac = mommy.make(models.GentityAltCode, gentity=station)
        self.assertEqual(gac.related_station, station)


class GentityGenericDataTestCase(TestCase):
    def test_create(self):
        station = mommy.make(models.Station)
        ggdt = mommy.make(models.GentityGenericDataType)
        ggd = models.GentityGenericData(
            gentity=station, data_type=ggdt, descr="North view"
        )
        ggd.save()
        self.assertEqual(models.GentityGenericData.objects.first().descr, "North view")

    def test_update(self):
        mommy.make(models.GentityGenericData)
        ggd = models.GentityGenericData.objects.first()
        ggd.descr = "North view"
        ggd.save()
        self.assertEqual(models.GentityGenericData.objects.first().descr, "North view")

    def test_delete(self):
        mommy.make(models.GentityGenericData)
        ggd = models.GentityGenericData.objects.first()
        ggd.delete()
        self.assertEqual(models.GentityGenericData.objects.count(), 0)

    def test_str(self):
        ggd = mommy.make(models.GentityGenericData, descr="North view")
        self.assertEqual(str(ggd), "North view")

    def test_related_station(self):
        station = mommy.make(models.Station)
        ggd = mommy.make(models.GentityGenericData, gentity=station)
        self.assertEqual(ggd.related_station, station)

    def test_related_station_is_empty_when_gentity_is_not_station(self):
        water_basin = mommy.make(models.WaterBasin)
        ggd = mommy.make(models.GentityGenericData, gentity=water_basin)
        self.assertIsNone(ggd.related_station)


class FileTypeTestCase(TestCase):
    # We don't test functionality inherited from Lookup, as this is tested in
    # GentityAltCodeTypeTestCase.

    def test_str(self):
        file_type = mommy.make(models.FileType, mime_type="image/png")
        self.assertEqual(str(file_type), "image/png")


class GentityFileTestCase(TestCase):
    def test_create(self):
        station = mommy.make(models.Station)
        file_type = mommy.make(models.FileType)
        gentity_file = models.GentityFile(
            gentity=station, file_type=file_type, descr="North view"
        )
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
        water_basin = mommy.make(models.WaterBasin)
        gentity_file = mommy.make(models.GentityFile, gentity=water_basin)
        self.assertIsNone(gentity_file.related_station)


class GentityEventTestCase(TestCase):
    def test_create(self):
        station = mommy.make(models.Station)
        type = mommy.make(models.EventType)
        gentity_event = models.GentityEvent(
            gentity=station,
            type=type,
            date=datetime.now(),
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
        water_basin = mommy.make(models.WaterBasin)
        gentity_event = mommy.make(models.GentityEvent, gentity=water_basin)
        self.assertIsNone(gentity_event.related_station)


class StationTestCase(TestCase):
    def test_create(self):
        person = mommy.make(models.Person)
        station = models.Station(
            owner=person,
            copyright_holder="Bilbo Baggins",
            copyright_years="2018",
            name="Hobbiton",
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
            point=Point(x=21.06071, y=39.09518, srid=4326),
            srid=2100,
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
            point=Point(x=21.06071, y=39.09518, srid=4326),
            srid=None,
        )
        self.station = models.Station.objects.get(name="Komboti")

    def test_original_abscissa(self):
        self.assertAlmostEqual(self.station.original_abscissa(), 21.06071)

    def test_original_ordinate(self):
        self.assertAlmostEqual(self.station.original_ordinate(), 39.09518)


class OverseerTestCase(TestCase):
    def test_create(self):
        person = mommy.make(models.Person)
        station = mommy.make(models.Station)
        overseer = models.Overseer(person=person, station=station)
        overseer.save()
        self.assertEqual(models.Overseer.objects.first().station, station)

    def test_update(self):
        mommy.make(models.Overseer)
        overseer = models.Overseer.objects.first()
        overseer.start_date = "2018-11-14"
        overseer.save()
        self.assertEqual(models.Overseer.objects.first().start_date, date(2018, 11, 14))

    def test_delete(self):
        mommy.make(models.Overseer)
        overseer = models.Overseer.objects.first()
        overseer.delete()
        self.assertEqual(models.Overseer.objects.count(), 0)

    def test_str(self):
        overseer = mommy.make(
            models.Overseer, person__last_name="Baggins", person__initials="F."
        )
        self.assertEqual(str(overseer), "Baggins F.")


class InstrumentTestCase(TestCase):
    def test_create(self):
        type = mommy.make(models.InstrumentType)
        station = mommy.make(models.Station)
        instrument = models.Instrument(type=type, station=station, name="Thermometer")
        instrument.save()
        self.assertEqual(models.Instrument.objects.first().name, "Thermometer")

    def test_update(self):
        mommy.make(models.Instrument)
        instrument = models.Instrument.objects.first()
        instrument.name = "Thermometer"
        instrument.save()
        self.assertEqual(models.Instrument.objects.first().name, "Thermometer")

    def test_delete(self):
        mommy.make(models.Instrument)
        instrument = models.Instrument.objects.first()
        instrument.delete()
        self.assertEqual(models.Instrument.objects.count(), 0)

    def test_str(self):
        instrument = mommy.make(models.Instrument, name="Thermometer")
        self.assertEqual(str(instrument), "Thermometer")


class UnitOfMeasurementTestCase(TestCase):
    # We don't test functionality inherited from Lookup, as this is tested in
    # GentityAltCodeTypeTestCase.

    def test_str(self):
        unit = mommy.make(models.UnitOfMeasurement, symbol="mm")
        self.assertEqual(str(unit), "mm")

    def test_str_when_symbol_is_empty(self):
        unit = mommy.make(models.UnitOfMeasurement, symbol="")
        self.assertEqual(str(unit), str(unit.id))


class TimeZoneTestCase(TestCase):
    def test_create(self):
        time_zone = models.TimeZone(code="EET", utc_offset=120)
        time_zone.save()
        self.assertEqual(models.TimeZone.objects.first().code, "EET")

    def test_update(self):
        mommy.make(models.TimeZone)
        time_zone = models.TimeZone.objects.first()
        time_zone.code = "EET"
        time_zone.save()
        self.assertEqual(models.TimeZone.objects.first().code, "EET")

    def test_delete(self):
        mommy.make(models.TimeZone)
        time_zone = models.TimeZone.objects.first()
        time_zone.delete()
        self.assertEqual(models.TimeZone.objects.count(), 0)

    def test_str(self):
        time_zone = mommy.make(models.TimeZone, code="EET", utc_offset=120)
        self.assertEqual(str(time_zone), "EET (UTC+0200)")

    def test_as_tzinfo(self):
        time_zone = mommy.make(models.TimeZone, code="EET", utc_offset=120)
        self.assertEqual(time_zone.as_tzinfo, timezone(timedelta(hours=2), "EET"))


class TimeStepTestCase(TestCase):
    # We don't test functionality inherited from Lookup, as this is tested in
    # GentityAltCodeTypeTestCase.

    def test_str_with_minutes(self):
        time_step = mommy.make(
            models.TimeStep, length_minutes=1563, length_months=0, descr="gazilliony"
        )
        self.assertEqual(
            str(time_step), "gazilliony - 1 day(s), 2 hour(s), 3 minute(s)"
        )

    def test_str_with_months(self):
        time_step = mommy.make(
            models.TimeStep,
            length_minutes=0,
            length_months=28,
            descr="twentyeightmonthly",
        )
        self.assertEqual(str(time_step), "twentyeightmonthly - 2 year(s), 4 month(s)")

    def test_save_with_both_minutes_and_months(self):
        time_step = models.TimeStep(length_minutes=5, length_months=2)
        with self.assertRaises(IntegrityError):
            time_step.save()

    def test_save_with_neither_minutes_nor_months(self):
        time_step = models.TimeStep(length_minutes=0, length_months=0)
        with self.assertRaises(IntegrityError):
            time_step.save()

    def test_save_with_minutes(self):
        time_step = models.TimeStep(length_minutes=10, length_months=0)
        time_step.save()

    def test_save_with_months(self):
        time_step = models.TimeStep(length_minutes=0, length_months=3)
        time_step.save()


class TimeseriesTestCase(TestCase):
    def test_create(self):
        station = mommy.make(models.Station)
        variable = mommy.make(models.Variable)
        unit = mommy.make(models.UnitOfMeasurement)
        time_zone = mommy.make(models.TimeZone)
        timeseries = models.Timeseries(
            gentity=station,
            name="Temperature",
            variable=variable,
            unit_of_measurement=unit,
            time_zone=time_zone,
        )
        timeseries.save()
        self.assertEqual(models.Timeseries.objects.first().name, "Temperature")

    def test_update(self):
        mommy.make(models.Timeseries)
        timeseries = models.Timeseries.objects.first()
        timeseries.name = "Temperature"
        timeseries.save()
        self.assertEqual(models.Timeseries.objects.first().name, "Temperature")

    def test_delete(self):
        mommy.make(models.Timeseries)
        timeseries = models.Timeseries.objects.first()
        timeseries.delete()
        self.assertEqual(models.Timeseries.objects.count(), 0)

    def test_str(self):
        timeseries = mommy.make(models.Timeseries, name="Temperature")
        self.assertEqual(str(timeseries), "Temperature")

    def test_related_station(self):
        station = mommy.make(models.Station)
        timeseries = mommy.make(models.Timeseries, gentity=station)
        self.assertEqual(timeseries.related_station, station)


class TimeseriesDatesTestCase(TestCase):
    def setUp(self):
        self.timeseries = mommy.make(models.Timeseries, time_zone__utc_offset=120)

        # We can't have mommy save the following two, because it calls
        # Timeseries.save(), and .save() would overwrite them.
        self.timeseries.start_date_utc = datetime(
            2018, 11, 15, 16, 0, tzinfo=timezone.utc
        )
        self.timeseries.end_date_utc = datetime(
            2018, 11, 17, 23, 0, tzinfo=timezone.utc
        )

    def test_start_date(self):
        self.assertEqual(
            self.timeseries.start_date,
            datetime(2018, 11, 15, 18, 0, tzinfo=self.timeseries.time_zone.as_tzinfo),
        )

    def test_end_date(self):
        self.assertEqual(
            self.timeseries.end_date,
            datetime(2018, 11, 18, 1, 0, tzinfo=self.timeseries.time_zone.as_tzinfo),
        )


class TimeseriesSaveDatesTestCase(TestCase):
    def setUp(self):
        self.timeseries = mommy.make(models.Timeseries, time_zone__utc_offset=120)

        # Mock self.timeseries.datafile
        self.timeseries.datafile = Mock(size=50)

        # Mock open so that it appears to provide some data
        m = mock_open(read_data="2017-11-23 17:23,1,\n" "2018-11-25 01:00,2,\n")
        patch_open = patch("enhydris.models.open", m)

        # Mock ropen so that it appears to provide the same data in reverse
        m = mock_open(read_data="2018-11-25 01:00,2,\n" "2017-11-23 17:23,1,\n")
        patch_ropen = patch("enhydris.models.ropen", m)

        # Mock django's Model.save(), otherwise when it runs under this mock mess
        # it causes an error
        patch_save = patch("enhydris.models.models.Model.save")

        # Execute Timeseries.save(); then we will verify dates were overwritten
        with patch_open, patch_ropen, patch_save:
            self.timeseries.save()

    def test_start_date(self):
        self.assertEqual(
            self.timeseries.start_date_utc,
            datetime(2017, 11, 23, 15, 23, tzinfo=timezone.utc),
        )

    def test_end_date(self):
        self.assertEqual(
            self.timeseries.end_date_utc,
            datetime(2018, 11, 24, 23, 0, tzinfo=timezone.utc),
        )


class TimeseriesGetDataExtraPropertiesTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        station = mommy.make(
            models.Station,
            name="Celduin",
            srid=4326,
            point=Point(x=21.06071, y=39.09518, srid=4326),
            altitude=219,
            asrid=None,
        )
        cls.timeseries = mommy.make(
            models.Timeseries,
            name="Daily temperature",
            gentity=station,
            time_step__length_minutes=60,
            time_step__length_months=0,
            timestamp_offset_minutes=0,
            timestamp_offset_months=0,
            timestamp_rounding_minutes=0,
            timestamp_rounding_months=0,
            interval_type__value="INSTANTANEOUS",
            unit_of_measurement__symbol="mm",
            time_zone__code="IST",
            time_zone__utc_offset=330,
            variable__descr="Temperature",
            precision=1,
            remarks="This timeseries rocks",
        )
        cls.data = cls.timeseries.get_data()

    def test_abscissa(self):
        self.assertAlmostEqual(self.data.location["abscissa"], 21.06071)

    def test_ordinate(self):
        self.assertAlmostEqual(self.data.location["ordinate"], 39.09518)

    def test_srid(self):
        self.assertAlmostEqual(self.data.location["srid"], 4326)

    def test_altitude(self):
        self.assertAlmostEqual(self.data.location["altitude"], 219)

    def test_asrid(self):
        self.assertIsNone(self.data.location["asrid"])

    def test_time_step(self):
        self.assertEqual(self.data.time_step, "60,0")

    def test_timestamp_rounding(self):
        self.assertEqual(self.data.timestamp_rounding, "0,0")

    def test_interval_type(self):
        self.assertEqual(self.data.interval_type, "instantaneous")

    def test_unit(self):
        self.assertEqual(self.data.unit, "mm")

    def test_title(self):
        self.assertEqual(self.data.title, "Daily temperature")

    def test_timezone(self):
        self.assertEqual(self.data.timezone, "IST (UTC+0530)")

    def test_negative_timezone(self):
        self.timeseries.time_zone.code = "NST"
        self.timeseries.time_zone.utc_offset = -210
        data = self.timeseries.get_data()
        self.assertEqual(data.timezone, "NST (UTC-0330)")

    def test_variable(self):
        self.assertEqual(self.data.variable, "Temperature")

    def test_precision(self):
        self.assertEqual(self.data.precision, 1)

    def test_comment(self):
        self.assertEqual(self.data.comment, "Celduin\n\nThis timeseries rocks")

    def test_location_is_none(self):
        self.timeseries.gentity.gpoint.point = None
        data = self.timeseries.get_data()
        self.assertIsNone(data.location)


class TimeseriesSetDataTestCase(TestCase):
    def setUp(self):
        self.timeseries = mommy.make(
            models.Timeseries, id=42, time_zone__utc_offset=0, precision=2
        )

        # Mock self.timeseries.datafile
        self.timeseries.datafile = MagicMock(
            size=50, path="/some/path", **{"__bool__.return_value": False}
        )

        # Mock open() so that it doesn't actually save to a file
        self.mock_open = mock_open()
        patch1 = patch("enhydris.models.open", self.mock_open)

        # Mock Timeseries.save(), otherwise there's chaos
        patch2 = patch("enhydris.models.Timeseries.save")

        with patch1, patch2:
            self.returned_length = self.timeseries.set_data(
                StringIO("2017-11-23 17:23,1,\n" "2018-11-25 01:00,2,\n")
            )

    def test_returned_length(self):
        self.assertEqual(self.returned_length, 2)

    def test_filepath(self):
        self.mock_open.assert_called_once_with("/some/path", "w")

    def test_filename(self):
        self.assertEqual(self.timeseries.datafile.name, "0000000042")

    def test_wrote_data(self):
        # Instead of six decimal digits we should probably have gotten two digits
        # because we specified precision=2. See Enhydris ticket #90.
        self.assertEqual(
            self.mock_open().write.call_args_list,
            [
                (("2017-11-23 17:23,1.000000,\r\n",),),
                (("2018-11-25 01:00,2.000000,\r\n",),),
            ],
        )


class TimeseriesUpdateDataTestCase(TestCase):
    def setUp(self):
        self.timeseries = mommy.make(
            models.Timeseries, id=42, time_zone__utc_offset=0, precision=2
        )

        # Mock self.timeseries.datafile
        self.timeseries.datafile = MagicMock(size=50, path="/some/path")

        # Mock open() so that it doesn't actually save to a file
        self.mock_open = mock_open()
        patch1 = patch("enhydris.models.open", self.mock_open)

        # Mock ropen() so that it supposedly returns some data
        patch2 = patch(
            "enhydris.models.ropen", mock_open(read_data="2016-01-01 00:00,42,\n")
        )

        # Mock Timeseries.save(), otherwise there's chaos
        patch3 = patch("enhydris.models.Timeseries.save")

        with patch1, patch2, patch3:
            self.returned_length = self.timeseries.append_data(
                StringIO("2017-11-23 17:23,1,\n" "2018-11-25 01:00,2,\n")
            )

    def test_returned_length(self):
        self.assertEqual(self.returned_length, 2)

    def test_called_open(self):
        self.mock_open.assert_called_once_with("/some/path", "a")

    def test_wrote_data(self):
        # Instead of six decimal digits we should probably have gotten two digits
        # because we specified precision=2. See Enhydris ticket #90.
        self.assertEqual(
            self.mock_open().write.call_args_list,
            [
                (("2017-11-23 17:23,1.000000,\r\n",),),
                (("2018-11-25 01:00,2.000000,\r\n",),),
            ],
        )


class TimeseriesUpdateErrorTestCase(TestCase):
    def test_does_not_update_if_data_to_append_are_not_later(self):
        self.timeseries = mommy.make(
            models.Timeseries, id=42, time_zone__utc_offset=0, precision=2
        )

        # Mock self.timeseries.datafile
        self.timeseries.datafile = MagicMock(size=50, path="/some/path")

        # Mock open() so that it doesn't actually save to a file
        self.mock_open = mock_open()
        patch1 = patch("enhydris.models.open", self.mock_open)

        # Mock ropen() so that it supposedly returns some data
        patch2 = patch(
            "enhydris.models.ropen", mock_open(read_data="2018-01-01 00:00,42,\n")
        )

        # Mock Timeseries.save(), otherwise there's chaos
        patch3 = patch("enhydris.models.Timeseries.save")

        with patch1, patch2, patch3:
            with self.assertRaises(IntegrityError):
                self.timeseries.append_data(
                    StringIO("2017-11-23 17:23,1,\n" "2018-11-25 01:00,2,\n")
                )


class TimeseriesGetFirstOrLastLineTestCase(TestCase):
    def test_get_first_line(self):
        timeseries = mommy.make(
            models.Timeseries, id=42, time_zone__utc_offset=0, precision=2
        )

        # Mock self.timeseries.datafile
        timeseries.datafile = MagicMock(size=50)

        # Mock open() so that it supposedly returns some data
        m = mock_open(read_data="2017-11-23 17:23,1,\n" "2018-11-25 01:00,2,\n")
        patch1 = patch("enhydris.models.open", m)

        # Mock Timeseries.save(), otherwise there's chaos
        patch2 = patch("enhydris.models.Timeseries.save")

        with patch1, patch2:
            first_line = timeseries.get_first_line()

        self.assertEqual(first_line, "2017-11-23 17:23,1,\n")

    def test_get_last_line(self):
        timeseries = mommy.make(
            models.Timeseries, id=42, time_zone__utc_offset=0, precision=2
        )

        # Mock self.timeseries.datafile
        timeseries.datafile = MagicMock(size=50)

        # Mock ropen() so that it supposedly returns some data
        m = mock_open(read_data="2018-11-25 01:00,2,\n" "2017-11-23 17:23,1,\n")
        patch1 = patch("enhydris.models.ropen", m)

        # Mock Timeseries.save(), otherwise there's chaos
        patch2 = patch("enhydris.models.Timeseries.save")

        with patch1, patch2:
            first_line = timeseries.get_last_line()

        self.assertEqual(first_line, "2018-11-25 01:00,2,\n")


class TimeseriesSaveWhenTimeStepIsNullTestCase(TestCase):
    def setUp(self):
        station = mommy.make(models.Station)
        variable = mommy.make(models.Variable)
        unit = mommy.make(models.UnitOfMeasurement)
        time_zone = mommy.make(models.TimeZone)
        self.timeseries = models.Timeseries(
            gentity=station,
            name="Temperature",
            variable=variable,
            unit_of_measurement=unit,
            time_zone=time_zone,
        )

    def test_rounding_minutes_must_be_null(self):
        self.timeseries.time_step = None
        self.timeseries.timestamp_rounding_minutes = 0
        with self.assertRaises(IntegrityError):
            self.timeseries.save()

    def test_rounding_months_must_be_null(self):
        self.timeseries.time_step = None
        self.timeseries.timestamp_rounding_months = 0
        with self.assertRaises(IntegrityError):
            self.timeseries.save()

    def test_offset_minutes_must_be_null(self):
        self.timeseries.time_step = None
        self.timeseries.timestamp_offset_minutes = 0
        with self.assertRaises(IntegrityError):
            self.timeseries.save()

    def test_offset_months_must_be_null(self):
        self.timeseries.time_step = None
        self.timeseries.timestamp_offset_months = 0
        with self.assertRaises(IntegrityError):
            self.timeseries.save()

    def test_everything_works_when_all_are_null(self):
        self.timeseries.save()  # No exception raised


class TimeseriesSaveWhenTimeStepIsNotNullTestCase(TestCase):
    def setUp(self):
        station = mommy.make(models.Station)
        variable = mommy.make(models.Variable)
        unit = mommy.make(models.UnitOfMeasurement)
        time_zone = mommy.make(models.TimeZone)
        time_step = mommy.make(models.TimeStep, length_minutes=10, length_months=0)
        self.timeseries = models.Timeseries(
            gentity=station,
            name="Temperature",
            variable=variable,
            unit_of_measurement=unit,
            time_zone=time_zone,
            time_step=time_step,
            timestamp_offset_minutes=0,
            timestamp_offset_months=0,
        )

    def test_offset_must_be_not_null_when_time_step_is_not_null(self):
        self.timeseries.timestamp_offset_minutes = None
        self.timeseries.timestamp_offset_months = None
        with self.assertRaises(IntegrityError):
            self.timeseries.save()

    def test_rounding_minutes_must_be_null_if_months_is_null(self):
        self.timeseries.timestamp_rounding_minutes = 0
        self.timeseries.timestamp_rounding_months = None
        with self.assertRaises(IntegrityError):
            self.timeseries.save()

    def test_rounding_months_must_be_null_if_minutes_is_null(self):
        self.timeseries.timestamp_rounding_minutes = None
        self.timeseries.timestamp_rounding_months = 0
        with self.assertRaises(IntegrityError):
            self.timeseries.save()

    def test_rounding_minutes_and_months_both_null_is_ok(self):
        self.timeseries.timestamp_rounding_minutes = None
        self.timeseries.timestamp_rounding_months = None
        self.timeseries.save()  # No exception raised

    def test_rounding_minutes_and_months_both_not_null_is_ok(self):
        self.timeseries.timestamp_rounding_minutes = 0
        self.timeseries.timestamp_rounding_months = 0
        self.timeseries.save()  # No exception raised


class RulesTestCase(TestCase):
    def setUp(self):
        self.alice = mommy.make(User, username="alice")
        self.bob = mommy.make(User, username="bob")
        self.charlie = mommy.make(User, username="charlie")

        self.station = mommy.make(
            models.Station, creator=self.alice, maintainers=[self.bob]
        )
        self.instrument = mommy.make(models.Instrument, station=self.station)
        self.timeseries = mommy.make(models.Timeseries, gentity=self.station)

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
