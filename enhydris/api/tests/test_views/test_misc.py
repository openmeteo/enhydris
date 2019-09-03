from rest_framework.test import APITestCase

from model_mommy import mommy

from enhydris import models


class WaterDivisionTestCase(APITestCase):
    def setUp(self):
        self.water_division = mommy.make(models.WaterDivision)

    def test_get_water_division(self):
        r = self.client.get("/api/waterdivisions/{}/".format(self.water_division.id))
        self.assertEqual(r.status_code, 200)


class OrganizationTestCase(APITestCase):
    def setUp(self):
        self.organization = mommy.make(models.Organization)

    def test_get_organization(self):
        r = self.client.get("/api/organizations/{}/".format(self.organization.id))
        self.assertEqual(r.status_code, 200)


class PersonTestCase(APITestCase):
    def setUp(self):
        self.person = mommy.make(models.Person)

    def test_get_person(self):
        r = self.client.get("/api/persons/{}/".format(self.person.id))
        self.assertEqual(r.status_code, 200)


class TimeZoneTestCase(APITestCase):
    def setUp(self):
        self.time_zone = mommy.make(models.TimeZone)

    def test_get_time_zone(self):
        r = self.client.get("/api/timezones/{}/".format(self.time_zone.id))
        self.assertEqual(r.status_code, 200)


class PoliticalDivisionTestCase(APITestCase):
    def setUp(self):
        self.political_division = mommy.make(models.PoliticalDivision)

    def test_get_political_division(self):
        r = self.client.get(
            "/api/politicaldivisions/{}/".format(self.political_division.id)
        )
        self.assertEqual(r.status_code, 200)


class IntervalTypeTestCase(APITestCase):
    def setUp(self):
        self.interval_type = mommy.make(models.IntervalType)

    def test_get_interval_type(self):
        r = self.client.get("/api/intervaltypes/{}/".format(self.interval_type.id))
        self.assertEqual(r.status_code, 200)


class FileTypeTestCase(APITestCase):
    def setUp(self):
        self.file_type = mommy.make(models.FileType)

    def test_get_file_type(self):
        r = self.client.get("/api/filetypes/{}/".format(self.file_type.id))
        self.assertEqual(r.status_code, 200)


class EventTypeTestCase(APITestCase):
    def setUp(self):
        self.event_type = mommy.make(models.EventType)

    def test_get_event_type(self):
        r = self.client.get("/api/eventtypes/{}/".format(self.event_type.id))
        self.assertEqual(r.status_code, 200)


class InstrumentTypeTestCase(APITestCase):
    def setUp(self):
        self.instrument_type = mommy.make(models.InstrumentType)

    def test_get_instrument_type(self):
        r = self.client.get("/api/instrumenttypes/{}/".format(self.instrument_type.id))
        self.assertEqual(r.status_code, 200)


class WaterBasinTestCase(APITestCase):
    def setUp(self):
        self.water_basin = mommy.make(models.WaterBasin)

    def test_get_water_basin(self):
        r = self.client.get("/api/basins/{}/".format(self.water_basin.id))
        self.assertEqual(r.status_code, 200)


class TimeStepTestCase(APITestCase):
    def setUp(self):
        self.time_step = mommy.make(models.TimeStep, length_minutes=10, length_months=0)

    def test_get_time_step(self):
        r = self.client.get("/api/timesteps/{}/".format(self.time_step.id))
        self.assertEqual(r.status_code, 200)


class VariableTestCase(APITestCase):
    def setUp(self):
        self.variable = mommy.make(models.Variable)

    def test_get_variable(self):
        r = self.client.get("/api/variables/{}/".format(self.variable.id))
        self.assertEqual(r.status_code, 200)


class UnitOfMeasurementTestCase(APITestCase):
    def setUp(self):
        self.unit_of_measurement = mommy.make(models.UnitOfMeasurement)

    def test_get_unit_of_measurement(self):
        r = self.client.get("/api/units/{}/".format(self.unit_of_measurement.id))
        self.assertEqual(r.status_code, 200)


class GentityEventTestCase(APITestCase):
    # We have extensively tested GentityFile, which is practically the same code,
    # so we test this briefly.
    def setUp(self):
        self.station = mommy.make(models.Station)
        self.gentity_file = mommy.make(models.GentityEvent, gentity=self.station)

    def test_list_status_code(self):
        r = self.client.get("/api/stations/{}/events/".format(self.station.id))
        self.assertEqual(r.status_code, 200)


class InstrumentTestCase(APITestCase):
    # We have extensively tested GentityFile, which is practically the same code,
    # so we test this briefly.
    def setUp(self):
        self.station = mommy.make(models.Station)
        self.gentity_file = mommy.make(models.Instrument, station=self.station)

    def test_list_status_code(self):
        r = self.client.get("/api/stations/{}/instruments/".format(self.station.id))
        self.assertEqual(r.status_code, 200)
