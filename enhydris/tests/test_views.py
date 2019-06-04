from unittest import skipUnless

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.test import TestCase, override_settings

from bs4 import BeautifulSoup
from django_selenium_clean import PageElement, SeleniumTestCase
from model_mommy import mommy
from selenium.webdriver.common.by import By

from enhydris.models import GentityFile, Station, Timeseries


class StationListTestCase(TestCase):
    def setUp(self):
        mommy.make(
            User,
            username="admin",
            password=make_password("topsecret"),
            is_active=True,
            is_superuser=True,
            is_staff=True,
        )
        mommy.make(
            Station,
            name="Komboti",
            point=Point(x=21.06071, y=39.09518, srid=4326),
            original_srid=4326,
        )
        mommy.make(
            Station,
            name="Agios Athanasios",
            point=Point(x=21.60121, y=39.22440, srid=4326),
            original_srid=4326,
        )
        mommy.make(
            Station,
            name="Tharbad",
            point=Point(x=-176.48368, y=0.19377, srid=4326),
            original_srid=4326,
        )
        mommy.make(
            Station,
            name="SRID Point, NoSRID Station",
            point=Point(x=-176.48368, y=0.19377, srid=4326),
            original_srid=None,
        )
        mommy.make(
            Station,
            name="NoSRID Point, SRID Station",
            point=Point(x=-176.48368, y=0.19377, srid=None),
            original_srid=4326,
        )
        mommy.make(
            Station,
            name="NoSRID Point, NoSRID Station",
            point=Point(x=-176.48368, y=0.19377, srid=None),
            original_srid=None,
        )

    def test_station_list(self):
        response = self.client.get("/")
        self.assertContains(
            response, '<a href="?sort=-name&amp;sort=name">Name&nbsp;↓</a>', html=True
        )

    @override_settings(ENHYDRIS_STATIONS_PER_PAGE=3)
    def test_two_pages(self):
        response = self.client.get("/")
        self.assertContains(response, "<a href='?page=2'>2</a>", html=True)
        self.assertNotContains(response, "<a href='?page=3'>3</a>", html=True)

    @override_settings(ENHYDRIS_STATIONS_PER_PAGE=2)
    def test_next_page_url(self):
        response = self.client.get("/")
        soup = BeautifulSoup(response.content, "html.parser")
        next_page_url = soup.find("a", id="next-page").get("href")
        self.assertEqual(next_page_url, "?page=2")

    @override_settings(ENHYDRIS_STATIONS_PER_PAGE=2)
    def test_previous_page_url(self):
        response = self.client.get("/?page=2")
        soup = BeautifulSoup(response.content, "html.parser")
        next_page_url = soup.find("a", id="previous-page").get("href")
        self.assertEqual(next_page_url, "?page=1")

    @override_settings(ENHYDRIS_STATIONS_PER_PAGE=100)
    def test_one_page(self):
        response = self.client.get("/")
        self.assertNotContains(response, "<a href='?page=2'>2</a>", html=True)


class StationDetailTestCase(TestCase):
    def setUp(self):
        self.station = mommy.make(
            Station,
            name="Komboti",
            point=Point(x=21.00000, y=39.00000, srid=4326),
            original_srid=4326,
        )

    @override_settings(ENHYDRIS_MAP_MIN_VIEWPORT_SIZE=0.2)
    def test_map_viewport(self):
        response = self.client.get("/stations/{}/".format(self.station.id))
        self.assertContains(response, "enhydris.mapViewport=[20.9, 38.9, 21.1, 39.1]")

    def test_popup_mode(self):
        response = self.client.get("/stations/{}/?mode=popup".format(self.station.id))
        self.assertContains(response, "Details...")


class TimeseriesDownloadLinkTestCase(TestCase):
    def setUp(self):
        self.station = mommy.make(Station, name="Komboti")
        self.timeseries = mommy.make(Timeseries, gentity=self.station)
        self.link = '<a href="/api/stations/{}/timeseries/{}/data/?fmt=hts">'.format(
            self.station.id, self.timeseries.id
        )

    def _get_response(self):
        self.response = self.client.get(
            "/stations/{}/timeseries/{}/".format(self.station.id, self.timeseries.id)
        )

    @override_settings(ENHYDRIS_OPEN_CONTENT=True)
    def test_contains_download_link_when_site_content_is_free(self):
        self._get_response()
        self.assertContains(self.response, self.link)

    @override_settings(ENHYDRIS_OPEN_CONTENT=False)
    def test_has_no_download_link_when_site_content_is_restricted(self):
        self._get_response()
        self.assertNotContains(self.response, self.link)

    @override_settings(ENHYDRIS_OPEN_CONTENT=True)
    def test_has_no_permission_denied_message_when_site_content_is_free(self):
        self._get_response()
        self.assertNotContains(self.response, "You don't have permission to download")

    @override_settings(ENHYDRIS_OPEN_CONTENT=False)
    def test_shows_permission_denied_message_when_site_content_is_restricted(self):
        self._get_response()
        self.assertContains(self.response, "You don't have permission to download")


class GentityFileDownloadLinkTestCase(TestCase):
    def setUp(self):
        self.station = mommy.make(Station, name="Komboti")
        self.gentityfile = mommy.make(GentityFile, gentity=self.station)
        self.link = '<a href="/api/stations/{}/files/{}/content/">'.format(
            self.station.id, self.gentityfile.id
        )

    @override_settings(ENHYDRIS_OPEN_CONTENT=True)
    def test_contains_download_link_when_site_content_is_free(self):
        response = self.client.get("/stations/{}/".format(self.station.id))
        self.assertContains(response, self.link)

    @override_settings(ENHYDRIS_OPEN_CONTENT=False)
    def test_has_no_download_link_when_site_content_is_restricted(self):
        response = self.client.get("/stations/{}/".format(self.station.id))
        self.assertNotContains(response, self.link)


class StationEditRedirectTestCase(TestCase):
    def setUp(self):
        self.response = self.client.get("/stations/42/edit/")

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 302)

    def test_redirect_target(self):
        self.assertEqual(
            self.response["Location"], "/admin/enhydris/station/42/change/"
        )


@skipUnless(getattr(settings, "SELENIUM_WEBDRIVERS", False), "Selenium is unconfigured")
class ListStationsVisibleOnMapTestCase(SeleniumTestCase):

    button_limit_to_map = PageElement(By.ID, "limit-to-map")
    td_komboti = PageElement(By.XPATH, '//td//a[text()="Komboti"]')
    td_agios_athanasios = PageElement(By.XPATH, '//td//a[text()="Agios Athanasios"]')
    td_tharbad = PageElement(By.XPATH, '//td//a[text()="Tharbad"]')

    def setUp(self):
        mommy.make(
            Station,
            name="Komboti",
            point=Point(x=21.06071, y=39.09518, srid=4326),
            original_srid=4326,
        )
        mommy.make(
            Station,
            name="Agios Athanasios",
            point=Point(x=21.60121, y=39.22440, srid=4326),
            original_srid=4326,
        )
        mommy.make(
            Station,
            name="Tharbad",
            point=Point(x=-176.48368, y=0.19377, srid=4326),
            original_srid=4326,
        )

    def test_list_stations_visible_on_map(self):
        # Visit site and wait until three stations are shown
        self.selenium.get(self.live_server_url)
        self.td_komboti.wait_until_is_displayed()
        self.td_agios_athanasios.wait_until_is_displayed()
        self.td_tharbad.wait_until_is_displayed()

        # Zoom station to an area that covers only two of these stations.
        # The co-ordinates below are 21, 39, 22, 40 in srid=3857.
        self.selenium.execute_script(
            """
            enhydris.map.zoomToExtent([2337700, 4721700, 2449000, 4865900]);
            """
        )

        # Click on "List stations visible on map"
        self.button_limit_to_map.click()

        # Now only two stations should be displayed
        self.td_komboti.wait_until_is_displayed()
        self.td_agios_athanasios.wait_until_is_displayed()
        self.assertFalse(self.td_tharbad.exists())