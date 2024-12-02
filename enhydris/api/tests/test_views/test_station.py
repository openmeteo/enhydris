import tempfile
from zipfile import ZipFile

from django.contrib.auth.models import Permission, User
from django.contrib.gis.geos import Point
from django.contrib.sites.models import Site
from django.test.utils import override_settings
from rest_framework.test import APITestCase

from model_bakery import baker

from enhydris import models


@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class StationListTestCase(APITestCase):
    def setUp(self):
        self.station = baker.make(models.Station, name="Hobbiton")
        self.response = self.client.get("/api/stations/")

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_number_of_returned_items(self):
        self.assertEqual(len(self.response.json()["results"]), 1)

    def test_name(self):
        self.assertEqual(self.response.json()["results"][0]["name"], "Hobbiton")


@override_settings(SITE_ID=1)
@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class StationListSitesTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        baker.make(Site, id=1, domain="middleearth.com", name="Middle Earth")
        site2 = baker.make(Site, id=2, domain="realearth.com", name="Real Earth")
        baker.make(models.Station, name="Hobbiton")
        arta = baker.make(models.Station, name="Arta")
        arta.sites.set({site2})

    def test_list_contains_hobbiton(self):
        response = self.client.get("/api/stations/")
        self.assertContains(response, "Hobbiton")

    def test_list_does_not_contain_arta(self):
        response = self.client.get("/api/stations/")
        self.assertNotContains(response, "Arta")


@override_settings(SITE_ID=1)
@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class StationDetailSitesTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        baker.make(Site, id=1, domain="middleearth.com", name="Middle Earth")
        baker.make(Site, id=2, domain="realearth.com", name="Real Earth")
        baker.make(models.Station, id=42, name="Hobbiton")

    def test_hobbiton_detail(self):
        response = self.client.get("/api/stations/42/")
        self.assertEqual(response.status_code, 200)

    @override_settings(SITE_ID=2)
    def test_hobbiton_detail_unavailable_on_site2(self):
        response = self.client.get("/api/stations/42/")
        self.assertEqual(response.status_code, 404)


@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class StationCreateTestCase(APITestCase):
    def setUp(self):
        self.user = baker.make(User, is_active=True, is_superuser=False)
        self.variable = baker.make(models.Variable)
        self.unit_of_measurement = baker.make(models.UnitOfMeasurement)
        self.bilbo = baker.make(models.Person, last_name="Baggins", first_name="Bilbo")

    def _create_station(self):
        return self.client.post(
            "/api/stations/",
            data={
                "name": "Hobbiton",
                "owner": self.bilbo.id,
                "geom": "SRID=4326;POINT (20.94565 39.12102)",
            },
        )

    @override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
    def test_unauthenticated_user_is_denied_permission_to_create_station(self):
        response = self._create_station()
        self.assertEqual(response.status_code, 401)

    @override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=False)
    def test_unauthorized_user_is_denied_permission_to_create_station(self):
        self.client.force_authenticate(user=self.user)
        response = self._create_station()
        self.assertEqual(response.status_code, 403)

    @override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=False)
    def test_authorized_user_can_create_station(self):
        permission = Permission.objects.get(
            content_type__app_label="enhydris", codename="add_station"
        )
        self.user.user_permissions.add(permission)
        self.user.save()
        self.client.force_authenticate(user=self.user)
        response = self._create_station()
        self.assertEqual(response.status_code, 201)

    @override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
    def test_any_user_can_create_station_when_system_is_open(self):
        self.client.force_authenticate(user=self.user)
        response = self._create_station()
        self.assertEqual(response.status_code, 201)


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class StationUpdateAndDeleteTestCase(APITestCase):
    def setUp(self):
        self.user1 = baker.make(User, is_active=True, is_superuser=False)
        self.user2 = baker.make(User, is_active=True, is_superuser=False)
        self.variable = baker.make(models.Variable)
        self.unit_of_measurement = baker.make(models.UnitOfMeasurement)
        self.station = baker.make(models.Station, creator=self.user1)
        self.bilbo = baker.make(models.Person, last_name="Baggins", first_name="Bilbo")

    def _put_station(self):
        return self.client.put(
            "/api/stations/{}/".format(self.station.id),
            data={
                "name": "Hobbiton",
                "owner": self.bilbo.id,
                "geom": "SRID=4326;POINT (20.94565 39.12102)",
            },
        )

    def _patch_station(self):
        return self.client.patch(
            "/api/stations/{}/".format(self.station.id), data={"name": "Hobbiton"}
        )

    def _delete_station(self):
        return self.client.delete("/api/stations/{}/".format(self.station.id))

    def test_unauthenticated_user_is_denied_permission_to_put_station(self):
        response = self._put_station()
        self.assertEqual(response.status_code, 401)

    def test_unauthorized_user_is_denied_permission_to_put_station(self):
        self.client.force_authenticate(user=self.user2)
        response = self._put_station()
        self.assertEqual(response.status_code, 403)

    def test_authorized_user_can_put_station(self):
        self.client.force_authenticate(user=self.user1)
        response = self._put_station()
        self.assertEqual(response.status_code, 200, response.content)

    def test_unauthenticated_user_is_denied_permission_to_patch_station(self):
        response = self._patch_station()
        self.assertEqual(response.status_code, 401)

    def test_unauthorized_user_is_denied_permission_to_patch_station(self):
        self.client.force_authenticate(user=self.user2)
        response = self._patch_station()
        self.assertEqual(response.status_code, 403)

    def test_authorized_user_can_patch_station(self):
        self.client.force_authenticate(user=self.user1)
        response = self._patch_station()
        self.assertEqual(response.status_code, 200, response.content)

    def test_unauthenticated_user_is_denied_permission_to_delete_station(self):
        response = self._delete_station()
        self.assertEqual(response.status_code, 401)

    def test_unauthorized_user_is_denied_permission_to_delete_station(self):
        self.client.force_authenticate(user=self.user2)
        response = self._delete_station()
        self.assertEqual(response.status_code, 403)

    def test_authorized_user_can_delete_station(self):
        self.client.force_authenticate(user=self.user1)
        response = self._delete_station()
        self.assertEqual(response.status_code, 204, response.content)


@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class StationCsvTestCase(APITestCase):
    def setUp(self):
        self._create_stations()

    def _create_stations(self):
        self.station_komboti = baker.make(
            models.Station,
            name="Komboti",
            geom=Point(x=21.06071, y=39.09518, srid=4326),
            original_srid=4326,
        )
        self.station_agios_athanasios = baker.make(
            models.Station,
            name="Agios Athanasios",
            geom=Point(x=21.60121, y=39.22440, srid=4326),
            original_srid=4326,
        )
        baker.make(
            models.Station,
            name="Tharbad",
            geom=Point(x=-176.48368, y=0.19377, srid=4326),
            original_srid=4326,
        )
        baker.make(
            models.Station,
            name="SRID Point, NoSRID Station",
            geom=Point(x=-176.48368, y=0.19377, srid=4326),
            original_srid=None,
        )
        baker.make(
            models.Station,
            name="NoSRID Point, SRID Station",
            geom=Point(x=-176.48368, y=0.19377, srid=None),
            original_srid=4326,
        )
        baker.make(
            models.Station,
            name="NoSRID Point, NoSRID Station",
            geom=Point(x=-176.48368, y=0.19377, srid=None),
            original_srid=None,
        )

    def _create_timeseries_groups(self):
        self._create_timeseries_group(self.station_komboti, "Temperature")
        self._create_timeseries_group(self.station_komboti, "Humidity")
        self._create_timeseries_group(self.station_agios_athanasios, "Temperature")
        self._create_timeseries_group(self.station_agios_athanasios, "Humidity")

    def _create_timeseries_group(self, station, variable_descr):
        baker.make(
            models.TimeseriesGroup, gentity=station, variable__descr=variable_descr
        )

    def test_station_csv(self):
        response = self.client.get("/api/stations/csv/")
        with tempfile.TemporaryFile() as t:
            t.write(response.content)
            with ZipFile(t) as f:
                stations_csv = f.open("stations.csv").read().decode()
                self.assertIn(",Agios Athanasios,", stations_csv)

    def test_station_with_no_original_srid_is_included(self):
        response = self.client.get("/api/stations/csv/")
        with tempfile.TemporaryFile() as t:
            t.write(response.content)
            with ZipFile(t) as f:
                stations_csv = f.open("stations.csv").read().decode()
                self.assertIn("SRID Point, NoSRID Station", stations_csv)

    def test_station_with_geometry_with_no_original_srid_is_included(self):
        response = self.client.get("/api/stations/csv/")
        with tempfile.TemporaryFile() as t:
            t.write(response.content)
            with ZipFile(t) as f:
                stations_csv = f.open("stations.csv").read().decode()
                self.assertIn("NoSRID Point, SRID Station", stations_csv)

    def test_station_with_no_srid_and_geometry_with_no_srid_is_included(self):
        response = self.client.get("/api/stations/csv/")
        with tempfile.TemporaryFile() as t:
            t.write(response.content)
            with ZipFile(t) as f:
                stations_csv = f.open("stations.csv").read().decode()
                self.assertIn("NoSRID Point, NoSRID Station", stations_csv)

    def test_num_queries(self):
        self._create_timeseries_groups()
        # There should be seven queries: one for stations, one for timeseries_groups,
        # one for timeseries. The other four are two for django_session and two
        # for a savepoint.
        with self.assertNumQueries(7):
            self.client.get("/api/stations/csv/")
