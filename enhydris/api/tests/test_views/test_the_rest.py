import tempfile
from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch
from zipfile import ZipFile

from django.contrib.auth.models import Permission, User
from django.contrib.gis.geos import Point
from django.db.models.fields.files import FieldFile
from django.test.utils import override_settings
from rest_framework.test import APITestCase

import iso8601
import pandas as pd
from model_mommy import mommy

from enhydris import models


class Tsdata404TestCase(APITestCase):
    def setUp(self):
        self.station = mommy.make(models.Station)

    def test_get_nonexistent_timeseries(self):
        response = self.client.get(
            "/api/stations/{}/timeseries/1234/data/".format(self.station.id)
        )
        self.assertEqual(response.status_code, 404)

    def test_post_nonexistent_timeseries(self):
        response = self.client.post(
            "/api/stations/{}/timeseries/1234/data/".format(self.station.id)
        )
        self.assertEqual(response.status_code, 404)


class TsdataGetTestCase(APITestCase):
    @patch(
        "enhydris.models.Timeseries.get_data",
        return_value=pd.DataFrame(
            index=[datetime(2017, 11, 23, 17, 23), datetime(2018, 11, 25, 1, 0)],
            data={"value": [1.0, 2.0], "flags": ["", ""]},
            columns=["value", "flags"],
        ),
    )
    def setUp(self, m):
        station = mommy.make(models.Station)
        timeseries = mommy.make(
            models.Timeseries, gentity=station, time_zone__utc_offset=120
        )
        self.response = self.client.get(
            "/api/stations/{}/timeseries/{}/data/".format(station.id, timeseries.id)
        )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_content_type(self):
        self.assertEqual(self.response["Content-Type"], "text/plain")

    def test_response_content(self):
        self.assertEqual(
            self.response.content.decode(),
            "2017-11-23 17:23,1.000000,\r\n" "2018-11-25 01:00,2.000000,\r\n",
        )


class TsdataPostTestCase(APITestCase):
    @patch("enhydris.models.Timeseries.append_data")
    def setUp(self, m):
        self.mock_append_data = m
        user = mommy.make(User, username="admin", is_superuser=True)
        station = mommy.make(models.Station)
        timeseries = mommy.make(models.Timeseries, gentity=station)
        self.client.force_authenticate(user=user)
        self.response = self.client.post(
            "/api/stations/{}/timeseries/{}/data/".format(station.id, timeseries.id),
            data={
                "timeseries_records": (
                    "2017-11-23 17:23,1.000000,\r\n" "2018-11-25 01:00,2.000000,\r\n",
                )
            },
        )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 204)

    def test_called_append_data(self):
        self.assertEqual(self.mock_append_data.call_count, 1)

    def test_called_append_data_with_correct_data(self):
        self.assertEqual(
            self.mock_append_data.call_args[0][0].getvalue(),
            "2017-11-23 17:23,1.000000,\r\n" "2018-11-25 01:00,2.000000,\r\n",
        )


class TsdataPostAuthorizationTestCase(APITestCase):
    def setUp(self):
        self.user1 = mommy.make(User, is_active=True, is_superuser=False)
        self.user2 = mommy.make(User, is_active=True, is_superuser=False)
        self.station = mommy.make(models.Station, creator=self.user1)
        self.timeseries = mommy.make(models.Timeseries, gentity=self.station)

    def _post_tsdata(self):
        return self.client.post(
            "/api/stations/{}/timeseries/{}/data/".format(
                self.station.id, self.timeseries.id
            ),
            data={
                "timeseries_records": (
                    "2017-11-23 17:23,1.000000,\r\n" "2018-11-25 01:00,2.000000,\r\n",
                )
            },
        )

    @patch("enhydris.models.Timeseries.append_data")
    def test_unauthenticated_user_is_denied_permission_to_post_tsdata(self, m):
        self.assertEqual(self._post_tsdata().status_code, 401)

    @patch("enhydris.models.Timeseries.append_data")
    def test_unauthorized_user_is_denied_permission_to_post_tsdata(self, m):
        self.client.force_authenticate(user=self.user2)
        self.assertEqual(self._post_tsdata().status_code, 403)

    @patch("enhydris.models.Timeseries.append_data")
    def test_authorized_user_can_posttsdata(self, m):
        self.client.force_authenticate(user=self.user1)
        self.assertEqual(self._post_tsdata().status_code, 204)


class TsdataPostGarbageTestCase(APITestCase):
    @patch("enhydris.models.Timeseries.append_data", side_effect=iso8601.ParseError)
    def setUp(self, m):
        self.mock_append_data = m
        user = mommy.make(User, username="admin", is_superuser=True)
        station = mommy.make(models.Station)
        timeseries = mommy.make(models.Timeseries, gentity=station)
        self.client.force_authenticate(user=user)
        self.response = self.client.post(
            "/api/stations/{}/timeseries/{}/data/".format(station.id, timeseries.id),
            data={
                "timeseries_records": (
                    # The actual content doesn't matter, since the mock will raise
                    # an error.
                    "2017-11-23 17:23,1.000000,\r\n"
                    "2018-aa-25 01:00,2.000000,\r\n",
                )
            },
        )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 400)


@override_settings(ENHYDRIS_TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS=True)
class TsdataStartAndEndDateTestCase(APITestCase):
    """Test that there's no aware/naive date confusion.

    There was this bug where you'd ask to download from start date, and the start date
    was interpreted as aware whereas the time series data was interpreted as naive. This
    test checks there's no such bug.
    """

    def setUp(self):
        self.tz = mommy.make(models.TimeZone, code="EET", utc_offset=120)
        self.timeseries = mommy.make(models.Timeseries, time_zone=self.tz)

    @patch("enhydris.models.Timeseries.get_data")
    def test_called_get_data_with_proper_start_date(self, m):
        self.response = self.client.get(
            "/api/stations/{}/timeseries/{}/data/?start_date=2005-08-23T19:54".format(
                self.timeseries.gentity.id, self.timeseries.id
            )
        )
        m.assert_called_once_with(
            start_date=datetime(2005, 8, 23, 19, 54), end_date=None
        )

    @patch("enhydris.models.Timeseries.get_data")
    def test_called_get_data_with_proper_end_date(self, m):
        self.response = self.client.get(
            "/api/stations/{}/timeseries/{}/data/?end_date=2005-08-23T19:54".format(
                self.timeseries.gentity.id, self.timeseries.id
            )
        )
        m.assert_called_once_with(
            start_date=None, end_date=datetime(2005, 8, 23, 19, 54)
        )


class TimeseriesBottomTestCase(APITestCase):
    @patch(
        "enhydris.models.Timeseries.get_last_line", return_value="2018-12-09 13:10,20,"
    )
    def setUp(self, m):
        station = mommy.make(models.Station)
        timeseries = mommy.make(
            models.Timeseries, gentity=station, time_zone__utc_offset=120
        )
        self.response = self.client.get(
            "/api/stations/{}/timeseries/{}/bottom/".format(station.id, timeseries.id)
        )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_content_type(self):
        self.assertEqual(self.response["Content-Type"], "text/plain")

    def test_response_content(self):
        self.assertEqual(self.response.content.decode(), "2018-12-09 13:10,20,")


class TimeseriesPostTestCase(APITestCase):
    def setUp(self):
        self.user1 = mommy.make(User, is_active=True, is_superuser=False)
        self.user2 = mommy.make(User, is_active=True, is_superuser=False)
        self.variable = mommy.make(models.Variable)
        self.time_zone = mommy.make(models.TimeZone)
        self.unit_of_measurement = mommy.make(models.UnitOfMeasurement)
        self.station = mommy.make(models.Station, creator=self.user1)

    def _create_timeseries(self):
        return self.client.post(
            "/api/stations/{}/timeseries/".format(self.station.id),
            data={
                "name": "Great time series",
                "gentity": self.station.id,
                "variable": self.variable.id,
                "time_zone": self.time_zone.id,
                "unit_of_measurement": self.unit_of_measurement.id,
            },
        )

    def test_unauthenticated_user_is_denied_permission_to_create_timeseries(self):
        self.assertEqual(self._create_timeseries().status_code, 401)

    def test_unauthorized_user_is_denied_permission_to_create_timeseries(self):
        self.client.force_authenticate(user=self.user2)
        self.assertEqual(self._create_timeseries().status_code, 403)

    def test_authorized_user_can_create_timeseries(self):
        self.client.force_authenticate(user=self.user1)
        self.assertEqual(self._create_timeseries().status_code, 201)


class TimeseriesPostWithWrongStationTestCase(APITestCase):
    def setUp(self):
        self.user = mommy.make(User, is_active=True, is_superuser=False)
        self.variable = mommy.make(models.Variable)
        self.time_zone = mommy.make(models.TimeZone)
        self.unit_of_measurement = mommy.make(models.UnitOfMeasurement)
        self.station1 = mommy.make(models.Station, creator=self.user)
        self.station2 = mommy.make(models.Station, creator=self.user)

    def _create_timeseries(self, station_for_url, station_for_data):
        self.client.force_authenticate(user=self.user)
        return self.client.post(
            "/api/stations/{}/timeseries/".format(station_for_url.id),
            data={
                "name": "Great time series",
                "gentity": station_for_data.id,
                "variable": self.variable.id,
                "time_zone": self.time_zone.id,
                "unit_of_measurement": self.unit_of_measurement.id,
            },
        )

    def test_create_timeseries_with_wrong_station(self):
        response = self._create_timeseries(
            station_for_url=self.station1, station_for_data=self.station2
        )
        self.assertEqual(response.status_code, 400)

    def test_create_timeseries_with_correct_station(self):
        response = self._create_timeseries(
            station_for_url=self.station1, station_for_data=self.station1
        )
        self.assertEqual(response.status_code, 201)


class TimeseriesDeleteTestCase(APITestCase):
    def setUp(self):
        self.user1 = mommy.make(User, is_active=True, is_superuser=False)
        self.user2 = mommy.make(User, is_active=True, is_superuser=False)
        self.station = mommy.make(models.Station, creator=self.user1)
        self.timeseries = mommy.make(models.Timeseries, gentity=self.station)

    def test_unauthenticated_user_is_denied_permission_to_delete_timeseries(self):
        response = self.client.delete(
            "/api/stations/{}/timeseries/{}/".format(
                self.station.id, self.timeseries.id
            )
        )
        self.assertEqual(response.status_code, 401)

    def test_unauthorized_user_is_denied_permission_to_delete_timeseries(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.delete(
            "/api/stations/{}/timeseries/{}/".format(
                self.station.id, self.timeseries.id
            )
        )
        self.assertEqual(response.status_code, 403)

    def test_authorized_user_can_delete_timeseries(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(
            "/api/stations/{}/timeseries/{}/".format(
                self.station.id, self.timeseries.id
            )
        )
        self.assertEqual(response.status_code, 204)


class StationListTestCase(APITestCase):
    def setUp(self):
        self.station = mommy.make(models.Station, name="Hobbiton")
        self.response = self.client.get("/api/stations/")

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_number_of_returned_items(self):
        self.assertEqual(len(self.response.json()["results"]), 1)

    def test_name(self):
        self.assertEqual(self.response.json()["results"][0]["name"], "Hobbiton")


class StationCreateTestCase(APITestCase):
    def setUp(self):
        self.user = mommy.make(User, is_active=True, is_superuser=False)
        self.variable = mommy.make(models.Variable)
        self.time_zone = mommy.make(models.TimeZone)
        self.unit_of_measurement = mommy.make(models.UnitOfMeasurement)
        self.bilbo = mommy.make(models.Person, last_name="Baggins", first_name="Bilbo")
        self.meteorological = mommy.make(models.StationType, descr="Meteorological")

    def _create_station(self):
        return self.client.post(
            "/api/stations/",
            data={
                "name": "Hobbiton",
                "copyright_years": "2018",
                "copyright_holder": "Bilbo Baggins",
                "owner": self.bilbo.id,
                "stype": [self.meteorological.id],
            },
        )

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
        permission = Permission.objects.get(codename="add_station")
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


class StationUpdateAndDeleteTestCase(APITestCase):
    def setUp(self):
        self.user1 = mommy.make(User, is_active=True, is_superuser=False)
        self.user2 = mommy.make(User, is_active=True, is_superuser=False)
        self.variable = mommy.make(models.Variable)
        self.time_zone = mommy.make(models.TimeZone)
        self.unit_of_measurement = mommy.make(models.UnitOfMeasurement)
        self.station = mommy.make(models.Station, creator=self.user1)
        self.bilbo = mommy.make(models.Person, last_name="Baggins", first_name="Bilbo")
        self.meteorological = mommy.make(models.StationType, descr="Meteorological")

    def _put_station(self):
        return self.client.put(
            "/api/stations/{}/".format(self.station.id),
            data={
                "name": "Hobbiton",
                "copyright_years": "2018",
                "copyright_holder": "Bilbo Baggins",
                "owner": self.bilbo.id,
                "stype": [self.meteorological.id],
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


class StationCsvTestCase(APITestCase):
    def setUp(self):
        mommy.make(
            models.Station,
            name="Komboti",
            point=Point(x=21.06071, y=39.09518, srid=4326),
            srid=4326,
        )
        mommy.make(
            models.Station,
            name="Agios Athanasios",
            point=Point(x=21.60121, y=39.22440, srid=4326),
            srid=4326,
        )
        mommy.make(
            models.Station,
            name="Tharbad",
            point=Point(x=-176.48368, y=0.19377, srid=4326),
            srid=4326,
        )
        mommy.make(
            models.Station,
            name="SRID Point, NoSRID Station",
            point=Point(x=-176.48368, y=0.19377, srid=4326),
            srid=None,
        )
        mommy.make(
            models.Station,
            name="NoSRID Point, SRID Station",
            point=Point(x=-176.48368, y=0.19377, srid=None),
            srid=4326,
        )
        mommy.make(
            models.Station,
            name="NoSRID Point, NoSRID Station",
            point=Point(x=-176.48368, y=0.19377, srid=None),
            srid=None,
        )

    def test_station_csv(self):
        response = self.client.get("/api/stations/csv/")
        with tempfile.TemporaryFile() as t:
            t.write(response.content)
            with ZipFile(t) as f:
                stations_csv = f.open("stations.csv").read().decode()
                self.assertIn(",Agios Athanasios,", stations_csv)

    def test_station_with_no_srid_is_included(self):
        response = self.client.get("/api/stations/csv/")
        with tempfile.TemporaryFile() as t:
            t.write(response.content)
            with ZipFile(t) as f:
                stations_csv = f.open("stations.csv").read().decode()
                self.assertIn("SRID Point, NoSRID Station", stations_csv)

    def test_station_with_point_with_no_srid_is_included(self):
        response = self.client.get("/api/stations/csv/")
        with tempfile.TemporaryFile() as t:
            t.write(response.content)
            with ZipFile(t) as f:
                stations_csv = f.open("stations.csv").read().decode()
                self.assertIn("NoSRID Point, SRID Station", stations_csv)

    def test_station_with_no_srid_and_point_with_no_srid_is_included(self):
        response = self.client.get("/api/stations/csv/")
        with tempfile.TemporaryFile() as t:
            t.write(response.content)
            with ZipFile(t) as f:
                stations_csv = f.open("stations.csv").read().decode()
                self.assertIn("NoSRID Point, NoSRID Station", stations_csv)


class WaterDivisionTestCase(APITestCase):
    def setUp(self):
        self.water_division = mommy.make(models.WaterDivision)

    def test_get_water_division(self):
        r = self.client.get("/api/waterdivisions/{}/".format(self.water_division.id))
        self.assertEqual(r.status_code, 200)


class GentityAltCodeTypeTestCase(APITestCase):
    def setUp(self):
        self.gentity_alt_code_type = mommy.make(models.GentityAltCodeType)

    def test_get_gentity_alt_code_type(self):
        r = self.client.get(
            "/api/gentityaltcodetypes/{}/".format(self.gentity_alt_code_type.id)
        )
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


class StationTypeTestCase(APITestCase):
    def setUp(self):
        self.station_type = mommy.make(models.StationType)

    def test_get_station_type(self):
        r = self.client.get("/api/stationtypes/{}/".format(self.station_type.id))
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


class StationAltCodeTestCase(APITestCase):
    def setUp(self):
        self.station = mommy.make(models.Station)
        self.alt_code = mommy.make(
            models.GentityAltCode, gentity=self.station, value="666"
        )
        self.station2 = mommy.make(models.Station)
        self.alt_code2 = mommy.make(models.GentityAltCode, gentity=self.station2)

    def test_list_status_code(self):
        r = self.client.get("/api/stations/{}/altcodes/".format(self.station.id))
        self.assertEqual(r.status_code, 200)

    def test_list_length(self):
        r = self.client.get("/api/stations/{}/altcodes/".format(self.station.id))
        self.assertEqual(len(r.json()["results"]), 1)

    def test_list_content(self):
        r = self.client.get("/api/stations/{}/altcodes/".format(self.station.id))
        self.assertEqual(r.json()["results"][0]["value"], "666")

    def test_detail_status_code(self):
        r = self.client.get(
            "/api/stations/{}/altcodes/{}/".format(self.station.id, self.alt_code.id)
        )
        self.assertEqual(r.status_code, 200)

    def test_detail_content(self):
        r = self.client.get(
            "/api/stations/{}/altcodes/{}/".format(self.station.id, self.alt_code.id)
        )
        self.assertEqual(r.json()["value"], "666")

    def test_detail_returns_nothing_if_wrong_station(self):
        r = self.client.get(
            "/api/stations/{}/altcodes/{}/".format(self.station2.id, self.alt_code.id)
        )
        self.assertEqual(r.status_code, 404)


class GentityEventTestCase(APITestCase):
    # We have extensively tested GentityAltCode, which is practically the same code,
    # so we test this briefly.
    def setUp(self):
        self.station = mommy.make(models.Station)
        self.gentity_file = mommy.make(models.GentityEvent, gentity=self.station)

    def test_list_status_code(self):
        r = self.client.get("/api/stations/{}/events/".format(self.station.id))
        self.assertEqual(r.status_code, 200)


class OverseerTestCase(APITestCase):
    # We have extensively tested GentityAltCode, which is practically the same code,
    # so we test this briefly.
    def setUp(self):
        self.station = mommy.make(models.Station)
        self.gentity_file = mommy.make(models.Overseer, station=self.station)

    def test_list_status_code(self):
        r = self.client.get("/api/stations/{}/overseers/".format(self.station.id))
        self.assertEqual(r.status_code, 200)


class InstrumentTestCase(APITestCase):
    # We have extensively tested GentityAltCode, which is practically the same code,
    # so we test this briefly.
    def setUp(self):
        self.station = mommy.make(models.Station)
        self.gentity_file = mommy.make(models.Instrument, station=self.station)

    def test_list_status_code(self):
        r = self.client.get("/api/stations/{}/instruments/".format(self.station.id))
        self.assertEqual(r.status_code, 200)


class GentityFileTestCase(APITestCase):
    # We have extensively tested GentityAltCode, which is practically the same code,
    # so we test this briefly.
    def setUp(self):
        self.station = mommy.make(models.Station)
        self.gentity_file = mommy.make(models.GentityFile, gentity=self.station)

    def test_list_status_code(self):
        r = self.client.get("/api/stations/{}/files/".format(self.station.id))
        self.assertEqual(r.status_code, 200)


class GentityFileContentTestCase(APITestCase):
    def setUp(self):
        # Mocking. We mock several things in Django and Python so that:
        #   1) The name of the file appears to be some_image.jpg
        #   2) Its data appears to be ABCDEF
        #   3) Its size appears to be 6
        self.saved_fieldfile_file = FieldFile.file
        self.filemock = MagicMock(**{"return_value.name": "some_image.jpg"})
        FieldFile.file = property(self.filemock, MagicMock(), MagicMock())
        patch1 = patch("enhydris.api.views.open", mock_open(read_data="ABCDEF"))
        patch2 = patch("os.path.getsize", return_value=6)

        self.station = mommy.make(models.Station)
        self.gentity_file = mommy.make(models.GentityFile, gentity=self.station)
        with patch1, patch2:
            self.response = self.client.get(
                "/api/stations/{}/files/{}/content/".format(
                    self.station.id, self.gentity_file.id
                )
            )

    def tearDown(self):
        FieldFile.file = self.saved_fieldfile_file

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_content(self):
        self.assertEqual(self.response.content, b"ABCDEF")

    def test_content_type(self):
        self.assertEqual(self.response["Content-Type"], "image/jpeg")


class GentityFileContentWithoutFileTestCase(APITestCase):
    def setUp(self):
        # Mommy creates a GentityFile without an associated file, so the
        # result should be 404
        self.station = mommy.make(models.Station)
        self.gentity_file = mommy.make(models.GentityFile, gentity=self.station)

        self.response = self.client.get(
            "/api/stations/{}/files/{}/content/".format(
                self.station.id, self.gentity_file.id
            )
        )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 404)
