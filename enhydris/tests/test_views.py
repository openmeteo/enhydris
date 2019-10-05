import datetime as dt
from time import sleep
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
            geom=Point(x=21.06071, y=39.09518, srid=4326),
            original_srid=4326,
        )
        mommy.make(
            Station,
            name="Agios Athanasios",
            geom=Point(x=21.60121, y=39.22440, srid=4326),
            original_srid=4326,
        )
        mommy.make(
            Station,
            name="Tharbad",
            geom=Point(x=-176.48368, y=0.19377, srid=4326),
            original_srid=4326,
        )
        mommy.make(
            Station,
            name="SRID Point, NoSRID Station",
            geom=Point(x=-176.48368, y=0.19377, srid=4326),
            original_srid=None,
        )
        mommy.make(
            Station,
            name="NoSRID Point, SRID Station",
            geom=Point(x=-176.48368, y=0.19377, srid=None),
            original_srid=4326,
        )
        mommy.make(
            Station,
            name="NoSRID Point, NoSRID Station",
            geom=Point(x=-176.48368, y=0.19377, srid=None),
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
            geom=Point(x=21.00000, y=39.00000, srid=4326),
            original_srid=4326,
        )

    @override_settings(ENHYDRIS_MAP_MIN_VIEWPORT_SIZE=0.2)
    def test_map_viewport(self):
        response = self.client.get("/stations/{}/".format(self.station.id))
        self.assertContains(response, "enhydris.mapViewport=[20.9, 38.9, 21.1, 39.1]")


class StationDetailPeriodOfOperationTestCase(TestCase):
    def setUp(self):
        self.station = mommy.make(
            Station,
            name="Komboti",
            geom=Point(x=21.00000, y=39.00000, srid=4326),
            original_srid=4326,
        )

    def _set_dates(self, start_date, end_date):
        self.station.start_date = start_date
        self.station.end_date = end_date
        self.station.save()

    def _get_response(self):
        return self.client.get(
            "/stations/{}/".format(self.station.id), HTTP_ACCEPT_LANGUAGE="en-gb"
        )

    def test_when_start_date_and_end_date(self):
        self._set_dates(dt.datetime(2019, 7, 26), dt.datetime(2019, 7, 27))
        response = self._get_response()
        self.assertContains(
            response, "<b>Period of operation:</b> 26/07/2019 - 27/07/2019"
        )

    def test_when_only_start_date(self):
        self._set_dates(dt.datetime(2019, 7, 26), None)
        response = self._get_response()
        self.assertContains(response, "<b>Start of operation:</b> 26/07/2019")

    def test_when_only_end_date(self):
        self._set_dates(None, dt.datetime(2019, 7, 27))
        response = self._get_response()
        self.assertContains(response, "<b>End of operation:</b> 27/07/2019")

    def test_when_no_dates(self):
        self._set_dates(None, None)
        response = self._get_response()
        self.assertNotContains(response, "operation")


class TimeseriesDownloadLinkTestCase(TestCase):
    def setUp(self):
        self.station = mommy.make(Station, name="Komboti")
        self.timeseries = mommy.make(
            Timeseries, gentity=self.station, variable__descr="irrelevant"
        )
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


class RedirectOldUrlsTestCase(TestCase):
    def test_old_stations_url_redirects(self):
        r = self.client.get("/stations/d/200348/")
        self.assertRedirects(
            r, "/stations/200348/", status_code=301, fetch_redirect_response=False
        )

    def test_old_timeseries_url_redirects(self):
        mommy.make(Timeseries, id=1169, gentity__id=200348)
        r = self.client.get("/timeseries/d/1169/")
        self.assertRedirects(
            r,
            "/stations/200348/timeseries/1169/",
            status_code=301,
            fetch_redirect_response=False,
        )

    def test_old_timeseries_url_for_nonexistent_timeseries_returns_404(self):
        r = self.client.get("/timeseries/d/1169/")
        self.assertEqual(r.status_code, 404)


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
            geom=Point(x=21.06071, y=39.09518, srid=4326),
            original_srid=4326,
        )
        mommy.make(
            Station,
            name="Agios Athanasios",
            geom=Point(x=21.60121, y=39.22440, srid=4326),
            original_srid=4326,
        )
        mommy.make(
            Station,
            name="Tharbad",
            geom=Point(x=-176.48368, y=0.19377, srid=4326),
            original_srid=4326,
        )

    def test_list_stations_visible_on_map(self):
        # Visit site and wait until three stations are shown
        self.selenium.get(self.live_server_url)
        self.td_komboti.wait_until_is_displayed()
        self.td_agios_athanasios.wait_until_is_displayed()
        self.td_tharbad.wait_until_is_displayed()

        # Zoom station to an area that covers only two of these stations.
        self.selenium.execute_script(
            """
            enhydris.map.fitBounds([[39.0, 21.0], [40.0, 22.0]]);
            """
        )

        # Click on "List stations visible on map"
        self.button_limit_to_map.click()

        # Now only two stations should be displayed
        self.td_komboti.wait_until_is_displayed()
        self.td_agios_athanasios.wait_until_is_displayed()
        self.assertFalse(self.td_tharbad.exists())


@skipUnless(getattr(settings, "SELENIUM_WEBDRIVERS", False), "Selenium is unconfigured")
class ShowOnlySearchedForStationsOnMapTestCase(SeleniumTestCase):

    markers = PageElement(By.CSS_SELECTOR, ".leaflet-marker-pane")

    def setUp(self):
        mommy.make(Station, name="West", geom=Point(x=23.0, y=38.0, srid=4326))
        mommy.make(Station, name="Middle", geom=Point(x=23.1, y=38.0, srid=4326))
        mommy.make(Station, name="East", geom=Point(x=23.2, y=38.0, srid=4326))

    def test_list_stations_visible_on_map(self):
        # Visit site and wait until three stations are shown
        self.selenium.get(self.live_server_url)
        num_stations_shown = self._get_num_stations_shown()
        self.assertEqual(num_stations_shown, 3)

        # Search so that only two stations will be found in an area that could include
        # all three stations, and verify only two stations are shown
        self.selenium.get(self.live_server_url + "?q=st")
        num_stations_shown = self._get_num_stations_shown()
        self.assertEqual(num_stations_shown, 2)

    def _get_num_stations_shown(self):
        self.markers.wait_until_exists()
        for i in range(6):
            result = len(self.markers.find_elements_by_tag_name("img"))
            if result:
                return result
            sleep(0.5)


@skipUnless(getattr(settings, "SELENIUM_WEBDRIVERS", False), "Selenium is unconfigured")
class ShowStationOnStationDetailMapTestCase(SeleniumTestCase):

    markers = PageElement(By.CSS_SELECTOR, ".leaflet-marker-pane")

    def setUp(self):
        mommy.make(Station, name="West", geom=Point(x=23.0, y=38.0, srid=4326))
        self.station = mommy.make(
            Station, name="Middle", geom=Point(x=23.001, y=38.0, srid=4326)
        )
        mommy.make(Station, name="East", geom=Point(x=23.002, y=38.0, srid=4326))

    def test_shows_a_single_station_in_station_detail(self):
        self.selenium.get(
            "{}/stations/{}/".format(self.live_server_url, self.station.id)
        )
        num_stations_shown = self._get_num_stations_shown()
        self.assertEqual(num_stations_shown, 1)

    def _get_num_stations_shown(self):
        self.markers.wait_until_exists()
        for i in range(6):
            result = len(self.markers.find_elements_by_tag_name("img"))
            if result:
                return result
            sleep(0.5)
        return 0
