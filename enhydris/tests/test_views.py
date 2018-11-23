import shutil
import tempfile
import textwrap
import time
from io import StringIO
from unittest import skip, skipUnless
from zipfile import ZipFile

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point, fromstr
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from django_selenium_clean import PageElement, SeleniumTestCase
from model_mommy import mommy
from selenium.webdriver.common.by import By

from enhydris.models import (
    Organization,
    Station,
    StationType,
    Timeseries,
    TimeZone,
    UnitOfMeasurement,
    Variable,
)


class StationsTestCase(TestCase):
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
            srid=4326,
        )
        mommy.make(
            Station,
            name="Agios Athanasios",
            point=Point(x=21.60121, y=39.22440, srid=4326),
            srid=4326,
        )
        mommy.make(
            Station,
            name="Tharbad",
            point=Point(x=-176.48368, y=0.19377, srid=4326),
            srid=4326,
        )
        mommy.make(
            Station,
            name="SRID Point, NoSRID Station",
            point=Point(x=-176.48368, y=0.19377, srid=4326),
            srid=None,
        )
        mommy.make(
            Station,
            name="NoSRID Point, SRID Station",
            point=Point(x=-176.48368, y=0.19377, srid=None),
            srid=4326,
        )
        mommy.make(
            Station,
            name="NoSRID Point, NoSRID Station",
            point=Point(x=-176.48368, y=0.19377, srid=None),
            srid=None,
        )

    def test_station_list_csv(self):
        response = self.client.get("/?format=csv")
        with tempfile.TemporaryFile() as t:
            t.write(response.content)
            with ZipFile(t) as f:
                stations_csv = f.open("stations.csv").read().decode()
                self.assertTrue(",Agios Athanasios," in stations_csv)

    def test_station_list_csv_station_no_srid(self):
        response = self.client.get("/?format=csv")
        with tempfile.TemporaryFile() as t:
            t.write(response.content)
            with ZipFile(t) as f:
                stations_csv = f.open("stations.csv").read().decode()
                self.assertTrue("SRID Point, NoSRID Station" in stations_csv)

    def test_station_list_csv_point_no_srid(self):
        response = self.client.get("/?format=csv")
        with tempfile.TemporaryFile() as t:
            t.write(response.content)
            with ZipFile(t) as f:
                stations_csv = f.open("stations.csv").read().decode()
                self.assertTrue("NoSRID Point, SRID Station" in stations_csv)

    def test_station_list_csv_station_and_point_with_no_srid(self):
        response = self.client.get("/?format=csv")
        with tempfile.TemporaryFile() as t:
            t.write(response.content)
            with ZipFile(t) as f:
                stations_csv = f.open("stations.csv").read().decode()
                self.assertTrue("NoSRID Point, NoSRID Station" in stations_csv)


class SortTestCase(TestCase):
    def setUp(self):
        mommy.make(
            Station, name="Komboti", water_division__name="North Syldavia Basins"
        )
        mommy.make(
            Station,
            name="Agios Athanasios",
            water_division__name="South Syldavia Basins",
        )
        mommy.make(
            Station, name="Tharbad", water_division__name="South Syldavia Basins"
        )

    def test_sort(self):
        # Request for host.domain/?sort=water_division&sort=name
        response = self.client.get(
            reverse("station_list") + "?sort=water_division&sort=name"
        )

        # Checking  test stations 'Komboti', 'Agios Athanasios', 'Tharbad'
        # alphabetical order ['water_division', 'name']
        i = response.content.decode("utf-8").index
        self.assertTrue(i("Komboti") < i("Agios Athanasios") < i("Tharbad"))

    def test_invalid_sort(self):
        # Request for host.domain/?sort=999.9
        response = self.client.get(reverse("station_list") + "?sort=999.9")

        # Sort is only made with default ['name'] term
        # Checking  test stations 'Komboti', 'Tharbad' alphabetical order index
        i = response.content.decode("utf-8").index
        self.assertLess(i("Komboti"), i("Tharbad"))

        # Order for host.domain/?sort=name&sort=999.9
        response = self.client.get(reverse("station_list") + "?sort=name&sort=999.9")

        # Order is only made with default ['name'] term
        # Checking  test stations 'Komboti', 'Tharbad' alphabetical order index
        i = response.content.decode("utf-8").index
        self.assertLess(i("Komboti"), i("Tharbad"))


class RandomEnhydrisTimeseriesDataDir(override_settings):
    """
    Override ENHYDRIS_TIMESERIES_DATA_DIR to a temporary directory.

    Specifying "@RandomEnhydrisTimeseriesDataDir()" as a decorator is the same
    as "@override_settings(ENHYDRIS_TIMESERIES_DATA_DIR=tempfile.mkdtemp())",
    except that in the end it removes the temporary directory.
    """

    def __init__(self):
        self.tmpdir = tempfile.mkdtemp()
        super().__init__(ENHYDRIS_TIMESERIES_DATA_DIR=self.tmpdir)

    def disable(self):
        super().disable()
        shutil.rmtree(self.tmpdir)


class RandomMediaRoot(override_settings):
    """
    Override MEDIA_ROOT to a temporary directory.

    Specifying "@RandomMediaRoot()" as a decorator is the same as
    "@override_settings(MEDIA_ROOT=tempfile.mkdtemp())", except that in the
    end it removes the temporary directory.
    """

    def __init__(self):
        self.tmpdir = tempfile.mkdtemp()
        super(RandomMediaRoot, self).__init__(MEDIA_ROOT=self.tmpdir)

    def disable(self):
        super(RandomMediaRoot, self).disable()
        shutil.rmtree(self.tmpdir)


class TsTestCase(TestCase):
    """Test timeseries data upload/download code."""

    def setUp(self):
        mommy.make(
            User,
            username="admin",
            password=make_password("topsecret"),
            is_active=True,
            is_superuser=True,
            is_staff=True,
        )
        self.stype = StationType.objects.create(descr="stype")
        self.stype.save()
        self.organization = Organization.objects.create(name="org")
        self.organization.save()
        self.var = Variable.objects.create(descr="var")
        self.var.save()
        self.unit = UnitOfMeasurement.objects.create(symbol="+")
        self.unit.variables.add(self.var)
        self.unit.save()
        self.tz = TimeZone.objects.create(code="EET", utc_offset=120)
        self.tz.save()
        self.station = Station.objects.create(
            name="station",
            owner=self.organization,
            approximate=False,
            is_automatic=True,
            point=fromstr("POINT(24.67890 38.12345)"),
            srid=4326,
            altitude=219.22,
        )
        self.station.save()
        self.ts = Timeseries(
            name="tstest",
            gentity=self.station,
            time_zone=self.tz,
            unit_of_measurement=self.unit,
            variable=self.var,
            precision=1,
        )
        self.ts.save()
        self.user = User.objects.create_user("test", "test@test.com", "test")
        self.user.save()

    @RandomEnhydrisTimeseriesDataDir()
    def test_timeseries_with_timezone_data(self):
        """Test that there's no aware/naive date confusion

        There was this bug where you'd ask to download from start date,
        and the start date was interpreted as aware whereas the time series
        data was interpreted as naive. This test checks there's no such
        bug.
        """
        data = textwrap.dedent(
            """\
                               2005-08-23 18:53,93,
                               2005-08-23 19:53,108.7,
                               2005-08-23 20:53,28.3,
                               2005-08-23 21:53,1.7,
                               2005-08-23 22:53,42.4,
            """
        )
        self.ts.set_data(StringIO(data))
        url = "/timeseries/d/{}/download/2005-08-23T19:54/".format(self.ts.pk)
        if not settings.ENHYDRIS_TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS:
            self.client.login(username="test", password="test")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        result = response.content.decode("utf-8")

        # Remove header, leave only data
        emptylinepos = result.find("\r\n\r\n")
        self.assertTrue(emptylinepos > 0)
        b = emptylinepos + 4
        result = result[b:]

        self.assertEqual(
            result,
            textwrap.dedent(
                """\
                                                 2005-08-23 20:53,28.3,\r
                                                 2005-08-23 21:53,1.7,\r
                                                 2005-08-23 22:53,42.4,\r
                                                 """
            ),
        )


class RegisterTestCase(TestCase):
    """
    Test that "Register" link appears depending on REGISTRATION_OPEN setting.
    """

    @override_settings(REGISTRATION_OPEN=False)
    def test_register_link_absent(self):
        response = self.client.get("/")
        self.assertNotContains(response, "Register")

    @skip("Would fail because this functionality does not exist yet")
    @override_settings(REGISTRATION_OPEN=True)
    def test_register_link_present(self):
        response = self.client.get("/")
        self.assertContains(response, "Register")


@skipUnless(getattr(settings, "SELENIUM_WEBDRIVERS", False), "Selenium is unconfigured")
class CoordinatesTestCase(SeleniumTestCase):

    # Elements in "Edit Station" view
    label_ordinate = PageElement(By.XPATH, '//label[@for="id_ordinate"]')
    field_ordinate = PageElement(By.ID, "id_ordinate")
    label_abscissa = PageElement(By.XPATH, '//label[@for="id_abscissa"]')
    field_abscissa = PageElement(By.ID, "id_abscissa")
    field_srid = PageElement(By.ID, "id_srid")
    field_altitude = PageElement(By.ID, "id_altitude")
    field_asrid = PageElement(By.ID, "id_asrid")
    field_approximate = PageElement(By.ID, "id_approximate")
    button_coordinates = PageElement(By.ID, "btnCoordinates")
    field_stype = PageElement(By.ID, "id_stype")
    stype_option_important = PageElement(
        By.XPATH, '//select[@id="id_stype"]/option[text()="Important"]'
    )
    field_owner = PageElement(By.ID, "id_owner")
    owner_option_big_tomatoes = PageElement(
        By.XPATH, '//select[@id="id_owner"]/option[text()="Big tomatoes"]'
    )
    field_copyright_holder = PageElement(By.ID, "id_copyright_holder")
    field_copyright_years = PageElement(By.ID, "id_copyright_years")
    button_submit = PageElement(By.XPATH, '//button[@type="submit"]')

    # Elements in "View Station" view
    button_edit = PageElement(
        By.XPATH,
        '//a[starts-with(@class, "btn") and ' 'starts-with(@href, "/stations/edit/")]',
    )

    def setUp(self):
        mommy.make(
            User,
            username="admin",
            password=make_password("topsecret"),
            is_active=True,
            is_superuser=True,
            is_staff=True,
        )
        mommy.make(StationType, descr="Important")
        mommy.make(Organization, name="Big tomatoes")

    @skip("Would fail because this functionality does not exist yet")
    @override_settings(DEBUG=True)
    def test_coordinates(self):
        # Login
        self.selenium.get(self.live_server_url + "/accounts/login/")
        PageElement(By.ID, "id_username").wait_until_is_displayed()
        PageElement(By.ID, "id_username").send_keys("admin")
        PageElement(By.ID, "id_password").send_keys("topsecret")
        submit_button = PageElement(By.XPATH, '//button[@type="submit"]')
        submit_button.click()

        # Go to the add new station page and check that the simple view is
        # active
        self.selenium.get(self.live_server_url + "/stations/add/")
        self.label_ordinate.wait_until_contains("Latitude")
        self.assertEqual(self.label_ordinate.text, "Latitude")
        self.assertEqual(self.label_abscissa.text, "Longitude")
        self.assertFalse(self.field_srid.is_displayed())
        self.assertFalse(self.field_asrid.is_displayed())
        self.assertFalse(self.field_approximate.is_displayed())

        # Switch to the advanced view and check it's ok
        self.button_coordinates.click()
        self.label_ordinate.wait_until_contains("Ordinate")
        self.assertEqual(self.label_ordinate.text, "Ordinate")
        self.assertEqual(self.label_abscissa.text, "Abscissa")
        self.assertTrue(self.field_srid.is_displayed())
        self.assertTrue(self.field_asrid.is_displayed())
        self.assertTrue(self.field_approximate.is_displayed())
        self.assertEqual(self.field_srid.get_attribute("value"), "4326")

        # Go back to the simple view and check it's ok
        self.button_coordinates.click()
        self.label_ordinate.wait_until_contains("Latitude")
        self.assertEqual(self.label_ordinate.text, "Latitude")
        self.assertEqual(self.label_abscissa.text, "Longitude")
        self.assertFalse(self.field_srid.is_displayed())
        self.assertFalse(self.field_asrid.is_displayed())
        self.assertFalse(self.field_approximate.is_displayed())

        # Enter a latitude and longitude and other data and submit
        self.field_ordinate.send_keys("37.97522")
        self.field_abscissa.send_keys("23.73700")
        self.stype_option_important.click()
        self.owner_option_big_tomatoes.click()
        self.field_copyright_holder.send_keys("Alice")
        self.field_copyright_years.send_keys("2015")
        self.selenium.execute_script(
            """document.evaluate('//button[@type="submit"]', document, null,
            XPathResult.FIRST_ORDERED_NODE_TYPE, null)
            .singleNodeValue.scrollIntoView()"""
        )
        self.button_submit.click()

        # Wait for the response, then go to edit the station and check that
        # it's the simple view
        self.button_edit.wait_until_is_displayed()
        self.button_edit.click()
        self.label_ordinate.wait_until_contains("Latitude")
        self.assertEqual(self.label_ordinate.text, "Latitude")
        self.assertEqual(self.label_abscissa.text, "Longitude")
        self.assertFalse(self.field_srid.is_displayed())
        self.assertFalse(self.field_asrid.is_displayed())
        self.assertFalse(self.field_approximate.is_displayed())
        self.assertEqual(self.field_ordinate.get_attribute("value"), "37.97522")
        self.assertEqual(self.field_abscissa.get_attribute("value"), "23.737")

        # Switch to the advanced view
        self.button_coordinates.click()
        self.label_ordinate.wait_until_contains("Ordinate")
        self.assertEqual(self.label_ordinate.text, "Ordinate")
        self.assertEqual(self.label_abscissa.text, "Abscissa")
        self.assertTrue(self.field_srid.is_displayed())
        self.assertTrue(self.field_asrid.is_displayed())
        self.assertTrue(self.field_approximate.is_displayed())
        self.assertEqual(self.field_srid.get_attribute("value"), "4326")

        # Enter some advanced data and submit
        self.field_ordinate.clear()
        self.field_ordinate.send_keys("4202810.33")
        self.field_abscissa.clear()
        self.field_abscissa.send_keys("476751.84")
        self.field_srid.clear()
        self.field_srid.send_keys("2100")
        self.selenium.execute_script(
            """document.evaluate('//button[@type="submit"]', document, null,
            XPathResult.FIRST_ORDERED_NODE_TYPE, null)
            .singleNodeValue.scrollIntoView()"""
        )
        self.button_submit.click()

        # Go to the edit page again, and check that the advanced view shows
        self.button_edit.wait_until_is_displayed()
        self.button_edit.click()
        self.label_ordinate.wait_until_is_displayed()
        time.sleep(1)  # Wait for JavaScript to take action
        self.assertEqual(self.label_ordinate.text, "Ordinate")
        self.assertEqual(self.label_abscissa.text, "Abscissa")
        self.assertTrue(self.field_srid.is_displayed())
        self.assertTrue(self.field_asrid.is_displayed())
        self.assertTrue(self.field_approximate.is_displayed())
        self.assertEqual(self.field_srid.get_attribute("value"), "2100")
        self.assertEqual(self.field_ordinate.get_attribute("value"), "4202810.33")
        self.assertEqual(self.field_abscissa.get_attribute("value"), "476751.84")

        # It should be impossible to change to the simple view
        self.assertFalse(self.button_coordinates.is_displayed())


@skip("Would fail because this functionality does not exist yet")
@skipUnless(getattr(settings, "SELENIUM_WEBDRIVERS", False), "Selenium is unconfigured")
class ListStationsVisibleOnMapTestCase(SeleniumTestCase):

    button_limit_to_map = PageElement(By.ID, "limit-to-map")
    td_komboti = PageElement(By.XPATH, '//td[text()="Komboti"]')
    td_agios_athanasios = PageElement(By.XPATH, '//td[text()="Agios Athanasios"]')
    td_tharbad = PageElement(By.XPATH, '//td[text()="Tharbad"]')

    def setUp(self):
        mommy.make(
            Station,
            name="Komboti",
            point=Point(x=21.06071, y=39.09518, srid=4326),
            srid=4326,
        )
        mommy.make(
            Station,
            name="Agios Athanasios",
            point=Point(x=21.60121, y=39.22440, srid=4326),
            srid=4326,
        )
        mommy.make(
            Station,
            name="Tharbad",
            point=Point(x=-176.48368, y=0.19377, srid=4326),
            srid=4326,
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
