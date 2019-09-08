import datetime as dt
import os
from glob import glob
from io import StringIO
from locale import LC_CTYPE, getlocale, setlocale

from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from model_mommy import mommy

from enhydris import models
from enhydris.admin.station import TimeseriesInlineAdminForm
from enhydris.tests import RandomEnhydrisTimeseriesDataDir


class StationSearchTestCase(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(
            username="alice", password="topsecret", is_staff=True, is_superuser=True
        )
        mommy.make(models.Station, name="Hobbiton")
        mommy.make(models.Station, name="Rivendell")

    def test_search_returns_correct_result(self):
        self.client.login(username="alice", password="topsecret")
        response = self.client.get("/admin/enhydris/station/?q=vendel")
        self.assertContains(response, "Rivendell")
        self.assertNotContains(response, "Hobbiton")


class StationPermsTestCaseBase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        alice = User.objects.create_user(
            username="alice", password="topsecret", is_staff=True, is_superuser=True
        )
        bob = User.objects.create_user(
            username="bob", password="topsecret", is_staff=True, is_superuser=False
        )
        charlie = User.objects.create_user(
            username="charlie", password="topsecret", is_staff=True, is_superuser=False
        )
        User.objects.create_user(
            username="david", password="topsecret", is_staff=True, is_superuser=False
        )
        elaine = User.objects.create_user(
            username="elaine", password="topsecret", is_staff=True, is_superuser=False
        )

        cls.azanulbizar = mommy.make(
            models.Station, name="Azanulbizar", creator=bob, maintainers=[]
        )
        cls.barazinbar = mommy.make(
            models.Station, name="Barazinbar", creator=bob, maintainers=[charlie]
        )
        cls.calenardhon = mommy.make(
            models.Station, name="Calenardhon", creator=alice, maintainers=[]
        )

        po = Permission.objects
        elaine.user_permissions.add(po.get(codename="add_station"))
        elaine.user_permissions.add(po.get(codename="change_station"))
        elaine.user_permissions.add(po.get(codename="delete_station"))


class CommonTests:
    """Tests that will run both for ENHYDRIS_USERS_CAN_ADD_CONTENT=True and False.

    Below we have two TestCase subclasses (actually StationPermissionsTestCaseBase
    subclasses); one of them overrides setting ENHYDRIS_USERS_CAN_ADD_CONTENT to True,
    and the other one to False. This is a mixin containing tests that should have the
    same results in both cases.
    """

    def test_station_list_has_all_stations_for_superuser(self):
        self.client.login(username="alice", password="topsecret")
        response = self.client.get("/admin/enhydris/station/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Azanulbizar")
        self.assertContains(response, "Barazinbar")
        self.assertContains(response, "Calenardhon")

    def test_station_list_has_all_stations_for_user_with_model_permissions(self):
        self.client.login(username="elaine", password="topsecret")
        response = self.client.get("/admin/enhydris/station/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Azanulbizar")
        self.assertContains(response, "Barazinbar")
        self.assertContains(response, "Calenardhon")

    def test_station_list_has_nothing_when_user_does_not_have_permissions(self):
        self.client.login(username="david", password="topsecret")
        response = self.client.get("/admin/enhydris/station/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Azanulbizar")
        self.assertNotContains(response, "Barazinbar")
        self.assertNotContains(response, "Calenardhon")

    def test_station_detail_is_inaccessible_if_user_does_not_have_perms(self):
        self.client.login(username="david", password="topsecret")
        response = self.client.get(
            "/admin/enhydris/station/{}/change/".format(self.barazinbar.id)
        )
        self.assertEqual(response.status_code, 302)


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class StationPermsTestCaseWhenUsersCanAddContent(StationPermsTestCaseBase, CommonTests):
    def test_station_list_has_created_stations(self):
        self.client.login(username="bob", password="topsecret")
        response = self.client.get("/admin/enhydris/station/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Azanulbizar")
        self.assertContains(response, "Barazinbar")
        self.assertNotContains(response, "Calenardhon")

    def test_station_list_has_maintained_stations(self):
        self.client.login(username="charlie", password="topsecret")
        response = self.client.get("/admin/enhydris/station/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Azanulbizar")
        self.assertContains(response, "Barazinbar")
        self.assertNotContains(response, "Calenardhon")

    def test_station_detail_has_creator_and_maintainers_for_superuser(self):
        self.client.login(username="alice", password="topsecret")
        response = self.client.get(
            "/admin/enhydris/station/{}/change/".format(self.azanulbizar.id)
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Creator")
        self.assertContains(response, "Maintainers")

    def test_station_detail_has_creator_and_maintainers_for_user_with_model_perms(self):
        self.client.login(username="elaine", password="topsecret")
        response = self.client.get(
            "/admin/enhydris/station/{}/change/".format(self.azanulbizar.id)
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Creator")
        self.assertContains(response, "Maintainers")

    def test_station_detail_has_only_maintainers_for_creator(self):
        self.client.login(username="bob", password="topsecret")
        response = self.client.get(
            "/admin/enhydris/station/{}/change/".format(self.azanulbizar.id)
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Creator")
        self.assertContains(response, "Maintainers")

    def test_station_detail_has_neither_creator_nor_maintainers_for_maintainer(self):
        self.client.login(username="charlie", password="topsecret")
        response = self.client.get(
            "/admin/enhydris/station/{}/change/".format(self.barazinbar.id)
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Creator")
        self.assertNotContains(response, "Maintainers")

    def test_add_station_has_creator_and_maintainers_for_superuser(self):
        self.client.login(username="alice", password="topsecret")
        response = self.client.get("/admin/enhydris/station/add/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Creator")
        self.assertContains(response, "Maintainers")

    def test_add_station_has_creator_and_maintainers_for_user_with_model_perms(self):
        self.client.login(username="elaine", password="topsecret")
        response = self.client.get("/admin/enhydris/station/add/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Creator")
        self.assertContains(response, "Maintainers")

    def test_add_station_has_only_maintainers_for_user_without_model_perms(self):
        self.client.login(username="bob", password="topsecret")
        response = self.client.get("/admin/enhydris/station/add/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Creator")
        self.assertContains(response, "Maintainers")


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=False)
class StationPermsTestCaseWhenUsersCannotAddCont(StationPermsTestCaseBase, CommonTests):
    def test_station_list_is_empty_even_if_user_is_creator(self):
        self.client.login(username="bob", password="topsecret")
        response = self.client.get("/admin/enhydris/station/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Azanulbizar")
        self.assertNotContains(response, "Barazinbar")
        self.assertNotContains(response, "Calenardhon")

    def test_station_list_is_empty_even_if_user_is_maintainer(self):
        self.client.login(username="charlie", password="topsecret")
        response = self.client.get("/admin/enhydris/station/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Azanulbizar")
        self.assertNotContains(response, "Barazinbar")
        self.assertNotContains(response, "Calenardhon")

    def test_station_detail_does_not_have_creator_and_maintainers(self):
        self.client.login(username="elaine", password="topsecret")
        response = self.client.get(
            "/admin/enhydris/station/{}/change/".format(self.azanulbizar.id)
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Creator")
        self.assertNotContains(response, "Maintainers")

    def test_add_station_has_no_creator_or_maintainers_for_user_with_model_perms(self):
        self.client.login(username="elaine", password="topsecret")
        response = self.client.get("/admin/enhydris/station/add/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Creator")
        self.assertNotContains(response, "Maintainers")


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class StationCreateSetsCreatorTestCase(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(
            username="alice", password="topsecret", is_staff=True, is_superuser=True
        )
        self.bob = User.objects.create_user(
            username="bob", password="topsecret", is_staff=True, is_superuser=False
        )
        self.serial_killers_sa = models.Organization.objects.create(
            name="Serial killers SA"
        )

    def test_when_creating_station_creator_is_set(self):
        self.client.login(username="bob", password="topsecret")
        response = self.client.post(
            "/admin/enhydris/station/add/",
            {
                "name": "Hobbiton",
                "copyright_years": "2018",
                "copyright_holder": "Bilbo Baggins",
                "owner": self.serial_killers_sa.id,
                "geometry_0": "20.94565",
                "geometry_1": "39.12102",
                "instrument_set-TOTAL_FORMS": "0",
                "instrument_set-INITIAL_FORMS": "0",
                "gentityfile_set-TOTAL_FORMS": "0",
                "gentityfile_set-INITIAL_FORMS": "0",
                "gentityevent_set-TOTAL_FORMS": "0",
                "gentityevent_set-INITIAL_FORMS": "0",
                "timeseries-TOTAL_FORMS": "0",
                "timeseries-INITIAL_FORMS": "0",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(models.Station.objects.first().creator, self.bob)


class TimeseriesInlineAdminFormRefusesToAppendIfNotInOrderTestCase(TestCase):
    def setUp(self):
        station = mommy.make(models.Station)
        self.timeseries = mommy.make(
            models.Timeseries, gentity=station, time_zone__utc_offset=0, precision=2
        )
        self.timeseries.set_data(
            StringIO("2005-11-01 18:00,3,\n2019-01-01 00:30,25,\n")
        )
        self.data = {
            "replace_or_append": "APPEND",
            "gentity": station.id,
            "unit_of_measurement": self.timeseries.unit_of_measurement.id,
            "variable": self.timeseries.variable.id,
            "time_zone": self.timeseries.time_zone.id,
            "precision": 2,
        }
        self.files = {
            "data": SimpleUploadedFile(
                "mytimeseries.csv", b"2005-12-01 18:35,7,\n2019-04-09 13:36,0,\n"
            )
        }
        self.form = TimeseriesInlineAdminForm(
            data=self.data, files=self.files, instance=self.timeseries
        )

    def test_form_is_not_valid(self):
        self.assertFalse(self.form.is_valid())

    def test_form_errors(self):
        self.assertIn(
            "the first record of the time series to append is earlier than the last "
            "record of the existing time series",
            self.form.errors["__all__"][0],
        )


class TimeseriesInlineAdminFormAcceptsAppendingIfInOrderTestCase(TestCase):
    def setUp(self):
        station = mommy.make(models.Station)
        self.timeseries = mommy.make(
            models.Timeseries,
            gentity=station,
            time_zone__utc_offset=0,
            variable__descr="irrelevant",
            precision=2,
        )
        self.timeseries.set_data(StringIO("2019-01-01 00:30,25,\n"))
        self.data = {
            "replace_or_append": "APPEND",
            "gentity": station.id,
            "unit_of_measurement": self.timeseries.unit_of_measurement.id,
            "variable": self.timeseries.variable.id,
            "time_zone": self.timeseries.time_zone.id,
            "precision": 2,
        }
        self.files = {
            "data": SimpleUploadedFile("mytimeseries.csv", b"2019-04-09 13:36,0,\n")
        }
        self.form = TimeseriesInlineAdminForm(
            data=self.data, files=self.files, instance=self.timeseries
        )
        self.form.save()

    def test_form_is_valid(self):
        self.assertTrue(self.form.is_valid())

    def test_data_length(self):
        self.assertEqual(len(self.timeseries.get_data().data), 2)

    def test_first_record(self):
        self.assertEqual(
            self.timeseries.get_data().data.index[0], dt.datetime(2019, 1, 1, 0, 30)
        )

    def test_second_record(self):
        self.assertEqual(
            self.timeseries.get_data().data.index[1], dt.datetime(2019, 4, 9, 13, 36)
        )


class TimeseriesInlineAdminFormAcceptsReplacingTestCase(TestCase):
    def setUp(self):
        station = mommy.make(models.Station)
        self.timeseries = mommy.make(
            models.Timeseries,
            gentity=station,
            time_zone__utc_offset=0,
            variable__descr="irrelevant",
            precision=2,
        )
        self.timeseries.set_data(StringIO("2019-01-01 00:30,25,\n"))
        self.data = {
            "replace_or_append": "REPLACE",
            "gentity": station.id,
            "unit_of_measurement": self.timeseries.unit_of_measurement.id,
            "variable": self.timeseries.variable.id,
            "time_zone": self.timeseries.time_zone.id,
            "precision": 2,
        }
        self.files = {
            "data": SimpleUploadedFile(
                "mytimeseries.csv", b"2005-12-01 18:35,7,\n2019-04-09 13:36,0,\n"
            )
        }
        self.form = TimeseriesInlineAdminForm(
            data=self.data, files=self.files, instance=self.timeseries
        )
        self.form.save()

    def test_form_is_valid(self):
        self.assertTrue(self.form.is_valid())

    def test_data_length(self):
        self.assertEqual(len(self.timeseries.get_data().data), 2)

    def test_first_record(self):
        self.assertEqual(
            self.timeseries.get_data().data.index[0], dt.datetime(2005, 12, 1, 18, 35)
        )

    def test_second_record(self):
        self.assertEqual(
            self.timeseries.get_data().data.index[1], dt.datetime(2019, 4, 9, 13, 36)
        )


class TimeseriesInlineAdminFormTimeStepNullTestCase(TestCase):
    def setUp(self):
        station = mommy.make(models.Station)
        self.timeseries = mommy.make(
            models.Timeseries, gentity=station, time_zone__utc_offset=0, precision=2
        )
        self.data = {
            "gentity": station.id,
            "unit_of_measurement": self.timeseries.unit_of_measurement.id,
            "variable": self.timeseries.variable.id,
            "time_zone": self.timeseries.time_zone.id,
            "precision": 2,
        }

    def test_form_is_not_valid_when_rounding_months_not_null(self):
        self.data["timestamp_rounding_months"] = 0
        self.form = TimeseriesInlineAdminForm(data=self.data, instance=self.timeseries)
        self.assertFalse(self.form.is_valid())

    def test_form_is_not_valid_when_rounding_minutes_not_null(self):
        self.data["timestamp_rounding_minutes"] = 0
        self.form = TimeseriesInlineAdminForm(data=self.data, instance=self.timeseries)
        self.assertFalse(self.form.is_valid())

    def test_form_is_not_valid_when_offset_months_not_null(self):
        self.data["timestamp_offset_months"] = 0
        self.form = TimeseriesInlineAdminForm(data=self.data, instance=self.timeseries)
        self.assertFalse(self.form.is_valid())

    def test_form_is_not_valid_when_offset_minutes_not_null(self):
        self.data["timestamp_offset_minutes"] = 0
        self.form = TimeseriesInlineAdminForm(data=self.data, instance=self.timeseries)
        self.assertFalse(self.form.is_valid())

    def test_form_is_valid_when_all_null(self):
        self.form = TimeseriesInlineAdminForm(data=self.data, instance=self.timeseries)
        self.assertTrue(self.form.is_valid())


class TimeseriesInlineAdminFormTimeStepNotNullTestCase(TestCase):
    def setUp(self):
        station = mommy.make(models.Station)
        self.timeseries = mommy.make(
            models.Timeseries, gentity=station, time_zone__utc_offset=0, precision=2
        )
        self.time_step = mommy.make(models.TimeStep, length_minutes=1, length_months=0)
        self.data = {
            "gentity": station.id,
            "unit_of_measurement": self.timeseries.unit_of_measurement.id,
            "variable": self.timeseries.variable.id,
            "time_zone": self.timeseries.time_zone.id,
            "time_step": self.time_step.id,
            "timestamp_offset_months": 0,
            "timestamp_offset_minutes": 0,
            "precision": 2,
        }

    def test_form_is_not_valid_when_offset_months_null_and_timestep_not_null(self):
        self.data["timestamp_offset_months"] = None
        self.form = TimeseriesInlineAdminForm(data=self.data, instance=self.timeseries)
        self.assertFalse(self.form.is_valid())

    def test_form_is_not_valid_when_offset_minutes_null_and_timestep_not_null(self):
        self.data["timestamp_offset_minutes"] = None
        self.form = TimeseriesInlineAdminForm(data=self.data, instance=self.timeseries)
        self.assertFalse(self.form.is_valid())

    def test_form_is_valid_when_offset_not_null_and_timestep_not_null(self):
        self.form = TimeseriesInlineAdminForm(data=self.data, instance=self.timeseries)
        self.assertTrue(self.form.is_valid())

    def test_form_is_invalid_when_rounding_mins_null_and_rounding_months_not_null(self):
        self.data["timestamp_rounding_minutes"] = None
        self.data["timestamp_rounding_months"] = 0
        self.form = TimeseriesInlineAdminForm(data=self.data, instance=self.timeseries)
        self.assertFalse(self.form.is_valid())

    def test_form_is_invalid_when_rounding_months_null_and_rounding_mins_not_null(self):
        self.data["timestamp_rounding_minutes"] = 0
        self.data["timestamp_rounding_months"] = None
        self.form = TimeseriesInlineAdminForm(data=self.data, instance=self.timeseries)
        self.assertFalse(self.form.is_valid())

    def test_form_is_valid_when_roundings_are_both_null(self):
        self.data["timestamp_rounding_minutes"] = None
        self.data["timestamp_rounding_months"] = None
        self.form = TimeseriesInlineAdminForm(data=self.data, instance=self.timeseries)
        self.assertTrue(self.form.is_valid())

    def test_form_is_valid_when_roundings_are_both_not_null(self):
        self.data["timestamp_rounding_minutes"] = 0
        self.data["timestamp_rounding_months"] = 0
        self.form = TimeseriesInlineAdminForm(data=self.data, instance=self.timeseries)
        self.assertTrue(self.form.is_valid())


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
@RandomEnhydrisTimeseriesDataDir()
class TimeseriesUploadFileTestCase(TestCase):
    def setUp(self):
        self.data = self._get_basic_form_contents()
        self.alice = User.objects.create_user(
            username="alice", password="topsecret", is_staff=True, is_superuser=False
        )
        self.client.login(username="alice", password="topsecret")
        with StringIO("Precision=2\n\n2019-08-18 12:39,0.12345678901234,\n") as f:
            self.data["timeseries-0-data"] = f
            self.response = self.client.post("/admin/enhydris/station/add/", self.data)

    def _get_basic_form_contents(self):
        return {
            "name": "Hobbiton",
            "copyright_years": "2018",
            "copyright_holder": "Bilbo Baggins",
            "owner": models.Organization.objects.create(name="Serial killers SA").id,
            "geometry_0": "20.94565",
            "geometry_1": "39.12102",
            "instrument_set-TOTAL_FORMS": "0",
            "instrument_set-INITIAL_FORMS": "0",
            "gentityfile_set-TOTAL_FORMS": "0",
            "gentityfile_set-INITIAL_FORMS": "0",
            "gentityevent_set-TOTAL_FORMS": "0",
            "gentityevent_set-INITIAL_FORMS": "0",
            "timeseries-TOTAL_FORMS": "1",
            "timeseries-INITIAL_FORMS": "0",
            "timeseries-0-variable": mommy.make(models.Variable).id,
            "timeseries-0-unit_of_measurement": mommy.make(models.UnitOfMeasurement).id,
            "timeseries-0-precision": 2,
            "timeseries-0-time_zone": mommy.make(
                models.TimeZone, code="EET", utc_offset=120
            ).id,
            "timeseries-0-replace_or_append": "APPEND",
        }

    def test_response(self):
        self.assertEqual(self.response.status_code, 302)

    def test_data_was_saved_with_full_precision(self):
        # Although the time series has a specified precision of 2, we want it to store
        # all the decimal digits to avoid losing data when the user makes an error when
        # entering the precision.
        filename = glob(os.path.join(settings.ENHYDRIS_TIMESERIES_DATA_DIR, "*"))[0]
        with open(filename) as f:
            contents = f.read()
        value = float(contents.split(",")[1])
        self.assertAlmostEqual(value, 0.12345678901234)

    def test_data_is_appended_with_full_precision(self):
        station = models.Station.objects.first()
        timeseries = models.Timeseries.objects.first()
        self.client.login(username="alice", password="topsecret")
        self.data["timeseries-0-id"] = timeseries.id
        self.data["timeseries-0-gentity"] = station.id
        self.data["timeseries-INITIAL_FORMS"] = "1"
        with StringIO("Precision=2\n\n2019-08-19 12:39,3.14159065358979,\n") as f:
            self.data["timeseries-0-data"] = f
            self.client.post(
                "/admin/enhydris/station/{}/change/".format(station.id), self.data
            )
        filename = glob(os.path.join(settings.ENHYDRIS_TIMESERIES_DATA_DIR, "*"))[0]
        with open(filename) as f:
            values = [float(line.split(",")[1]) for line in f]
        self.assertAlmostEqual(values[0], 0.12345678901234)
        self.assertAlmostEqual(values[1], 3.14159065358979)


class TimeseriesUploadFileWithUnicodeHeadersTestCase(TestCase):
    def setUp(self):
        station = mommy.make(models.Station)
        self.timeseries = mommy.make(
            models.Timeseries,
            gentity=station,
            time_zone__utc_offset=0,
            variable__descr="irrelevant",
            precision=2,
        )
        self.data = {
            "replace_or_append": "REPLACE",
            "gentity": station.id,
            "unit_of_measurement": self.timeseries.unit_of_measurement.id,
            "variable": self.timeseries.variable.id,
            "time_zone": self.timeseries.time_zone.id,
            "precision": 2,
        }
        self.files = {
            "data": SimpleUploadedFile(
                "mytimeseries.csv",
                "Station=Πάπιγκο\n\n2019-04-09 13:36,0,\n".encode("utf-8"),
            )
        }
        try:
            # We check that the file is read without problem even if the locale
            # is set to C (i.e. ascii only)
            saved_locale = getlocale(LC_CTYPE)
            setlocale(LC_CTYPE, "C")
            self.form = TimeseriesInlineAdminForm(
                data=self.data, files=self.files, instance=self.timeseries
            )
            self.form.save()
        finally:
            setlocale(LC_CTYPE, saved_locale)

    def test_form_is_valid(self):
        self.assertTrue(self.form.is_valid())

    def test_data_length(self):
        self.assertEqual(len(self.timeseries.get_data().data), 1)

    def test_first_record(self):
        self.assertEqual(
            self.timeseries.get_data().data.index[0], dt.datetime(2019, 4, 9, 13, 36)
        )


class TimeseriesUploadInvalidFileTestCase(TestCase):
    def setUp(self):
        station = mommy.make(models.Station)
        self.timeseries = mommy.make(
            models.Timeseries,
            gentity=station,
            time_zone__utc_offset=0,
            variable__descr="irrelevant",
            precision=2,
        )
        self.data = {
            "replace_or_append": "REPLACE",
            "gentity": station.id,
            "unit_of_measurement": self.timeseries.unit_of_measurement.id,
            "variable": self.timeseries.variable.id,
            "time_zone": self.timeseries.time_zone.id,
            "precision": 2,
        }
        self.files = {"data": SimpleUploadedFile("mytimeseries.csv", b"\xbc\xbd")}
        self.form = TimeseriesInlineAdminForm(
            data=self.data, files=self.files, instance=self.timeseries
        )

    def test_form_is_invalid(self):
        self.assertFalse(self.form.is_valid())


class TimeseriesInlineAdminFormProcessWithoutFileTestCase(TestCase):
    def setUp(self):
        station = mommy.make(models.Station)
        self.timeseries = mommy.make(
            models.Timeseries, gentity=station, time_zone__utc_offset=0, precision=2
        )
        self.timeseries.set_data(StringIO("2019-01-01 00:30,25,\n"))
        self.data = {
            "replace_or_append": "REPLACE",
            "gentity": station.id,
            "unit_of_measurement": self.timeseries.unit_of_measurement.id,
            "variable": self.timeseries.variable.id,
            "time_zone": self.timeseries.time_zone.id,
            "precision": 2,
        }
        self.form = TimeseriesInlineAdminForm(data=self.data, instance=self.timeseries)

    def test_form_is_valid(self):
        self.assertTrue(self.form.is_valid())

    def test_form_saves_and_returns_object(self):
        timeseries = self.form.save()
        self.assertEqual(timeseries.id, self.timeseries.id)
