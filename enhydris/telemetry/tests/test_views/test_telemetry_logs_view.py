import datetime as dt

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from bs4 import BeautifulSoup
from model_mommy import mommy

from enhydris.models import Station
from enhydris.telemetry.models import Telemetry, TelemetryLogMessage


class TelemetryLogViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("alice", password="topsecret")
        cls.station = mommy.make(Station, name="great station", creator=cls.user)
        cls.station2 = mommy.make(Station, name="another station", creator=cls.user)
        cls.telemetry = mommy.make(Telemetry, station=cls.station)
        cls.telemetry_log = mommy.make(
            TelemetryLogMessage,
            telemetry=cls.telemetry,
            exception_name="HugeError",
            message="huge error",
            traceback="Detailed traceback:\nThe problem occurred somewhere",
            enhydris_version="14.15.16",
            enhydris_commit_id="1234567890abcdef",
        )
        utc = dt.timezone.utc
        cls.telemetry_log.timestamp = dt.datetime(2022, 8, 5, 18, 31, 44, tzinfo=utc)
        cls.telemetry_log.save()


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class TelemetryLogListViewTestCase(TelemetryLogViewTestCase):
    def setUp(self):
        self.client.login(username="alice", password="topsecret")
        self.url = f"/stations/{self.station.id}/telemetry/logs/"
        self.response = self.client.get(self.url)

    def test_shows_message(self):
        self.assertContains(self.response, "HugeError: huge error")

    def test_shows_station_name(self):
        self.assertContains(self.response, "great station")

    def test_links_to_detail_page(self):
        log_id = self.telemetry_log.id
        soup = BeautifulSoup(self.response.content, "html.parser")
        target = soup.find("div", class_="list-group-item").find("a").get("href")
        self.assertEqual(target, f"{self.url}{log_id}/")

    def test_no_message_about_no_logs(self):
        self.assertNotContains(self.response, "No telemetry errors have been logged")


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class TelemetryLogListViewNoLogsTestCase(TelemetryLogViewTestCase):
    def setUp(self):
        self.client.login(username="alice", password="topsecret")
        self.url = f"/stations/{self.station2.id}/telemetry/logs/"
        self.response = self.client.get(self.url)

    def test_has_no_logs(self):
        self.assertNotContains(self.response, "HugeError")

    def test_message_no_logs(self):
        self.assertContains(
            self.response, "No telemetry errors have been logged for this station."
        )


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class TelemetryLogDetailViewTestCase(TelemetryLogViewTestCase):
    def setUp(self):
        self.client.login(username="alice", password="topsecret")
        log_id = self.telemetry_log.id
        url = f"/stations/{self.telemetry.station_id}/telemetry/logs/{log_id}/"
        self.response = self.client.get(url)

    def test_shows_station_name(self):
        self.assertContains(self.response, "great station")

    def test_shows_message(self):
        self.assertContains(self.response, "huge error")

    def test_shows_exception_name(self):
        self.assertContains(self.response, "HugeError")

    def test_shows_error_date(self):
        self.assertContains(self.response, "2022-08-05 18:31:44")

    def test_shows_traceback(self):
        self.assertContains(
            self.response, "Detailed traceback:\nThe problem occurred somewhere"
        )

    def test_shows_enhydris_version(self):
        self.assertContains(self.response, "14.15.16 (1234567890)")

    def test_back_button(self):
        soup = BeautifulSoup(self.response.content, "html.parser")
        target = soup.find(id="back-button").get("href")
        station_id = self.telemetry.station_id
        self.assertEqual(target, f"/stations/{station_id}/telemetry/logs/")


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class PermissionsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("alice", password="topsecret")
        cls.station = mommy.make(Station, creator=cls.user)
        cls.telemetry_log_message = mommy.make(
            TelemetryLogMessage,
            telemetry__station=cls.station,
        )

    def test_telemetry_logs_are_visible_when_correct_user_logged_on(self):
        self.client.login(username="alice", password="topsecret")
        response = self.client.get(f"/stations/{self.station.id}/telemetry/logs/")
        self.assertEqual(response.status_code, 200)

    def test_telemetry_logs_denied_when_not_logged_on(self):
        url = f"/stations/{self.station.id}/telemetry/logs/"
        response = self.client.get(url)
        self.assertRedirects(response, f"/accounts/login/?next={url}")

    def test_telemetry_log_detail_visible_when_correct_user_logged_on(self):
        self.client.login(username="alice", password="topsecret")
        station_id = self.station.id
        tlm_id = self.telemetry_log_message.id
        url = f"/stations/{station_id}/telemetry/logs/{tlm_id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_telemetry_log_detail_denied_when_not_logged_on(self):
        station_id = self.station.id
        tlm_id = self.telemetry_log_message.id
        url = f"/stations/{station_id}/telemetry/logs/{tlm_id}/"
        response = self.client.get(url)
        self.assertRedirects(response, f"/accounts/login/?next={url}")
