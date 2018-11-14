from io import StringIO
import json
import re
import shutil
import tempfile
import textwrap
import time
from unittest import skip, skipIf, skipUnless
from urllib.parse import urlencode
from zipfile import ZipFile

import django
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.contrib.gis.geos import fromstr, Point
from django.db import connections
from django.db.utils import DEFAULT_DB_ALIAS
from django.http import Http404, HttpRequest, QueryDict
from django.test import TestCase
from django.test.utils import override_settings

from bs4 import BeautifulSoup
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
    UserProfile,
    Variable,
)
from enhydris.tests.test_models import RandomEnhydrisTimeseriesDataDir
from enhydris.views import StationListBaseView


def check_if_connected_to_old_sqlite():
    """Return True if connected to sqlite<3.8.3

    Used to skip a test, notably on Travis, which currently runs an old sqlite
    version.

    The correct way would have been to remove the functionality, not just skip
    the test, because the functionality is still there and will cause an
    internal server error, but this would be too much work given that we use
    SQLite only for development.
    """
    try:
        from django.contrib.gis.db.backends.spatialite import base
        import sqlite3
    except ImportError:
        return False
    if not isinstance(connections[DEFAULT_DB_ALIAS], base.DatabaseWrapper):
        return False
    major, minor, micro = [int(x) for x in sqlite3.sqlite_version.split(".")[:3]]
    return (
        (major < 3)
        or (major == 3 and minor < 8)
        or (major == 3 and minor == 8 and micro < 3)
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

    def test_station_list(self):
        response = self.client.get("/")
        self.assertContains(
            response, '<a href="?sort=-name&amp;sort=name">Name&nbsp;↓</a>', html=True
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


class SearchTestCaseBase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Station owners
        rich = mommy.make(Organization, name="We're rich and we fancy it SA")
        poor = mommy.make(Organization, name="We're poor and dislike it Ltd")

        # Create three stations
        station_komboti = mommy.make(
            Station,
            name="Komboti",
            owner=poor,
            political_division__name="Arta",
            political_division__parent__name="Epirus",
            political_division__parent__parent__name="Greece",
            stype__descr="Important",
            water_basin__name="Arachthos",
            water_division__name="North Syldavia Basins",
        )
        greece = station_komboti.political_division.parent.parent
        station_ai_thanassis = mommy.make(
            Station,
            name="Agios Athanasios",
            owner=poor,
            political_division__name="Karditsa",
            political_division__parent__name="Thessaly",
            political_division__parent__parent=greece,
            stype__descr=["Important", "Unimportant"],
            water_division__name="South Syldavia Basins",
        )
        station_tharbad = mommy.make(
            Station,
            name="Tharbad",
            owner=rich,
            political_division__name="Cardolan",
            political_division__parent__name="Eriador",
            political_division__parent__parent__name="Middle Earth",
            stype__descr=["Unimportant"],
            water_basin__name="Greyflood",
            water_division__name="South Syldavia Basins",
        )

        # A time zone
        timezone = mommy.make(TimeZone, code="UTC", utc_offset=0)

        # Five time series
        cls.komboti_temperature = mommy.make(
            Timeseries,
            name="Air temperature",
            variable__descr="Temperature",
            gentity=station_komboti,
            time_zone=timezone,
        )
        cls.komboti_rain = mommy.make(
            Timeseries,
            name="Rain",
            gentity=station_komboti,
            variable__descr="Rain",
            time_zone=timezone,
        )
        cls.ai_thanassis_temperature = mommy.make(
            Timeseries,
            name="Air temperature",
            gentity=station_ai_thanassis,
            variable=cls.komboti_temperature.variable,
            time_zone=timezone,
        )
        cls.ai_thanassis_rain = mommy.make(
            Timeseries,
            name="Rain",
            gentity=station_ai_thanassis,
            variable=cls.komboti_rain.variable,
            time_zone=timezone,
        )
        cls.tharbad_temperature = mommy.make(
            Timeseries,
            name="Temperature",
            gentity=station_tharbad,
            variable=cls.komboti_temperature.variable,
            remarks="This is an extremely important time series, "
            "just because it is hugely significant and markedly "
            "outstanding.",
            time_zone=timezone,
        )

        # And a station with no time series
        mommy.make(Station, name="Lefkada")

    def get_queryset(self, query_string):
        view = StationListBaseView()
        view.request = HttpRequest()
        view.request.method = "GET"
        view.request.GET = QueryDict(query_string)
        return view.get_queryset()


class SearchTestCase(SearchTestCaseBase):
    def test_search_in_timeseries_remarks(self):
        # Search for something that exists
        queryset = self.get_queryset(
            urlencode({"q": "extremely important time series"})
        )
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].name, "Tharbad")

        # Search for something that doesn't exist
        queryset = self.get_queryset(urlencode({"q": "this should not exist anywhere"}))
        self.assertEqual(queryset.count(), 0)

    def test_search_by_owner(self):
        queryset = self.get_queryset(urlencode({"q": "owner:RiCh"}))
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(
            queryset[0].owner.organization.name, "We're rich and we fancy it SA"
        )
        queryset = self.get_queryset(urlencode({"owner": "poor"}))
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(
            queryset[0].owner.organization.name, "We're poor and dislike it Ltd"
        )
        queryset = self.get_queryset(urlencode({"owner": "nonexistent"}))
        self.assertEqual(queryset.count(), 0)

    def test_search_by_type(self):
        # The following will find both "Important" and "Unimportant" stations,
        # because the string "important" is included in "Unimportant".
        queryset = self.get_queryset(urlencode({"q": "type:Important"}))
        queryset = queryset.distinct()
        self.assertEqual(queryset.count(), 3)

        queryset = self.get_queryset(urlencode({"type": "Unimportant"}))
        queryset = queryset.order_by("name")
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].name, "Agios Athanasios")
        self.assertEqual(queryset[1].name, "Tharbad")

        queryset = self.get_queryset(urlencode({"type": "Nonexistent"}))
        self.assertEqual(queryset.count(), 0)

    def test_search_by_water_division(self):
        queryset = self.get_queryset(urlencode({"q": "water_division:north"}))
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].name, "Komboti")

        queryset = self.get_queryset(urlencode({"q": "water_division:south"}))
        queryset = queryset.order_by("name")
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].name, "Agios Athanasios")
        self.assertEqual(queryset[1].name, "Tharbad")

        queryset = self.get_queryset(urlencode({"q": "water_division:east"}))
        self.assertEqual(queryset.count(), 0)

    def test_search_by_water_basin(self):
        queryset = self.get_queryset(urlencode({"q": "water_basin:arachthos"}))
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].name, "Komboti")

        queryset = self.get_queryset(urlencode({"water_basin": "greyflood"}))
        queryset = queryset.order_by("name")
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].name, "Tharbad")

        queryset = self.get_queryset(urlencode({"water_basin": "nonexistent"}))
        self.assertEqual(queryset.count(), 0)

    def test_search_by_variable(self):
        queryset = self.get_queryset(urlencode({"q": "variable:rain"}))
        queryset = queryset.order_by("name")
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].name, "Agios Athanasios")
        self.assertEqual(queryset[1].name, "Komboti")

        queryset = self.get_queryset(urlencode({"q": "variable:temperature"}))
        queryset = queryset.order_by("name")
        self.assertEqual(queryset.count(), 3)
        self.assertEqual(queryset[0].name, "Agios Athanasios")
        self.assertEqual(queryset[1].name, "Komboti")
        self.assertEqual(queryset[2].name, "Tharbad")

        queryset = self.get_queryset(urlencode({"q": "variable:nonexistent"}))
        self.assertEqual(queryset.count(), 0)

    def test_search_by_gentityId(self):
        station_id = Station.objects.get(name="Komboti").id
        queryset = self.get_queryset(urlencode({"gentityId": str(station_id)}))
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].name, "Komboti")

        queryset = self.get_queryset(urlencode({"gentityId": "98765"}))
        self.assertEqual(queryset.count(), 0)

    def test_search_by_ts_only(self):
        queryset = self.get_queryset("")
        self.assertEqual(queryset.count(), 4)
        queryset = self.get_queryset(urlencode({"q": "ts_only:"}))
        self.assertEqual(queryset.count(), 3)

    @skipIf(check_if_connected_to_old_sqlite(), "Use sqlite>=3.8.3")
    def test_search_by_political_division(self):
        queryset = self.get_queryset(urlencode({"political_division": "Cardolan"}))
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].name, "Tharbad")

        queryset = self.get_queryset(urlencode({"political_division": "Arthedain"}))
        self.assertEqual(queryset.count(), 0)

        queryset = self.get_queryset(urlencode({"political_division": "Karditsa"}))
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].name, "Agios Athanasios")

        queryset = self.get_queryset(urlencode({"political_division": "Arta"}))
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].name, "Komboti")

        queryset = self.get_queryset(urlencode({"political_division": "Epirus"}))
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].name, "Komboti")

        queryset = self.get_queryset(urlencode({"political_division": "Greece"}))
        queryset = queryset.order_by("name")
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].name, "Agios Athanasios")
        self.assertEqual(queryset[1].name, "Komboti")

        queryset = self.get_queryset(urlencode({"political_division": "Middle Earth"}))
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].name, "Tharbad")


@skipIf(
    settings.DATABASES["default"]["ENGINE"].endswith(".spatialite"),
    "This functionality is not available on spatialite",
)
@RandomEnhydrisTimeseriesDataDir()
class SearchTsHasYearsTestCase(SearchTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Add some timeseries data
        cls.komboti_temperature.set_data(
            StringIO(
                textwrap.dedent(
                    """\
            2005-08-23 18:53,93,
            2010-08-23 22:53,42.4,
            """
                )
            )
        )
        cls.komboti_rain.set_data(
            StringIO(
                textwrap.dedent(
                    """\
            2011-08-23 18:53,93,
            2015-08-23 22:53,42.4,
            """
                )
            )
        )
        cls.ai_thanassis_temperature.set_data(
            StringIO(
                textwrap.dedent(
                    """\
            2005-08-23 18:53,93,
            2010-08-23 22:53,42.4,
            """
                )
            )
        )
        cls.ai_thanassis_rain.set_data(
            StringIO(
                textwrap.dedent(
                    """\
            2009-08-23 18:53,93,
            2017-08-23 22:53,42.4,
            """
                )
            )
        )

    def test_search_with_year_existing_somewhere(self):
        queryset = self.get_queryset(urlencode({"ts_has_years": "2005,2012,2016"}))
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].name, "Agios Athanasios")

    def test_search_with_years_existing_everywhere(self):
        queryset = self.get_queryset(urlencode({"ts_has_years": "2005,2012"})).order_by(
            "name"
        )
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].name, "Agios Athanasios")
        self.assertEqual(queryset[1].name, "Komboti")

    def test_search_with_year_existing_nowhere(self):
        queryset = self.get_queryset(urlencode({"ts_has_years": "2005,2012,2018"}))
        self.assertEqual(queryset.count(), 0)

    def test_search_with_garbage(self):
        with self.assertRaises(Http404):
            self.get_queryset(urlencode({"ts_has_years": "hello,world"}))


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
        result = result[emptylinepos + 4 :]

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


class ProfileTestCase(TestCase):
    def test_profile(self):
        # Create a user
        self.auser = User.objects.create_user(
            username="auser", email="irrelevant@example.com", password="topsecret"
        )
        self.auser.save()
        profile = UserProfile.objects.get(user=self.auser)
        profile.fname = "A"
        profile.lname = "User"
        profile.address = "Nowhere"
        profile.email_is_public = True
        profile.save()

        # Create a second user
        self.buser = User.objects.create_user(
            username="buser",
            email="irrelevant_indeed@example.com",
            password="topsecret",
        )
        self.buser.save()

        # View the first user's profile
        response = self.client.get("/profile/auser/")
        self.assertContains(response, "irrelevant@example.com")

        # Prepare the post data that we will be attempting to post -
        # essentially this sets email_is_public to False.
        post_data = {
            "user": self.auser.id,
            "fname": "A",
            "lname": "User",
            "address": "Nowhere",
            "organization": "UN",
            "email_is_public": False,
        }

        # Try to modify first user's profile anonymously - should deny
        response = self.client.post("/profile/edit/", post_data)
        self.assertEqual(response.status_code, 200)

        # Try to modify first user's profile as second user - should deny
        r = self.client.login(username="buser", password="topsecret")
        self.assertTrue(r)
        response = self.client.post("/profile/edit/", post_data)
        self.assertEqual(response.status_code, 200)
        self.client.logout()

        # Try to modify first user's profile as first user - should accept.
        # Also check that email_is_public makes a difference.
        r = self.client.login(username="auser", password="topsecret")
        self.assertTrue(r)
        response = self.client.get("/profile/auser/")
        self.assertContains(response, "irrelevant@example.com")
        response = self.client.post("/profile/edit/", post_data)
        self.assertEqual(response.status_code, 302)
        response = self.client.get("/profile/auser/")
        self.assertNotContains(response, "irrelevant@example.com")
        self.client.logout()


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class ResetPasswordTestCase(TestCase):
    def test_reset_password(self):
        # Create a user
        self.auser = User.objects.create_user(
            username="auser", email="irrelevant@example.com", password="topsecret1"
        )
        self.auser.save()

        # Ooops... I thought my password was topsecret2, but apparently I
        # forgot it...
        r = self.client.login(username="auser", password="topsecret2")
        self.assertFalse(r)

        # No problem, let me submit the password reset form
        response = self.client.get("/accounts/password/reset/")
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            "/accounts/password/reset/", {"email": "irrelevant@example.com"}
        )
        self.assertEqual(response.status_code, 302)

        # Did I receive an email?
        self.assertEqual(len(django.core.mail.outbox), 1)

        # Get the link from the email
        m = re.search(r"http://[^/]+(\S+)", django.core.mail.outbox[0].body)
        reset_link = m.group(1)

        # Visit the link and submit the form
        response = self.client.get(reset_link)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            reset_link, {"new_password1": "topsecret2", "new_password2": "topsecret2"}
        )
        self.assertEqual(response.status_code, 302)

        # Cool, now let me log in
        r = self.client.login(username="auser", password="topsecret2")
        self.assertTrue(r)


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
