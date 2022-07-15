import os
from io import StringIO
from locale import LC_CTYPE, getlocale, setlocale
from unittest import mock

from django.contrib.auth.models import Permission, User
from django.contrib.messages import get_messages
from django.contrib.messages.storage.cookie import CookieStorage
from django.contrib.sites.models import Site
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.http import HttpRequest
from django.test import TestCase, override_settings

from crequest.middleware import CrequestMiddleware
from model_mommy import mommy

from enhydris import models
from enhydris.admin.station import TimeseriesInlineAdminForm
from enhydris.tests import TestTimeseriesMixin
from enhydris.tests.admin import get_formset_parameters


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
        elaine.user_permissions.add(
            po.get(content_type__app_label="enhydris", codename="add_station")
        )
        elaine.user_permissions.add(
            po.get(content_type__app_label="enhydris", codename="change_station")
        )
        elaine.user_permissions.add(
            po.get(content_type__app_label="enhydris", codename="delete_station")
        )


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
        self.assertContains(response, "Administrator")
        self.assertContains(response, "Maintainers")

    def test_station_detail_has_creator_and_maintainers_for_user_with_model_perms(self):
        self.client.login(username="elaine", password="topsecret")
        response = self.client.get(
            "/admin/enhydris/station/{}/change/".format(self.azanulbizar.id)
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Administrator")
        self.assertContains(response, "Maintainers")

    def test_station_detail_has_only_maintainers_for_creator(self):
        self.client.login(username="bob", password="topsecret")
        response = self.client.get(
            "/admin/enhydris/station/{}/change/".format(self.azanulbizar.id)
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Administrator")
        self.assertContains(response, "Maintainers")

    def test_station_detail_has_neither_creator_nor_maintainers_for_maintainer(self):
        self.client.login(username="charlie", password="topsecret")
        response = self.client.get(
            "/admin/enhydris/station/{}/change/".format(self.barazinbar.id)
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Administrator")
        self.assertNotContains(response, "Maintainers")

    def test_add_station_has_creator_and_maintainers_for_superuser(self):
        self.client.login(username="alice", password="topsecret")
        response = self.client.get("/admin/enhydris/station/add/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Administrator")
        self.assertContains(response, "Maintainers")

    def test_add_station_has_creator_and_maintainers_for_user_with_model_perms(self):
        self.client.login(username="elaine", password="topsecret")
        response = self.client.get("/admin/enhydris/station/add/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Administrator")
        self.assertContains(response, "Maintainers")

    def test_add_station_has_only_maintainers_for_user_without_model_perms(self):
        self.client.login(username="bob", password="topsecret")
        response = self.client.get("/admin/enhydris/station/add/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Administrator")
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
        self.assertNotContains(response, "Administrator")
        self.assertNotContains(response, "Maintainers")

    def test_add_station_has_no_creator_or_maintainers_for_user_with_model_perms(self):
        self.client.login(username="elaine", password="topsecret")
        response = self.client.get("/admin/enhydris/station/add/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Administrator")
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
                "owner": self.serial_killers_sa.id,
                "geom_0": "20.94565",
                "geom_1": "39.12102",
                **get_formset_parameters(self.client, "/admin/enhydris/station/add/"),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(models.Station.objects.first().creator, self.bob)


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
@override_settings(SITE_ID=1)
class StationChangeSites(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.site1 = mommy.make(Site, id=1, domain="hello.com", name="hello")
        cls.site2 = mommy.make(Site, id=2, domain="world.com", name="world")

        cls.alice = User.objects.create_user(
            username="alice", password="topsecret", is_staff=True, is_superuser=True
        )
        cls.bob = User.objects.create_user(
            username="bob", password="topsecret", is_staff=True, is_superuser=False
        )

        cls.station = mommy.make(models.Station, creator=cls.bob, sites=[cls.site1])

    def get_response(self):
        return self.client.get(
            "/admin/enhydris/station/{}/change/".format(self.station.id)
        )

    def test_normal_user_cannot_change_sites(self):
        self.client.login(username="bob", password="topsecret")
        response = self.get_response()
        self.assertNotContains(response, "id_sites")

    def test_administrator_can_change_sites(self):
        self.client.login(username="alice", password="topsecret")
        response = self.get_response()
        self.assertContains(response, "id_sites")

    def test_administrator_cannot_change_sites_when_there_is_only_one_site(self):
        self.site2.delete()
        self.client.login(username="alice", password="topsecret")
        response = self.get_response()
        self.assertNotContains(response, "id_sites")

    def test_cannot_change_sites_when_creating(self):
        self.client.login(username="alice", password="topsecret")
        response = self.client.get("/admin/enhydris/station/add/")
        self.assertNotContains(response, "id_sites")


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
@override_settings(SITE_ID=1)
class StationListFromDifferentSites(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.site1 = mommy.make(Site, id=1, domain="hello.com", name="hello")
        cls.site2 = mommy.make(Site, id=2, domain="world.com", name="world")

        cls.alice = User.objects.create_user(
            username="alice", password="topsecret", is_staff=True, is_superuser=True
        )
        cls.bob = User.objects.create_user(
            username="bob", password="topsecret", is_staff=True, is_superuser=False
        )

        cls.station1 = mommy.make(
            models.Station, id=42, name="hello station", creator=cls.bob
        )
        cls.station2 = mommy.make(
            models.Station, id=43, name="world station", creator=cls.bob
        )
        cls.station2.sites.set({cls.site2})

    def test_bob_can_view_station1_in_list(self):
        self.client.login(username="bob", password="topsecret")
        response = self.client.get("/admin/enhydris/station/")
        self.assertContains(response, "hello station")

    def test_bob_cannot_view_station2_in_list(self):
        self.client.login(username="bob", password="topsecret")
        response = self.client.get("/admin/enhydris/station/")
        self.assertNotContains(response, "world station")

    def test_alice_can_view_station2_in_list(self):
        self.client.login(username="alice", password="topsecret")
        response = self.client.get("/admin/enhydris/station/")
        self.assertContains(response, "world station")

    def test_bob_can_view_station1_detail(self):
        self.client.login(username="bob", password="topsecret")
        response = self.client.get("/admin/enhydris/station/42/change/")
        self.assertEqual(response.status_code, 200)

    def test_bob_cannot_view_station2_detail(self):
        self.client.login(username="bob", password="topsecret")
        response = self.client.get("/admin/enhydris/station/43/change/")
        self.assertEqual(response.status_code, 302)
        msg = str(list(get_messages(response.wsgi_request))[0])
        self.assertIn("Station with ID “43” doesn’t exist.", msg)

    def test_alice_can_view_station2_detail(self):
        self.client.login(username="alice", password="topsecret")
        response = self.client.get("/admin/enhydris/station/43/change/")
        self.assertEqual(response.status_code, 200)

    def test_alice_has_a_by_site_list_filter(self):
        self.client.login(username="alice", password="topsecret")
        response = self.client.get("/admin/enhydris/station/")
        self.assertContains(response, "By Site")

    def test_bob_does_not_have_a_by_site_list_filter(self):
        self.client.login(username="bob", password="topsecret")
        response = self.client.get("/admin/enhydris/station/")
        self.assertNotContains(response, "By Site")


class TestTimeseriesFormMixin(TestTimeseriesMixin):
    def _create_timeseries_inline_admin_form(self, replace_or_append, file_contents=""):
        self.data = {
            "replace_or_append": replace_or_append,
            "timeseries_group": self.timeseries_group.id,
            "type": models.Timeseries.INITIAL,
        }
        if file_contents:
            self.files = {
                "data": TemporaryUploadedFile(
                    "mytimeseries.csv",
                    "text/plain",
                    size=len(file_contents),
                    charset="utf8",
                )
            }
            self.files["data"].write(file_contents)
            self.files["data"].seek(0)
        else:
            self.files = None
        self.form = TimeseriesInlineAdminForm(
            data=self.data, files=self.files, instance=self.timeseries
        )

    def _setup_request_object(self):
        self.request = HttpRequest()
        self.request.user = User.objects.create_user(
            username="alice", email="alice@example.com"
        )
        self.request._messages = CookieStorage(self.request)
        CrequestMiddleware.set_request(self.request)

    def _teardown_request_object(self):
        CrequestMiddleware.del_request()

    def _delete_temporary_file(self):
        if self.files:
            os.remove(self.files["data"].temporary_file_path())


class TimeseriesInlineAdminFormRefusesToAppendIfNotInOrderTestCase(
    TestTimeseriesFormMixin, TestCase
):
    def setUp(self):
        self._setup_request_object()
        self._create_test_timeseries(data="2005-11-01 18:00,3,\n2019-01-01 00:30,25,\n")
        self._create_timeseries_inline_admin_form(
            "APPEND", b"2005-12-01 18:35,7,\n2019-04-09 13:36,0,\n"
        )

    def tearDown(self):
        self._teardown_request_object()

    def test_form_is_not_valid(self):
        self.assertFalse(self.form.is_valid())

    def test_form_errors(self):
        self.assertIn(
            "the first record of the time series to append is earlier than the last "
            "record of the existing time series",
            self.form.errors["__all__"][0],
        )


class TimeseriesInlineAdminFormAcceptsAppendingIfInOrderTestCase(
    TestTimeseriesFormMixin, TestCase
):
    def setUp(self):
        self._create_test_timeseries(data="2019-01-01 00:30,25,\n")
        self._create_timeseries_inline_admin_form("APPEND", b"2019-04-09 13:36,0,\n")

    def test_form_is_valid(self):
        self.assertTrue(self.form.is_valid())


class TimeseriesInlineAdminFormAcceptsReplacingTestCase(
    TestTimeseriesFormMixin, TestCase
):
    def setUp(self):
        self._create_test_timeseries(data="2019-01-01 00:30,25,\n")
        self._create_timeseries_inline_admin_form(
            "REPLACE", b"2005-12-01 18:35,7,\n2019-04-09 13:36,0,\n"
        )

    def test_form_is_valid(self):
        self.assertTrue(self.form.is_valid())


class TimeseriesUploadFileMixin:
    def _get_basic_form_contents(self):
        return {
            "name": "Hobbiton",
            "owner": models.Organization.objects.create(name="Serial killers SA").id,
            "geom_0": "20.94565",
            "geom_1": "39.12102",
            **get_formset_parameters(self.client, "/admin/enhydris/station/add/"),
            "timeseriesgroup_set-TOTAL_FORMS": "1",
            "timeseriesgroup_set-INITIAL_FORMS": "0",
            "timeseriesgroup_set-0-variable": mommy.make(
                models.Variable, descr="myvar"
            ).id,
            "timeseriesgroup_set-0-unit_of_measurement": mommy.make(
                models.UnitOfMeasurement
            ).id,
            "timeseriesgroup_set-0-precision": 2,
            "timeseriesgroup_set-0-time_zone": mommy.make(
                models.TimeZone, code="EET", utc_offset=120
            ).id,
            "timeseriesgroup_set-0-timeseries_set-TOTAL_FORMS": "1",
            "timeseriesgroup_set-0-timeseries_set-INITIAL_FORMS": "0",
            "timeseriesgroup_set-0-timeseries_set-0-type": "100",
            "timeseriesgroup_set-0-timeseries_set-0-replace_or_append": "APPEND",
        }


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class TimeseriesUploadFileTestCase(TestCase, TimeseriesUploadFileMixin):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(
            username="alice", password="topsecret", is_staff=True, is_superuser=False
        )

    @mock.patch("enhydris.admin.station.tasks.save_timeseries_data")
    def setUp(self, m):
        self.mock_save_timeseries_data = m
        self.client.login(username="alice", password="topsecret")
        self.data = self._get_basic_form_contents()
        with StringIO("Precision=2\n\n2019-08-18 12:39,0.12345678901234,\n") as f:
            self.data["timeseriesgroup_set-0-timeseries_set-0-data"] = f
            self.response = self.client.post("/admin/enhydris/station/add/", self.data)

    def tearDown(self):
        filename = self.mock_save_timeseries_data.delay.call_args[1]["datafilename"]
        os.remove(filename)

    def test_response(self):
        self.assertEqual(self.response.status_code, 302)

    def test_calls_save_timeseries_data(self):
        self.mock_save_timeseries_data.delay.assert_called_once()

    def test_requests_append(self):
        self.assertEqual(
            self.mock_save_timeseries_data.delay.call_args[1]["replace_or_append"],
            "APPEND",
        )

    def test_passes_correct_username(self):
        self.assertEqual(
            self.mock_save_timeseries_data.delay.call_args[1]["username"], "alice"
        )

    def test_passes_correct_timeseries_id(self):
        self.assertEqual(
            self.mock_save_timeseries_data.delay.call_args[1]["id"],
            models.Timeseries.objects.get().id,
        )

    def test_passes_correct_file(self):
        filename = self.mock_save_timeseries_data.delay.call_args[1]["datafilename"]
        with open(filename) as f:
            file_contents = f.read()
        self.assertEqual(
            file_contents, "Precision=2\n\n2019-08-18 12:39,0.12345678901234,\n"
        )

    def test_message(self):
        response = self.client.get(self.response.url)  # Follow the redirect
        self.assertContains(
            response,
            (
                "The data for the time series &quot;Hobbiton - myvar - Initial&quot; "
                "will be imported soon. You will be notified by email when the "
                "importing finishes."
            ),
        )


class TimeseriesUploadFileWithUnicodeHeadersTestCase(TestTimeseriesFormMixin, TestCase):
    def setUp(self):
        self._create_test_timeseries()
        try:
            # We check that the file is read without problem even if the locale
            # is set to C (i.e. ascii only)
            saved_locale = getlocale(LC_CTYPE)
            setlocale(LC_CTYPE, "C")
            self._create_timeseries_inline_admin_form(
                "REPLACE", "Station=Πάπιγκο\n\n2019-04-09 13:36,0,\n".encode("utf-8")
            )
        finally:
            setlocale(LC_CTYPE, saved_locale)

    def test_form_is_valid(self):
        self.assertTrue(self.form.is_valid())


class TimeseriesUploadInvalidFileTestCase(TestTimeseriesFormMixin, TestCase):
    def setUp(self):
        self._create_test_timeseries()

    def test_file_starting_with_garbage(self):
        self._create_timeseries_inline_admin_form("REPLACE", b"\xbc\xbd")
        self.assertFalse(self.form.is_valid())

    def test_file_with_wrong_header(self):
        self._create_timeseries_inline_admin_form("REPLACE", b"hello\n")
        self.assertFalse(self.form.is_valid())

    def test_file_not_ending_in_line_feed(self):
        self._create_timeseries_inline_admin_form("REPLACE", b"2020-01-28 18:28,7,")
        self.assertFalse(self.form.is_valid())

    def test_file_not_having_enough_columns(self):
        self._create_timeseries_inline_admin_form("REPLACE", b"2020-01-28 18:28\n")
        self.assertFalse(self.form.is_valid())

    def test_file_with_multiple_timestamps(self):
        self._create_timeseries_inline_admin_form(
            "REPLACE", b"2020-01-28 18:28,7,\n2020-01-28 18:28,8,\n"
        )
        self.assertFalse(self.form.is_valid())


class TimeseriesUploadAppendWithOverlapTestCase(TestTimeseriesFormMixin, TestCase):
    def setUp(self):
        self._create_test_timeseries(data="2005-11-01 18:00,3,\n2019-01-01 00:30,25,\n")

    def test_append_badly_ordered_file_that_overlaps(self):
        self._create_timeseries_inline_admin_form(
            "APPEND", b"2019-01-02 00:30,42,\n2019-01-01 00:30,42,\n"
        )
        self.assertFalse(self.form.is_valid())


class TimeseriesInlineAdminFormProcessWithoutFileTestCase(
    TestTimeseriesFormMixin, TestCase
):
    def setUp(self):
        self._setup_request_object()
        self._create_test_timeseries(data="2019-01-01 00:30,25,\n")
        self._create_timeseries_inline_admin_form("REPLACE")

    def tearDown(self):
        self._teardown_request_object()
        self._delete_temporary_file()

    def test_form_is_valid(self):
        self.assertTrue(self.form.is_valid())

    def test_form_saves_and_returns_object(self):
        timeseries = self.form.save()
        self.assertEqual(timeseries.id, self.timeseries.id)


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class TimeseriesInlineFormSetTestCase(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(
            username="alice", password="topsecret", is_staff=True, is_superuser=False
        )
        self.client.login(username="alice", password="topsecret")

    def _get_basic_form_contents(self):
        return {
            "name": "Hobbiton",
            "owner": models.Organization.objects.create(name="Serial killers SA").id,
            "geom_0": "20.94565",
            "geom_1": "39.12102",
            **get_formset_parameters(self.client, "/admin/enhydris/station/add/"),
            "timeseriesgroup_set-TOTAL_FORMS": "1",
            "timeseriesgroup_set-INITIAL_FORMS": "0",
            "timeseriesgroup_set-0-variable": mommy.make(
                models.Variable, descr="myvar"
            ).id,
            "timeseriesgroup_set-0-unit_of_measurement": mommy.make(
                models.UnitOfMeasurement
            ).id,
            "timeseriesgroup_set-0-precision": 2,
            "timeseriesgroup_set-0-time_zone": mommy.make(
                models.TimeZone, code="EET", utc_offset=120
            ).id,
            "timeseriesgroup_set-0-timeseries_set-INITIAL_FORMS": "0",
        }

    def test_checks_unique_key(self):
        data = {
            **self._get_basic_form_contents(),
            "timeseriesgroup_set-0-timeseries_set-TOTAL_FORMS": "2",
            "timeseriesgroup_set-0-timeseries_set-0-type": "100",
            "timeseriesgroup_set-0-timeseries_set-0-time_step": "10min",
            "timeseriesgroup_set-0-timeseries_set-0-replace_or_append": "APPEND",
            "timeseriesgroup_set-0-timeseries_set-1-type": "100",
            "timeseriesgroup_set-0-timeseries_set-1-time_step": "10min",
            "timeseriesgroup_set-0-timeseries_set-1-replace_or_append": "APPEND",
        }
        response = self.client.post("/admin/enhydris/station/add/", data)
        self.assertContains(response, "must be unique")

    def test_checks_unique_initial(self):
        data = {
            **self._get_basic_form_contents(),
            "timeseriesgroup_set-0-timeseries_set-TOTAL_FORMS": "3",
            "timeseriesgroup_set-0-timeseries_set-0-type": "100",
            "timeseriesgroup_set-0-timeseries_set-0-time_step": "10min",
            "timeseriesgroup_set-0-timeseries_set-0-replace_or_append": "APPEND",
            "timeseriesgroup_set-0-timeseries_set-1-type": "100",
            "timeseriesgroup_set-0-timeseries_set-1-time_step": "20min",
            "timeseriesgroup_set-0-timeseries_set-1-replace_or_append": "APPEND",
            "timeseriesgroup_set-0-timeseries_set-2-type": "200",
            "timeseriesgroup_set-0-timeseries_set-2-time_step": "10min",
            "timeseriesgroup_set-0-timeseries_set-2-replace_or_append": "APPEND",
        }
        response = self.client.post("/admin/enhydris/station/add/", data)
        self.assertContains(response, "only one initial time series")

    def test_checks_unique_checked(self):
        data = {
            **self._get_basic_form_contents(),
            "timeseriesgroup_set-0-timeseries_set-TOTAL_FORMS": "3",
            "timeseriesgroup_set-0-timeseries_set-0-type": "100",
            "timeseriesgroup_set-0-timeseries_set-0-time_step": "10min",
            "timeseriesgroup_set-0-timeseries_set-0-replace_or_append": "APPEND",
            "timeseriesgroup_set-0-timeseries_set-1-type": "200",
            "timeseriesgroup_set-0-timeseries_set-1-time_step": "10min",
            "timeseriesgroup_set-0-timeseries_set-1-replace_or_append": "APPEND",
            "timeseriesgroup_set-0-timeseries_set-2-type": "200",
            "timeseriesgroup_set-0-timeseries_set-2-time_step": "20min",
            "timeseriesgroup_set-0-timeseries_set-2-replace_or_append": "APPEND",
        }
        response = self.client.post("/admin/enhydris/station/add/", data)
        self.assertContains(response, "only one checked time series")

    def test_checks_unique_regularized(self):
        data = {
            **self._get_basic_form_contents(),
            "timeseriesgroup_set-0-timeseries_set-TOTAL_FORMS": "3",
            "timeseriesgroup_set-0-timeseries_set-0-type": "100",
            "timeseriesgroup_set-0-timeseries_set-0-time_step": "10min",
            "timeseriesgroup_set-0-timeseries_set-0-replace_or_append": "APPEND",
            "timeseriesgroup_set-0-timeseries_set-1-type": "300",
            "timeseriesgroup_set-0-timeseries_set-1-time_step": "10min",
            "timeseriesgroup_set-0-timeseries_set-1-replace_or_append": "APPEND",
            "timeseriesgroup_set-0-timeseries_set-2-type": "300",
            "timeseriesgroup_set-0-timeseries_set-2-time_step": "20min",
            "timeseriesgroup_set-0-timeseries_set-2-replace_or_append": "APPEND",
        }
        response = self.client.post("/admin/enhydris/station/add/", data)
        self.assertContains(response, "only one regularized time series")

    def test_empty_timeseries_form_is_ignored(self):
        data = {
            **self._get_basic_form_contents(),
            "timeseriesgroup_set-0-timeseries_set-TOTAL_FORMS": "1",
            "timeseriesgroup_set-0-timeseries_set-0-type": "",
            "timeseriesgroup_set-0-timeseries_set-0-time_step": "",
            "timeseriesgroup_set-0-timeseries_set-0-replace_or_append": "APPEND",
        }
        response = self.client.post("/admin/enhydris/station/add/", data)
        self.assertEqual(response.status_code, 302)
