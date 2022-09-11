from unittest.mock import patch

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import Client, TestCase, override_settings

import requests
from bs4 import BeautifulSoup
from model_mommy import mommy

from enhydris.models import Station
from enhydris.telemetry.forms import ConnectionDataForm
from enhydris.telemetry.models import Telemetry
from enhydris.telemetry.views import TelemetryWizardView


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class RedirectToFirstStepTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="alice", password="topsecret")
        cls.station = mommy.make(Station, creator=cls.user)

    def test_redirects(self):
        """Test that we are redirected to the first step if we don't come from there"""
        self.client.login(username="alice", password="topsecret")
        response = self.client.get(f"/stations/{self.station.id}/telemetry/2/")
        expected_url = f"/stations/{self.station.id}/telemetry/1/"
        self.assertRedirects(response, expected_url)

    def test_no_redirects(self):
        """Test that we are not redirected if we come from the first step"""
        self.client.login(username="alice", password="topsecret")
        self.client.post(
            f"/stations/{self.station.id}/telemetry/1/",
            {
                "type": "meteoview2",
                "data_time_zone": "Europe/Athens",
                "fetch_interval_minutes": "10",
                "fetch_offset_minutes": "2",
                "fetch_offset_time_zone": "Europe/Kiev",
            },
        )
        response = self.client.get(f"/stations/{self.station.id}/telemetry/2/")
        self.assertEqual(response.status_code, 200)


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class CopyTelemetryDataFromDatabaseToSessionTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="alice", password="topsecret")
        cls.station = mommy.make(Station, creator=cls.user)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cclient = Client()
        cls.cclient.login(username="alice", password="topsecret")
        cls.response = cls.cclient.get(f"/stations/{cls.station.id}/telemetry/1/")
        cls.soup = BeautifulSoup(cls.response.content, "html.parser")

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_default_type_is_empty(self):
        option_empty = self.soup.find(id="id_type").find("option", value="")
        self.assertEqual(option_empty.get("selected"), "")

    def test_meteoview2_option_is_not_selected(self):
        option_empty = self.soup.find(id="id_type").find("option", value="meteoview2")
        self.assertIsNone(option_empty.get("selected"))

    def test_default_data_time_zone_is_empty(self):
        option_empty = self.soup.find(id="id_data_time_zone").find("option", value="")
        self.assertEqual(option_empty.get("selected"), "")

    def test_default_fetch_interval_minutes_is_empty(self):
        fetch_interval_minutes = self.soup.find(id="id_fetch_interval_minutes")
        self.assertIsNone(fetch_interval_minutes.get("value"))

    def test_default_fetch_offset_minutes_is_empty(self):
        fetch_offset_minutes = self.soup.find(id="id_fetch_offset_minutes")
        self.assertIsNone(fetch_offset_minutes.get("value"))

    def test_default_fetch_offset_time_zone_is_empty(self):
        option_empty = self.soup.find(id="id_fetch_offset_time_zone").find(
            "option", value=""
        )
        self.assertEqual(option_empty.get("selected"), "")


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class CopyTelemetryDataFromDatabaseToSessionWithExistingTelemetryTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="alice", password="topsecret")
        cls.station = mommy.make(Station, creator=cls.user)
        cls.telemetry = mommy.make(
            Telemetry,
            station=cls.station,
            type="meteoview2",
            data_time_zone="Europe/Athens",
            fetch_interval_minutes=10,
            fetch_offset_minutes=2,
            fetch_offset_time_zone="Asia/Vladivostok",
            additional_config="{}",
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cclient = Client()
        cls.cclient.login(username="alice", password="topsecret")
        cls.response = cls.cclient.get(f"/stations/{cls.station.id}/telemetry/1/")
        cls.soup = BeautifulSoup(cls.response.content, "html.parser")

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_empty_type_is_not_selected(self):
        option_empty = self.soup.find(id="id_type").find("option", value="")
        self.assertIsNone(option_empty.get("selected"))

    def test_default_type_is_meteoview2(self):
        option_meteoview2 = self.soup.find(id="id_type").find(
            "option", value="meteoview2"
        )
        self.assertEqual(option_meteoview2.get("selected"), "")

    def test_empty_data_time_zone_is_not_selected(self):
        option_empty = self.soup.find(id="id_data_time_zone").find("option", value="")
        self.assertIsNone(option_empty.get("selected"))

    def test_default_data_time_zone_is_meteoview2(self):
        option_europe_athens = self.soup.find(id="id_data_time_zone").find(
            "option", value="Europe/Athens"
        )
        self.assertEqual(option_europe_athens.get("selected"), "")

    def test_default_fetch_interval_minutes_is_10(self):
        fetch_interval_minutes = self.soup.find(id="id_fetch_interval_minutes")
        self.assertEqual(fetch_interval_minutes["value"], "10")

    def test_default_fetch_offset_minutes_is_2(self):
        fetch_offset_minutes = self.soup.find(id="id_fetch_offset_minutes")
        self.assertEqual(fetch_offset_minutes["value"], "2")

    def test_empty_fetch_offset_time_zone_is_not_selected(self):
        option_empty = self.soup.find(id="id_fetch_offset_time_zone").find(
            "option", value=""
        )
        self.assertIsNone(option_empty.get("selected"))

    def test_default_fetch_offset_time_zone_is_meteoview2(self):
        option_asia_vladivostok = self.soup.find(id="id_fetch_offset_time_zone").find(
            "option", value="Asia/Vladivostok"
        )
        self.assertEqual(option_asia_vladivostok.get("selected"), "")

    def test_configuration_is_in_the_session(self):
        itemkey = f"telemetry_{self.station.id}"
        expected = {
            "type": "meteoview2",
            "data_time_zone": "Europe/Athens",
            "fetch_interval_minutes": 10,
            "fetch_offset_minutes": 2,
            "fetch_offset_time_zone": "Asia/Vladivostok",
            "additional_config": "{}",
        }
        self.assertEqual(self.cclient.session[itemkey], expected)


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class FirstStepPostTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="alice", password="topsecret")
        cls.station = mommy.make(Station, creator=cls.user)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cclient = Client()
        cls.cclient.login(username="alice", password="topsecret")
        cls.response = cls.cclient.post(
            f"/stations/{cls.station.id}/telemetry/1/",
            {
                "type": "meteoview2",
                "data_time_zone": "Europe/Athens",
                "fetch_interval_minutes": "10",
                "fetch_offset_minutes": "2",
                "fetch_offset_time_zone": "Europe/Kiev",
            },
        )

    def _session(self, key):
        return self.cclient.session[f"telemetry_{self.station.id}"][key]

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 302)

    def test_type(self):
        self.assertEqual(self._session("type"), "meteoview2")

    def test_data_time_zone(self):
        self.assertEqual(self._session("data_time_zone"), "Europe/Athens")

    def test_fetch_interval_minutes(self):
        self.assertEqual(self._session("fetch_interval_minutes"), 10)

    def test_fetch_offset_minutes(self):
        self.assertEqual(self._session("fetch_offset_minutes"), 2)

    def test_fetch_offset_time_zone(self):
        self.assertEqual(self._session("fetch_offset_time_zone"), "Europe/Kiev")


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class FirstStepPostErrorTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="alice", password="topsecret")
        cls.station = mommy.make(Station, creator=cls.user)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cclient = Client()
        cls.cclient.login(username="alice", password="topsecret")
        cls.response = cls.cclient.post(
            f"/stations/{cls.station.id}/telemetry/1/", {"hello": "world"}
        )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)


class SecondStepGetMixin:
    # Note: we use the "meteoview2" driver (otherwise we'd need to mock or create a
    # dummy driver for testing), but we only test the functionality of telemetry.views
    # here, not the functionality of meteoview2 (this is to be tested elsewhere).

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="alice", password="topsecret")
        cls.station = mommy.make(Station, creator=cls.user)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cclient = Client()
        cls.cclient.login(username="alice", password="topsecret")
        cls._post_step_1()
        cls._make_request_for_step_2()

    @classmethod
    def _post_step_1(cls):
        cls.cclient.post(
            f"/stations/{cls.station.id}/telemetry/1/",
            {
                "type": "meteoview2",
                "data_time_zone": "Europe/Athens",
                "fetch_interval_minutes": "10",
                "fetch_offset_minutes": "2",
                "fetch_offset_time_zone": "Europe/Kiev",
            },
        )

    @classmethod
    def _make_request_for_step_2(cls):
        p1 = patch("enhydris.telemetry.views.render", return_value=HttpResponse("hi"))
        with p1 as mock_render:
            cls.mock_render = mock_render
            cls.response = cls.cclient.get(f"/stations/{cls.station.id}/telemetry/2/")

    @property
    def _template_context(self):
        return self.mock_render.call_args.args[2]


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class SecondStepGetTestCase(SecondStepGetMixin, TestCase):
    def test_called_render(self):
        self.mock_render.assert_called_once()

    def test_render_context_station(self):
        self.assertEqual(self._template_context["station"].id, self.station.id)

    def test_render_context_form(self):
        self.assertEqual(self._template_context["form"].__class__, ConnectionDataForm)

    def test_render_context_seq(self):
        self.assertEqual(self._template_context["seq"], 2)

    def test_render_context_prev_seq(self):
        self.assertEqual(self._template_context["prev_seq"], 1)

    def test_render_context_max_seq(self):
        self.assertEqual(self._template_context["max_seq"], 4)

    def test_form_created_with_the_correct_configuration(self):
        self.assertEqual(self._template_context["form"].initial["type"], "meteoview2")


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class SecondStepGetWithNondefaultConfigurationTestCase(SecondStepGetMixin, TestCase):
    # This is essentially the same as
    # SecondStepGetTestCase.test_form_created_with_the_correct_configuration, except
    # that it modifies the session to ensure that the configuration is read from there.
    @classmethod
    def _make_request_for_step_2(cls):
        session = cls.cclient.session
        session[f"telemetry_{cls.station.id}"] = {"type": "addupi"}
        session.save()
        super()._make_request_for_step_2()

    def test_form_created_with_the_correct_configuration(self):
        self.assertEqual(self._template_context["form"].initial["type"], "addupi")


class SecondStepPostMixin:
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="alice", password="topsecret")
        cls.station = mommy.make(Station, creator=cls.user)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cclient = Client()
        cls.cclient.login(username="alice", password="topsecret")
        cls._post_step_1()
        cls._post_step_2()

    @classmethod
    def _post_step_1(cls):
        cls.cclient.post(
            f"/stations/{cls.station.id}/telemetry/1/",
            {
                "type": "meteoview2",
                "data_time_zone": "Europe/Athens",
                "fetch_interval_minutes": "10",
                "fetch_offset_minutes": "2",
                "fetch_offset_time_zone": "Europe/Kiev",
            },
        )


class MockResponse(requests.Response):
    def __init__(self, status_code=200, json_result=None):
        super().__init__()
        self.status_code = status_code
        self.json_result = json_result

    def json(self):
        return self.json_result


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class SecondStepPostWithErrorTestCase(SecondStepPostMixin, TestCase):
    @classmethod
    def _post_step_2(cls):
        p1 = patch(
            "enhydris.telemetry.types.meteoview2.requests.request",
            **{
                "return_value.raise_for_status.side_effect": requests.RequestException(
                    "error"
                )
            },
        )
        with p1:
            cls.response = cls.cclient.post(
                f"/stations/{cls.station.id}/telemetry/2/",
                data={"invalid": "data"},
            )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_error_message(self):
        self.assertContains(self.response, "This field is required")


class SecondStepPostSuccessfulMixin(SecondStepPostMixin):
    @classmethod
    def _post_step_2(cls):
        p1 = patch(
            "enhydris.telemetry.types.meteoview2.requests.request",
            return_value=MockResponse(json_result={"code": 200, "token": "hello"}),
        )
        with p1:
            cls.response = cls.cclient.post(
                f"/stations/{cls.station.id}/telemetry/2/",
                data={
                    "username": "someemail@email.com",
                    "password": "topsecret",
                },
            )


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class SecondStepPostSuccessfulTestCase(SecondStepPostSuccessfulMixin, TestCase):
    def test_redirects_to_next_step(self):
        self.assertRedirects(
            self.response,
            f"/stations/{self.station.id}/telemetry/3/",
            fetch_redirect_response=False,
        )

    def test_updated_configuration(self):
        self.assertEqual(
            self.cclient.session[f"telemetry_{self.station.id}"],
            {
                "type": "meteoview2",
                "data_time_zone": "Europe/Athens",
                "fetch_interval_minutes": 10,
                "fetch_offset_minutes": 2,
                "fetch_offset_time_zone": "Europe/Kiev",
                "username": "someemail@email.com",
                "password": "topsecret",
                "device_locator": "",
                "additional_config": {},
            },
        )


class FinalStepPostSuccessfulMixin(SecondStepPostSuccessfulMixin):
    # We use the same request as second step, but we meddle with the number of steps
    # to fool the system into thinking it's the final step.
    @classmethod
    def setUpClass(cls):
        cls.saved_forms = TelemetryWizardView.forms
        TelemetryWizardView.forms = TelemetryWizardView.forms[:2]
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        TelemetryWizardView.forms = cls.saved_forms


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class FinalStepPostSuccessfulTestCase(FinalStepPostSuccessfulMixin, TestCase):
    def test_saves_stuff_in_database(self):
        telemetry = Telemetry.objects.get(station=self.station)
        self.assertEqual(telemetry.username, "someemail@email.com")

    def test_redirects_to_station_page(self):
        self.assertRedirects(
            self.response,
            f"/stations/{self.station.id}/",
            fetch_redirect_response=False,
        )

    def test_shows_message(self):
        final_response = self.cclient.get(self.response.url)
        self.assertContains(final_response, "Telemetry has been configured")


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class FinalStepPostSuccessfulReplacesExistingTelemetryTestCase(
    FinalStepPostSuccessfulMixin, TestCase
):
    # Tests that when telemetry already exists, it is replaced.
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        Telemetry.objects.create(
            station=cls.station,
            fetch_interval_minutes=10,
            fetch_offset_minutes=0,
            additional_config={},
        )

    def test_replaces_stuff_in_database(self):
        telemetry = Telemetry.objects.get(station=self.station)
        self.assertEqual(telemetry.username, "someemail@email.com")


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
@patch(
    "enhydris.telemetry.types.meteoview2.requests.request",
    return_value=MockResponse(
        json_result={"code": 200, "token": "hello", "stations": []}
    ),
)
class NextOrFinishButtonTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="alice", password="topsecret")
        cls.station = mommy.make(Station, creator=cls.user)
        Telemetry.objects.create(
            station=cls.station,
            fetch_interval_minutes=10,
            fetch_offset_minutes=0,
            additional_config={},
        )

    def setUp(self):
        self.client.login(username="alice", password="topsecret")
        session = self.client.session
        session[f"telemetry_{self.station.id}"] = {
            "station_id": self.station.id,
            "username": "someemail@somewhere.com",
            "password": "topsecret",
            "type": "meteoview2",
            "data_time_zone": "Europe/Athens",
            "fetch_interval_minutes": "10",
            "fetch_offset_minutes": "2",
            "fetch_offset_time_zone": "Europe/Kiev",
        }
        session.save()

        self.saved_forms = TelemetryWizardView.forms

    def tearDown(self):
        TelemetryWizardView.forms = self.saved_forms

    def _get_button_text_for_step_2(self):
        response = self.client.get(f"/stations/{self.station.id}/telemetry/2/")
        soup = BeautifulSoup(response.content, "html.parser")
        return soup.find("button", attrs={"type": "submit"}).get_text().strip()

    def test_button_says_next_in_nonfinal_step(self, m):
        button_text = self._get_button_text_for_step_2()
        self.assertEqual(button_text, "Next")

    def test_button_says_finish_in_final_step(self, m):
        TelemetryWizardView.forms = TelemetryWizardView.forms[:2]
        button_text = self._get_button_text_for_step_2()
        self.assertEqual(button_text, "Finish")


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class PermissionsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("alice", password="topsecret")
        cls.station = mommy.make(Station, creator=cls.user)

    def test_telemetry_button_does_not_appear_when_not_logged_on(self):
        response = self.client.get(f"/stations/{self.station.id}/")
        self.assertNotContains(response, "btn-station-telemetry")

    def test_telemetry_button_appears_when_correct_user_logged_on(self):
        self.client.login(username="alice", password="topsecret")
        response = self.client.get(f"/stations/{self.station.id}/")
        self.assertContains(response, "btn-station-telemetry")

    def test_telemetry_form_works_when_correct_user_logged_on(self):
        self.client.login(username="alice", password="topsecret")
        response = self.client.get(f"/stations/{self.station.id}/telemetry/1/")
        self.assertEqual(response.status_code, 200)

    def test_telemetry_form_denies_when_not_logged_on(self):
        response = self.client.get(f"/stations/{self.station.id}/telemetry/1/")
        self.assertEqual(response.status_code, 404)
