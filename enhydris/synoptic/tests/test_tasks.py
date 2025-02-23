import datetime as dt
import locale
import os
import shutil
import tempfile
from io import StringIO
from unittest import skipUnless
from urllib.parse import urlparse

from django.conf import settings
from django.core import mail
from django.core.cache import cache
from django.http import HttpResponse
from django.test import TestCase, override_settings

import numpy as np
from bs4 import BeautifulSoup
from django_selenium_clean import PageElement
from freezegun import freeze_time
from selenium.webdriver.common.by import By

from enhydris.synoptic import models
from enhydris.synoptic.tasks import create_static_files
from enhydris.tests import ClearCacheMixin, SeleniumTestCase

from .data import TestData


class RandomSynopticRoot(override_settings):
    """
    Override ENHYDRIS_SYNOPTIC_ROOT to a temporary directory.

    Specifying "@RandomSynopticRoot()" as a decorator is the same as
    "@override_settings(ENHYDRIS_SYNOPTIC_ROOT=tempfile.mkdtemp())", except
    that in the end it removes the temporary directory.
    """

    def __init__(self):
        self.tmpdir = tempfile.mkdtemp()
        super(RandomSynopticRoot, self).__init__(ENHYDRIS_SYNOPTIC_ROOT=self.tmpdir)

    def disable(self):
        super(RandomSynopticRoot, self).disable()
        shutil.rmtree(self.tmpdir)


def days_since_epoch(y, mo, d, h, mi):
    adelta = dt.datetime(y, mo, d, h, mi) - dt.datetime(1, 1, 1)
    return adelta.days + 1 + adelta.seconds / 86400.0


class AssertHtmlContainsMixin:
    def assertHtmlContains(self, filename, text):
        """Check if a file contains an HTML extract.

        This is pretty much the same as self.assertContains() with html=True,
        but uses a filename instead of a response.
        """
        # We implement it by converting to an HTTPResponse, because there is
        # no better way to use self.assertContains() to do the actual job.
        with open(filename, encoding="utf-8") as f:
            response = HttpResponse(f.read())
        self.assertContains(response, text, html=True)


@RandomSynopticRoot()
class MainPageTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.data = TestData()
        create_static_files()

    def test_timezone_message(self):
        root = settings.ENHYDRIS_SYNOPTIC_ROOT
        filename = os.path.join(root, "mygroup", "index.html")
        with open(filename) as f:
            output = f.read()
        self.assertIn("All times are in Etc/GMT-1", output)


@RandomSynopticRoot()
class ChartTestCase(ClearCacheMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.data = TestData()
        settings.TEST_MATPLOTLIB = True
        create_static_files()

    @classmethod
    def tearDownClass(self):
        settings.TEST_MATPLOTLIB = False
        super().tearDownClass()

    def test_chart(self):
        # We will not compare a bitmap because it is unreliable; instead, we
        # will verify that an image was created and that the data that was used
        # in the image creation was correct. See
        # http://stackoverflow.com/questions/27948126#27948646

        # Check that it is a png of substantial length
        filename = os.path.join(
            settings.ENHYDRIS_SYNOPTIC_ROOT, "chart", str(self.data.stsg2_2.id) + ".png"
        )
        self.assertTrue(filename.endswith(".png"))
        self.assertGreater(os.stat(filename).st_size, 100)

        # Retrieve data
        datastr = open(filename.replace("png", "dat")).read()
        self.assertTrue(datastr.startswith("(array("))
        datastr = datastr.replace("array", "np.array")
        data_array = eval(datastr)

        # Check that the data is correct
        desired_result = np.array(
            [
                [days_since_epoch(2015, 10, 23, 15, 00), 40],
                [days_since_epoch(2015, 10, 23, 15, 10), 39],
                [days_since_epoch(2015, 10, 23, 15, 20), 38.5],
            ]
        )
        np.testing.assert_allclose(data_array, desired_result, rtol=1e-6)

    def test_grouped_chart(self):
        # Here we test the wind speed chart, which is grouped with wind gust.
        # See the comment in test_chart() above; the same applies here.

        # Check that it is a png of substantial length
        filename = os.path.join(
            settings.ENHYDRIS_SYNOPTIC_ROOT, "chart", str(self.data.stsg1_3.id) + ".png"
        )
        self.assertTrue(filename.endswith(".png"))
        self.assertGreater(os.stat(filename).st_size, 100)

        # Retrieve data
        datastr = open(filename.replace("png", "dat")).read()
        self.assertTrue(datastr.startswith("(array("))
        datastr = datastr.replace("array", "np.array")
        data_array = eval(datastr)

        desired_result = (
            np.array(
                [
                    [days_since_epoch(2015, 10, 22, 15, 00), 3.7],
                    [days_since_epoch(2015, 10, 22, 15, 10), 4.5],
                    [days_since_epoch(2015, 10, 22, 15, 20), 4.1],
                ]
            ),
            np.array(
                [
                    [days_since_epoch(2015, 10, 22, 15, 00), 2.9],
                    [days_since_epoch(2015, 10, 22, 15, 10), 3.2],
                    [days_since_epoch(2015, 10, 22, 15, 20), 3],
                ]
            ),
        )
        np.testing.assert_allclose(data_array[0], desired_result[0], rtol=1e-6)
        np.testing.assert_allclose(data_array[1], desired_result[1], rtol=1e-6)


@RandomSynopticRoot()
class StationReportTestCase(ClearCacheMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.data = TestData()
        create_static_files()
        filename = os.path.join(
            settings.ENHYDRIS_SYNOPTIC_ROOT,
            cls.data.sg1.slug,
            "station",
            str(cls.data.sgs_agios.station.id),
            "index.html",
        )
        with open(filename) as f:
            cls.soup = BeautifulSoup(f, "html.parser")
        cls.labels = cls.soup.find("dl").find_all("dt")
        cls.values = cls.soup.find("dl").find_all("dd")

    def _check(self, i, expected_label, expected_value):
        self.assertEqual(self.labels[i].contents[0].strip(), expected_label)
        self.assertEqual(self.values[i].contents[0].strip(), expected_value)

    def test_date(self):
        self._check(0, "Last update", "23 Oct 2015 15:20 (+0200)")

    def test_rain(self):
        self._check(2, "Rain", "0.2 mm")

    def test_temperature(self):
        self._check(3, "Air temperature", "38.5 °C")

    def test_wind(self):
        self._check(4, "Wind speed", "")


@RandomSynopticRoot()
class AsciiSystemLocaleTestCase(ClearCacheMixin, AssertHtmlContainsMixin, TestCase):
    def setUp(self):
        self.saved_locale = locale.setlocale(locale.LC_CTYPE)
        locale.setlocale(locale.LC_CTYPE, "C")
        self.data = TestData()

    def tearDown(self):
        locale.setlocale(locale.LC_CTYPE, self.saved_locale)

    def test_uses_utf8_regardless_locale_setting(self):
        create_static_files()
        filename = os.path.join(
            settings.ENHYDRIS_SYNOPTIC_ROOT,
            self.data.sg1.slug,
            "station",
            str(self.data.sgs_agios.station.id),
            "index.html",
        )
        self.assertHtmlContains(filename, "Άγιος Αθανάσιος")


class EarlyWarningTestMixin:
    def _set_limits(self, low_temperature, high_gust):
        self.data.stsg1_4.high_limit = high_gust
        self.data.stsg1_4.save()
        self.data.stsg1_2.low_limit = low_temperature
        self.data.stsg1_2.save()


class MapTestCaseMixin(EarlyWarningTestMixin):
    komboti_div_icon_xpath = (
        '//div[contains(@class, "leaflet-div-icon") and .//a/text()="Komboti"]'
    )
    komboti_div_icon = PageElement(By.XPATH, komboti_div_icon_xpath)
    layer_control = PageElement(By.XPATH, '//a[@class="leaflet-control-layers-toggle"]')
    layer_control_rain = PageElement(
        By.XPATH,
        (
            '//label[input[@class="leaflet-control-layers-selector"] '
            'and span/text()=" Rain"]'
        ),
    )
    layer_control_temperature = PageElement(
        By.XPATH,
        (
            '//label[input[@class="leaflet-control-layers-selector"] '
            'and span/text()=" Air temperature"]'
        ),
    )
    layer_control_wind_gust = PageElement(
        By.XPATH,
        (
            '//label[input[@class="leaflet-control-layers-selector"] '
            'and span/text()=" Wind (gust)"]'
        ),
    )

    def setUp(self):
        self.data = TestData()
        settings.TEST_MATPLOTLIB = True
        self._setup_synoptic_root()
        cache.clear()

    def tearDown(self):
        self._teardown_synoptic_root()
        settings.TEST_MATPLOTLIB = False

    def _setup_synoptic_root(self):
        # We create synoptic root inside static files so that it will be served by
        # the live server during testing (otherwise relative links to js/css/etc won't
        # work)
        this_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(this_dir)
        static_dir = os.path.join(parent_dir, "static")
        self.synoptic_root = tempfile.mkdtemp(
            prefix=os.path.join(static_dir, "synoptic")
        )
        self.saved_synoptic_root = settings.ENHYDRIS_SYNOPTIC_ROOT
        self.saved_synoptic_url = settings.ENHYDRIS_SYNOPTIC_URL
        settings.ENHYDRIS_SYNOPTIC_ROOT = self.synoptic_root
        settings.ENHYDRIS_SYNOPTIC_URL = (
            f"{self.live_server_url}/static/{os.path.basename(self.synoptic_root)}/"
        )

    def _teardown_synoptic_root(self):
        settings.ENHYDRIS_SYNOPTIC_URL = self.saved_synoptic_url
        settings.ENHYDRIS_SYNOPTIC_ROOT = self.saved_synoptic_root
        shutil.rmtree(self.synoptic_root)

    def _get_synoptic_page(self):
        create_static_files()
        self.selenium.get(
            f"{settings.ENHYDRIS_SYNOPTIC_URL}{self.data.sg1.slug}/index.html"
        )


@skipUnless(getattr(settings, "SELENIUM_WEBDRIVERS", False), "Selenium is unconfigured")
@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
    SITE_ID=1,
    ENHYDRIS_SITES_FOR_NEW_STATIONS=set(),
)
class OutdatedDateRedTestCase(MapTestCaseMixin, SeleniumTestCase):

    @freeze_time("2015-10-22 14:20:01")
    def test_outdated_date_shows_red(self):
        self._get_synoptic_page()
        self.komboti_div_icon.wait_until_is_displayed(1)
        date = self.komboti_div_icon.find_element(By.TAG_NAME, "span")
        self.assertEqual(date.get_attribute("class"), "date old")


@skipUnless(getattr(settings, "SELENIUM_WEBDRIVERS", False), "Selenium is unconfigured")
@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
    SITE_ID=1,
    ENHYDRIS_SITES_FOR_NEW_STATIONS=set(),
)
class UpToDateGreenTestCase(MapTestCaseMixin, SeleniumTestCase):
    @freeze_time("2015-10-22 14:19:59")
    def test_up_to_date_date_shows_green(self):
        self._get_synoptic_page()
        self.komboti_div_icon.wait_until_is_displayed()
        date = self.komboti_div_icon.find_element(By.TAG_NAME, "span")
        self.assertEqual(date.get_attribute("class"), "date recent")


@skipUnless(getattr(settings, "SELENIUM_WEBDRIVERS", False), "Selenium is unconfigured")
@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
    SITE_ID=1,
    ENHYDRIS_SITES_FOR_NEW_STATIONS=set(),
)
class DateFormatTestCase(MapTestCaseMixin, SeleniumTestCase):
    @freeze_time("2015-10-22 14:19:59")
    def test_date_format(self):
        self._get_synoptic_page()
        self.komboti_div_icon.wait_until_is_displayed()
        date = self.komboti_div_icon.find_element(By.TAG_NAME, "span")
        self.assertEqual(date.text, "22 Oct 2015 14:20")


@skipUnless(getattr(settings, "SELENIUM_WEBDRIVERS", False), "Selenium is unconfigured")
@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
    SITE_ID=1,
    ENHYDRIS_SITES_FOR_NEW_STATIONS=set(),
)
class ValueStatusTestCase(MapTestCaseMixin, SeleniumTestCase):
    def test_value_status(self):
        self._set_limits(low_temperature=17.1, high_gust=4)
        self._get_synoptic_page()
        self.layer_control.wait_until_is_displayed()
        self.layer_control.click()
        self.layer_control_rain.wait_until_is_displayed()

        # Rain should be ok
        self.layer_control_rain.click()
        xpath = f'{self.komboti_div_icon_xpath}//span[contains(@class, "value ok")]'
        value_element = PageElement(By.XPATH, xpath)
        value_element.wait_until_exists()
        self.assertEqual(value_element.get_attribute("class"), "value ok")

        # Wind gust should be high
        self.layer_control_wind_gust.click()
        xpath = f'{self.komboti_div_icon_xpath}//span[contains(@class, "value high")]'
        value_element = PageElement(By.XPATH, xpath)
        value_element.wait_until_exists()
        self.assertEqual(value_element.get_attribute("class"), "value high")

        # Temperature should be low
        self.layer_control_temperature.click()
        xpath = f'{self.komboti_div_icon_xpath}//span[contains(@class, "value low")]'
        value_element = PageElement(By.XPATH, xpath)
        value_element.wait_until_exists()
        self.assertEqual(value_element.get_attribute("class"), "value low")


@skipUnless(getattr(settings, "SELENIUM_WEBDRIVERS", False), "Selenium is unconfigured")
@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
    SITE_ID=1,
    ENHYDRIS_SITES_FOR_NEW_STATIONS=set(),
    ENHYDRIS_SYNOPTIC_STATION_LINK_TARGET="/hello{station.id}world",
)
class StationLinkTargetTestCase(MapTestCaseMixin, SeleniumTestCase):
    def test_station_link_target(self):
        self._get_synoptic_page()
        self.komboti_div_icon.wait_until_is_displayed()
        a_element = self.komboti_div_icon.find_element(By.TAG_NAME, "a")
        href = a_element.get_attribute("href")
        self.assertEqual(
            urlparse(href).path, f"/hello{self.data.station_komboti.id}world"
        )


@RandomSynopticRoot()
class EmptyTimeseriesTestCase(ClearCacheMixin, TestCase):
    def setUp(self):
        self.data = TestData()
        settings.TEST_MATPLOTLIB = True
        self.data.tsg_komboti_temperature.default_timeseries.set_data(StringIO(""))
        create_static_files()

    def test_chart(self):
        # Check that the chart is a png of substantial length
        filename = os.path.join(
            settings.ENHYDRIS_SYNOPTIC_ROOT, "chart", str(self.data.stsg1_2.id) + ".png"
        )
        self.assertTrue(filename.endswith(".png"))
        self.assertGreater(os.stat(filename).st_size, 100)

        # Check that the array was made from empty data
        datastr = open(filename.replace("png", "dat")).read()
        self.assertEqual(datastr, "()")


@RandomSynopticRoot()
class TimeseriesWithOneRecordTestCase(ClearCacheMixin, TestCase):
    def setUp(self):
        self.data = TestData()
        settings.TEST_MATPLOTLIB = True
        self.data.tsg_komboti_temperature.default_timeseries.set_data(
            StringIO("2015-10-22 15:10,0,\n"), default_timezone="Etc/GMT-2"
        )
        create_static_files()

    def test_chart(self):
        # Check that the chart is a png of substantial length
        filename = os.path.join(
            settings.ENHYDRIS_SYNOPTIC_ROOT, "chart", str(self.data.stsg1_2.id) + ".png"
        )
        self.assertTrue(filename.endswith(".png"))
        self.assertGreater(os.stat(filename).st_size, 100)

        # Check that the array was made from empty data
        datastr = open(filename.replace("png", "dat")).read()
        self.assertEqual(datastr, "()")


@RandomSynopticRoot()
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class EmailTestCase(ClearCacheMixin, TestCase, EarlyWarningTestMixin):
    def setUp(self):
        self.data = TestData()

    def test_sends_email_if_emails_are_registered(self):
        self._set_limits(low_temperature=17.1, high_gust=4)
        models.EarlyWarningEmail.objects.create(
            synoptic_group=self.data.sg1, email="someone@blackhole.com"
        )
        create_static_files()
        self.assertEqual(len(mail.outbox), 1)

    def test_does_not_send_email_if_no_emails_are_registered(self):
        self._set_limits(low_temperature=17.1, high_gust=4)
        create_static_files()
        self.assertEqual(len(mail.outbox), 0)

    def test_does_not_send_email_if_limits_are_not_exceeded(self):
        models.EarlyWarningEmail.objects.create(
            synoptic_group=self.data.sg1, email="someone@blackhole.com"
        )
        self._set_limits(low_temperature=10, high_gust=5)
        create_static_files()
        self.assertEqual(len(mail.outbox), 0)


@RandomSynopticRoot()
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="noreply@enhydris.com",
)
class EmailContentTestCase(ClearCacheMixin, TestCase, EarlyWarningTestMixin):
    @classmethod
    def setUpTestData(cls):
        cls.data = TestData()
        cls._set_limits(cls, low_temperature=17.1, high_gust=4)
        models.EarlyWarningEmail.objects.create(
            synoptic_group=cls.data.sg1, email="someone@blackhole.com"
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_static_files()
        cls.message = mail.outbox[0].message()

    def test_subject(self):
        self.assertEqual(self.message["Subject"], "Enhydris early warning (Komboti)")

    def test_from(self):
        self.assertEqual(self.message["From"], "noreply@enhydris.com")

    def test_to(self):
        self.assertEqual(self.message["To"], "someone@blackhole.com")

    def test_payload(self):
        self.assertEqual(
            self.message.get_payload(),
            "Komboti Air temperature 2015-10-22 15:20 17.0 (low limit 17.1)\n"
            "Komboti Wind 2015-10-22 15:20 4.1 (high limit 4.0)\n",
        )


class EmailSubjectTestCase(TestCase):
    def test_subject(self):
        synoptic_group = models.SynopticGroup()
        synoptic_group.early_warnings = {
            "one": {"station": "Komboti"},
            "two": {"station": "Agios Spyridon"},
        }
        expected_subject = "Enhydris early warning (Agios Spyridon, Komboti)"
        self.assertEqual(synoptic_group._get_warning_email_subject(), expected_subject)


@RandomSynopticRoot()
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="noreply@enhydris.com",
)
class RoccEmailContentTestCase(ClearCacheMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.data = TestData()
        cls.data.stsg1_2.set_roc_thresholds("10min 0.5")
        models.EarlyWarningEmail.objects.create(
            synoptic_group=cls.data.sg1, email="someone@blackhole.com"
        )

    def test_payload(self):
        create_static_files()
        message = mail.outbox[0].message()
        self.assertEqual(
            message.get_payload(),
            "Komboti Air temperature 2015-10-22T15:20  +1.0 in 10min (> 0.5)\n",
        )
