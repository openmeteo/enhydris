import json
from datetime import datetime

from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import Point
from django.test import TestCase
from django.test.client import BOUNDARY, MULTIPART_CONTENT, encode_multipart
from django.test.utils import override_settings
from rest_framework.test import APITestCase

import iso8601
import pytz
from model_mommy import mommy

import enhydris
from enhydris import models
from enhydris.tests.test_views import RandomEnhydrisTimeseriesDataDir


def create_test_data():
    "Besides creating test data, return the list of created gentities."
    user1 = User.objects.create_user("user1", "user1@nowhere.org", "password1")
    user1.is_active = True
    user1.is_superuser = False
    user1.is_staff = False
    user1.save()

    user2 = User.objects.create_user("user2", "user2@nowhere.org", "password2")
    user2.is_active = True
    user2.is_superuser = False
    user2.is_staff = False
    user2.save()

    organization1 = models.Organization.objects.create(name="Test Organization")
    timezone1 = models.TimeZone.objects.create(code="Test Time Zone", utc_offset=2)
    variable1 = models.Variable.objects.create(descr="Test Variable")
    uom1 = models.UnitOfMeasurement.objects.create(
        descr="Test Unit Of Measurement", symbol="+"
    )
    uom1.variables = [variable1]
    uom1.save()

    pd1 = models.PoliticalDivision.objects.create(name="Test Political Division")
    water_basin1 = models.WaterBasin.objects.create(name="Test Water Basin")
    water_division1 = models.WaterDivision.objects.create(name="Test Water Division")
    stype1 = models.StationType.objects.create(descr="Test Station Type")

    station1 = mommy.make(
        models.Station,
        name="Test Station",
        water_division=water_division1,
        water_basin=water_basin1,
        political_division=pd1,
        owner=organization1,
        is_automatic=False,
        copyright_holder="Joe User",
        copyright_years=2014,
        stype__id=stype1.id,
        gpoint__point=Point(0.0, 0.0),
    )

    station2 = mommy.make(
        models.Station,
        name="Test Station 2",
        water_division=water_division1,
        water_basin=water_basin1,
        political_division=pd1,
        owner=organization1,
        is_automatic=False,
        copyright_holder="Joe User",
        copyright_years=2014,
        stype__id=stype1.id,
        gpoint__point=Point(0.0, 0.0),
        last_modified=iso8601.parse_date(
            "2010-05-10 14:26:22", default_timezone=pytz.utc
        ),
    )

    # timeseries1
    models.Timeseries.objects.create(
        name="Test Timeseries",
        time_zone=timezone1,
        variable=variable1,
        unit_of_measurement=uom1,
        gentity=station1,
    )
    # timeseries2
    models.Timeseries.objects.create(
        name="Test Timeseries 2",
        time_zone=timezone1,
        variable=variable1,
        unit_of_measurement=uom1,
        gentity=station1,
    )

    # permissions1
    enhydris.permissions.models.Permission.objects.create(
        name="edit",
        object_id=station1.id,
        user=user1,
        content_type=ContentType.objects.get_for_model(models.Station),
    )

    return [pd1, water_basin1, water_division1, station1, station2]


class ReadTestCase(APITestCase):
    def setUp(self):
        self.reference_gentities = create_test_data()

    def testGentityList(self):

        response = self.client.get("/api/Gentity/")
        response.data.sort(key=lambda x: x["id"])
        self.assertEqual(len(response.data), len(self.reference_gentities))
        for res_datum, ref_datum in zip(response.data, self.reference_gentities):
            self.assertEqual(res_datum["id"], ref_datum.id)
            self.assertEqual(res_datum["name"], ref_datum.name)
            self.assertEqual(res_datum["name_alt"], ref_datum.name_alt)
            self.assertEqual(res_datum["short_name"], ref_datum.short_name)
            self.assertEqual(res_datum["short_name_alt"], ref_datum.short_name_alt)
            self.assertEqual(res_datum["remarks"], ref_datum.remarks)
            self.assertEqual(res_datum["remarks_alt"], ref_datum.remarks_alt)
            wb_id = ref_datum.water_basin.id if ref_datum.water_basin else None
            self.assertEqual(res_datum["water_basin"], wb_id)
            wd_id = ref_datum.water_division.id if ref_datum.water_division else None
            self.assertEqual(res_datum["water_division"], wd_id)
            pd_id = (
                ref_datum.political_division.id
                if ref_datum.political_division
                else None
            )
            self.assertEqual(res_datum["political_division"], pd_id)
            res_last_modified = iso8601.parse_date(
                res_datum["last_modified"], default_timezone=pytz.utc
            )
            self.assertEqual(res_last_modified, ref_datum.last_modified)

        # Same thing, but test with modified_after
        n_all_gentities = len(self.reference_gentities)
        for item in self.reference_gentities[:]:
            if item.last_modified < datetime(2010, 5, 11, tzinfo=pytz.utc):
                self.reference_gentities.remove(item)
        n_recent_gentities = len(self.reference_gentities)
        self.assertTrue(n_recent_gentities < n_all_gentities)
        response = self.client.get("/api/Gentity/modified_after/2010-05-11 00:00/")
        response.data.sort(key=lambda x: x["id"])
        self.assertEqual(len(response.data), len(self.reference_gentities))
        for res_datum, ref_datum in zip(response.data, self.reference_gentities):
            self.assertEqual(res_datum["id"], ref_datum.id)
            self.assertEqual(res_datum["name"], ref_datum.name)
            self.assertEqual(res_datum["name_alt"], ref_datum.name_alt)
            self.assertEqual(res_datum["short_name"], ref_datum.short_name)
            self.assertEqual(res_datum["short_name_alt"], ref_datum.short_name_alt)
            self.assertEqual(res_datum["remarks"], ref_datum.remarks)
            self.assertEqual(res_datum["remarks_alt"], ref_datum.remarks_alt)
            wb_id = ref_datum.water_basin.id if ref_datum.water_basin else None
            self.assertEqual(res_datum["water_basin"], wb_id)
            wd_id = ref_datum.water_division.id if ref_datum.water_division else None
            self.assertEqual(res_datum["water_division"], wd_id)
            pd_id = (
                ref_datum.political_division.id
                if ref_datum.political_division
                else None
            )
            self.assertEqual(res_datum["political_division"], pd_id)
            res_last_modified = iso8601.parse_date(
                res_datum["last_modified"], default_timezone=None
            )
            self.assertEqual(res_last_modified, ref_datum.last_modified)

        @RandomEnhydrisTimeseriesDataDir()
        def test_get_nonexisting_timeseries_data_using_url_query(self):
            response = self.client.get("/api/tsdata/?pk=9999999999999")
            self.assertEqual(response.status_code, 404)

        @RandomEnhydrisTimeseriesDataDir()
        def test_get_nonexisting_timeseries_data_using_url_parameter(self):
            response = self.client.get("/api/tsdata/9999999", follow=True)
            self.assertEqual(response.status_code, 404)


class WriteTestCase(TestCase):
    def setUp(self):
        create_test_data()
        self.timeseries1 = models.Timeseries.objects.get(name="Test Timeseries")

    def testTimeSeries(self):
        # Get an existing time series
        response = self.client.get("/api/Timeseries/{}/".format(self.timeseries1.id))
        t = json.loads(response.content.decode("utf-8"))

        # Change some of its attributes
        t["id"] = None
        t["name"] = "Test Timeseries 1221"
        t["remarks"] = "Yet another timeseries test"

        # Attempt to upload unauthenticated - should deny
        d = json.dumps(t)
        response = self.client.post(
            "/api/Timeseries/", data=d, content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            models.Timeseries.objects.filter(name="Test Timeseries 1221").count(), 0
        )

        # Now try again, this time logged on as user 2; again should deny
        self.assertTrue(self.client.login(username="user2", password="password2"))
        response = self.client.post(
            "/api/Timeseries/", data=d, content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            models.Timeseries.objects.filter(name="Test Timeseries 1221").count(), 0
        )
        self.client.logout()

        # Now try again, this time logged on as user 1; should accept
        self.assertTrue(self.client.login(username="user1", password="password1"))
        response = self.client.post(
            "/api/Timeseries/", data=d, content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            models.Timeseries.objects.filter(name="Test Timeseries 1221").count(), 1
        )
        self.client.logout()

    def testTimeseriesDelete(self):
        # Check the number of timeseries available
        ntimeseries = models.Timeseries.objects.count()

        # 1 is not enough; we need to know we aren't
        # deleting more than necessary.
        assert ntimeseries > 1

        # Attempt to delete unauthenticated - should fail
        response = self.client.delete("/api/Timeseries/{}/".format(self.timeseries1.id))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            models.Timeseries.objects.filter(pk=self.timeseries1.id).count(), 1
        )
        self.assertEqual(models.Timeseries.objects.count(), ntimeseries)

        # Try again as user2 - should fail
        self.assertTrue(self.client.login(username="user2", password="password2"))
        response = self.client.delete("/api/Timeseries/{}/".format(self.timeseries1.id))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            models.Timeseries.objects.filter(pk=self.timeseries1.id).count(), 1
        )
        self.assertEqual(models.Timeseries.objects.count(), ntimeseries)
        self.client.logout()

        # Try again as user1 - should succeed
        self.assertTrue(self.client.login(username="user1", password="password1"))
        response = self.client.delete("/api/Timeseries/{}/".format(self.timeseries1.id))
        self.assertEqual(response.status_code, 204)
        self.assertEqual(
            models.Timeseries.objects.filter(pk=self.timeseries1.id).count(), 0
        )
        self.assertEqual(models.Timeseries.objects.count(), ntimeseries - 1)
        self.client.logout()

    @RandomEnhydrisTimeseriesDataDir()
    def testUploadTsDataUnauthenticated(self):
        # Attempt to upload some timeseries data, unauthenticated
        response = self.client.put(
            "/api/tsdata/{}/".format(self.timeseries1.id),
            encode_multipart(
                BOUNDARY, {"timeseries_records": "2012-11-06 18:17,20,\n"}
            ),
            content_type=MULTIPART_CONTENT,
        )
        t = self.timeseries1.get_data()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(t), 0)

    @RandomEnhydrisTimeseriesDataDir()
    def testUploadTsDataAsWrongUser(self):
        # Attempt to upload some timeseries data as user 2; should deny
        self.assertTrue(self.client.login(username="user2", password="password2"))
        response = self.client.put(
            "/api/tsdata/{}/".format(self.timeseries1.id),
            encode_multipart(
                BOUNDARY, {"timeseries_records": "2012-11-06 18:17,20,\n"}
            ),
            content_type=MULTIPART_CONTENT,
        )
        adataframe = self.timeseries1.get_data()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(adataframe), 0)
        self.client.logout()

    @RandomEnhydrisTimeseriesDataDir()
    def testUploadTsDataGarbage(self):
        self.assertTrue(self.client.login(username="user1", password="password1"))
        response = self.client.put(
            "/api/tsdata/{}/".format(self.timeseries1.id),
            encode_multipart(
                BOUNDARY, {"timeseries_records": "2012-aa-06 18:17,20,\n"}
            ),
            content_type=MULTIPART_CONTENT,
        )
        adataframe = self.timeseries1.get_data()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(adataframe), 0)
        self.client.logout()

    @RandomEnhydrisTimeseriesDataDir()
    def testUploadTsData(self):
        self.assertTrue(self.client.login(username="user1", password="password1"))
        response = self.client.put(
            "/api/tsdata/{}/".format(self.timeseries1.id),
            encode_multipart(
                BOUNDARY, {"timeseries_records": "2012-11-06 18:17,20,\n"}
            ),
            content_type=MULTIPART_CONTENT,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode("utf-8"), "1")
        adataframe = models.Timeseries.objects.get(pk=self.timeseries1.id).get_data()
        self.assertEqual(len(adataframe), 1)
        self.assertEqual(adataframe.index[0], datetime(2012, 11, 6, 18, 17, 0))
        self.assertEqual(adataframe.iloc[0].value, 20)
        self.client.logout()

        # Append two more records
        self.assertTrue(self.client.login(username="user1", password="password1"))
        response = self.client.put(
            "/api/tsdata/{}/".format(self.timeseries1.id),
            encode_multipart(
                BOUNDARY,
                {"timeseries_records": "2012-11-06 18:18,21,\n2012-11-07 18:18,23,\n"},
            ),
            content_type=MULTIPART_CONTENT,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode("utf-8"), "2")
        adataframe = models.Timeseries.objects.get(pk=self.timeseries1.id).get_data()
        self.assertEqual(len(adataframe), 3)
        self.assertEqual(adataframe.index[0], datetime(2012, 11, 6, 18, 17, 0))
        self.assertEqual(adataframe.iloc[0].value, 20)
        self.assertEqual(adataframe.index[1], datetime(2012, 11, 6, 18, 18, 0))
        self.assertEqual(adataframe.iloc[1].value, 21)
        self.assertEqual(adataframe.index[2], datetime(2012, 11, 7, 18, 18, 0))
        self.assertEqual(adataframe.iloc[2].value, 23)
        self.client.logout()

        # Try to append an earlier record; should fail
        self.assertTrue(self.client.login(username="user1", password="password1"))
        response = self.client.put(
            "/api/tsdata/{}/".format(self.timeseries1.id),
            encode_multipart(
                BOUNDARY, {"timeseries_records": "2012-11-05 18:18,21,\n"}
            ),
            content_type=MULTIPART_CONTENT,
        )
        self.client.logout()
        self.assertEqual(response.status_code, 400)
        t = models.Timeseries.objects.get(pk=self.timeseries1.id).get_data()
        self.assertEqual(len(t), 3)
        self.client.logout()


class WriteStationTestCase(TestCase):
    def setUp(self):
        create_test_data()
        self.station1 = models.Station.objects.get(name="Test Station")

    def test_edit_station(self):
        # Get an existing station
        response = self.client.get("/api/Station/{}/".format(self.station1.id))
        station = json.loads(response.content.decode("utf-8"))

        # Change some of its attributes
        station_id = station["id"]
        del station["id"]
        station["name"] = "Test Station 1222"
        station["remarks"] = "Yet another station test"

        # Attempt to upload unauthenticated - should deny
        d = json.dumps(station)
        response = self.client.put(
            "/api/Station/{}/".format(station_id),
            data=d,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            models.Station.objects.filter(name="Test Station 1222").count(), 0
        )

        # Try again, this time logged on as user 2; again should deny
        self.assertTrue(self.client.login(username="user2", password="password2"))
        response = self.client.put(
            "/api/Station/{}/".format(station_id),
            data=d,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            models.Station.objects.filter(name="Test Station 1222").count(), 0
        )
        self.client.logout()

        # Try again, as user 1; should accept
        self.assertTrue(self.client.login(username="user1", password="password1"))
        response = self.client.put(
            "/api/Station/{}/".format(station_id),
            data=d,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            models.Station.objects.filter(name="Test Station 1222").count(), 1
        )
        self.client.logout()

    def test_station_delete(self):
        # Check the number of stations available
        nstations = models.Station.objects.count()

        # 1 is not enough; we need to know we aren't
        # deleting more than necessary.
        assert nstations > 1

        # Attempt to delete unauthenticated - should fail
        response = self.client.delete("/api/Station/{}/".format(self.station1.id))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(models.Station.objects.filter(pk=self.station1.id).count(), 1)
        self.assertEqual(models.Station.objects.count(), nstations)

        # Try again as user2 - should fail
        self.assertTrue(self.client.login(username="user2", password="password2"))
        response = self.client.delete("/api/Station/{}/".format(self.station1.id))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(models.Station.objects.filter(pk=self.station1.id).count(), 1)
        self.assertEqual(models.Station.objects.count(), nstations)
        self.client.logout()

        # Try again as user1 - should succeed
        self.assertTrue(self.client.login(username="user1", password="password1"))
        response = self.client.delete("/api/Station/{}/".format(self.station1.id))
        self.assertEqual(response.status_code, 204)
        self.assertEqual(models.Station.objects.filter(pk=self.station1.id).count(), 0)
        self.assertEqual(models.Station.objects.count(), nstations - 1)
        self.client.logout()


class CreateStationTestCase(TestCase):
    def setUp(self):
        create_test_data()

        # Get an existing station
        obj = models.Station.objects.get(name="Test Station")
        response = self.client.get("/api/Station/{}/".format(obj.id))
        self.station = json.loads(response.content.decode("utf-8"))

        # Change some of its attributes
        del self.station["id"]
        self.station["name"] = "Test Station 1507"
        self.station["remarks"] = "Yet another station test"

    def test_create_unauthenticated(self):
        response = self.client.post(
            "/api/Station/",
            data=json.dumps(self.station),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            models.Station.objects.filter(name="Test Station 1507").count(), 0
        )

    @override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
    def test_create_station_on_database_allowing_any_user(self):
        self.assertTrue(self.client.login(username="user2", password="password2"))
        response = self.client.post(
            "/api/Station/",
            data=json.dumps(self.station),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            models.Station.objects.filter(name="Test Station 1507").count(), 1
        )
        self.client.logout()

    @override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=False)
    def test_create_station_by_disallowed_user(self):
        self.assertTrue(self.client.login(username="user2", password="password2"))
        response = self.client.post(
            "/api/Station/",
            data=json.dumps(self.station),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            models.Station.objects.filter(name="Test Station 1507").count(), 0
        )
        self.client.logout()

    @override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=False)
    def test_create_station_by_allowed_user(self):
        # Give the appropriate permissions to the user
        user = User.objects.get(username="user2")
        permission = Permission.objects.get(codename="add_station")
        user.user_permissions.add(permission)
        user.save()

        self.assertTrue(self.client.login(username="user2", password="password2"))
        response = self.client.post(
            "/api/Station/",
            data=json.dumps(self.station),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            models.Station.objects.filter(name="Test Station 1507").count(), 1
        )
        self.client.logout()


class WaterDivisionTestCase(TestCase):
    def setUp(self):
        self.water_division = mommy.make(models.WaterDivision)

    def test_get_water_division(self):
        r = self.client.get("/api/WaterDivision/{}/".format(self.water_division.id))
        self.assertEqual(r.status_code, 200)


class GentityAltCodeTypeTestCase(TestCase):
    def setUp(self):
        self.gentity_alt_code_type = mommy.make(models.GentityAltCodeType)

    def test_get_gentity_alt_code_type(self):
        r = self.client.get(
            "/api/GentityAltCodeType/{}/".format(self.gentity_alt_code_type.id)
        )
        self.assertEqual(r.status_code, 200)


class OrganizationTestCase(TestCase):
    def setUp(self):
        self.organization = mommy.make(models.Organization)

    def test_get_organization(self):
        r = self.client.get("/api/Organization/{}/".format(self.organization.id))
        self.assertEqual(r.status_code, 200)


class PersonTestCase(TestCase):
    def setUp(self):
        self.person = mommy.make(models.Person)

    def test_get_person(self):
        r = self.client.get("/api/Person/{}/".format(self.person.id))
        self.assertEqual(r.status_code, 200)


class StationTypeTestCase(TestCase):
    def setUp(self):
        self.station_type = mommy.make(models.StationType)

    def test_get_station_type(self):
        r = self.client.get("/api/StationType/{}/".format(self.station_type.id))
        self.assertEqual(r.status_code, 200)


class TimeZoneTestCase(TestCase):
    def setUp(self):
        self.time_zone = mommy.make(models.TimeZone)

    def test_get_time_zone(self):
        r = self.client.get("/api/TimeZone/{}/".format(self.time_zone.id))
        self.assertEqual(r.status_code, 200)


class PoliticalDivisionTestCase(TestCase):
    def setUp(self):
        self.political_division = mommy.make(models.PoliticalDivision)

    def test_get_political_division(self):
        r = self.client.get(
            "/api/PoliticalDivision/{}/".format(self.political_division.id)
        )
        self.assertEqual(r.status_code, 200)


class IntervalTypeTestCase(TestCase):
    def setUp(self):
        self.interval_type = mommy.make(models.IntervalType)

    def test_get_interval_type(self):
        r = self.client.get("/api/IntervalType/{}/".format(self.interval_type.id))
        self.assertEqual(r.status_code, 200)


class FileTypeTestCase(TestCase):
    def setUp(self):
        self.file_type = mommy.make(models.FileType)

    def test_get_file_type(self):
        r = self.client.get("/api/FileType/{}/".format(self.file_type.id))
        self.assertEqual(r.status_code, 200)


class EventTypeTestCase(TestCase):
    def setUp(self):
        self.event_type = mommy.make(models.EventType)

    def test_get_event_type(self):
        r = self.client.get("/api/EventType/{}/".format(self.event_type.id))
        self.assertEqual(r.status_code, 200)


class InstrumentTypeTestCase(TestCase):
    def setUp(self):
        self.instrument_type = mommy.make(models.InstrumentType)

    def test_get_instrument_type(self):
        r = self.client.get("/api/InstrumentType/{}/".format(self.instrument_type.id))
        self.assertEqual(r.status_code, 200)


class WaterBasinTestCase(TestCase):
    def setUp(self):
        self.water_basin = mommy.make(models.WaterBasin)

    def test_get_water_basin(self):
        r = self.client.get("/api/WaterBasin/{}/".format(self.water_basin.id))
        self.assertEqual(r.status_code, 200)


class TimeStepTestCase(TestCase):
    def setUp(self):
        self.time_step = mommy.make(models.TimeStep, length_minutes=10, length_months=0)

    def test_get_time_step(self):
        r = self.client.get("/api/TimeStep/{}/".format(self.time_step.id))
        self.assertEqual(r.status_code, 200)


class VariableTestCase(TestCase):
    def setUp(self):
        self.variable = mommy.make(models.Variable)

    def test_get_variable(self):
        r = self.client.get("/api/Variable/{}/".format(self.variable.id))
        self.assertEqual(r.status_code, 200)


class UnitOfMeasurementTestCase(TestCase):
    def setUp(self):
        self.unit_of_measurement = mommy.make(models.UnitOfMeasurement)

    def test_get_unit_of_measurement(self):
        r = self.client.get(
            "/api/UnitOfMeasurement/{}/".format(self.unit_of_measurement.id)
        )
        self.assertEqual(r.status_code, 200)
