from rest_framework.test import APITestCase

from model_mommy import mommy

from enhydris import models


class GareaTestCase(APITestCase):
    def setUp(self):
        self.garea = mommy.make(models.Garea)

    def test_get_garea(self):
        r = self.client.get("/api/gareas/{}/".format(self.garea.id))
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


class EventTypeTestCase(APITestCase):
    def setUp(self):
        self.event_type = mommy.make(models.EventType)

    def test_get_event_type(self):
        r = self.client.get("/api/eventtypes/{}/".format(self.event_type.id))
        self.assertEqual(r.status_code, 200)


class VariableTestCase(APITestCase):
    def setUp(self):
        self.variable = mommy.make(models.Variable, descr="Temperature")

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


class GetTokenTestCase(APITestCase):
    """Test a workaround against a DRF <3.13 problem.

    There's a nasty typo in a Greek translation string in DRF—instead of '"{method}"' it
    has '"{method"}'. This causes an internal server error when we try to visit
    "/api/auth/login/" and the language is Greek. As of this writing, the latest version
    of DRF (3.12) still has the problem, although they tell us it's been fixed in
    Transifex (see https://github.com/encode/django-rest-framework/pull/7591). While
    waiting for a new version, we've worked around by overriding the translation (see
    enhydris/translation_overrides.py and locale/el/LC_MESSAGES/django.po). We test this
    here. When a fixed DRF is out, this test should be removed together with the
    translation override.
    """

    def test_greek(self):
        r = self.client.get("/api/auth/login/", HTTP_ACCEPT_LANGUAGE="el")
        self.assertContains(r, "δεν επιτρέπεται", status_code=405)
