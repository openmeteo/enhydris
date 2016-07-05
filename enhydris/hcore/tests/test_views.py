from io import StringIO
from itertools import takewhile
import json
import re
import os
import shutil
import tempfile
import textwrap
import time
from unittest import skipIf, skipUnless
from urllib.parse import urlencode

import django
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User, Group, Permission
from django.contrib.gis.geos import fromstr, Point
from django.http import HttpRequest, QueryDict
from django.test import TestCase
from django.test.utils import override_settings

from model_mommy import mommy
import pd2hts

from enhydris.hcore.forms import TimeseriesDataForm
from enhydris.hcore.models import (
    EventType, FileType, GentityEvent, GentityFile, Instrument, InstrumentType,
    Organization, Station, StationType, Timeseries, TimeZone,
    UnitOfMeasurement, UserProfile, Variable)
from enhydris.hcore.views import ALLOWED_TO_EDIT, StationListBaseView

try:
    # Experimental Selenium support. Enhydris does not require Selenium
    # to be installed or configured. If it is, it runs the selenium tests;
    # otherwise the tests are skipped. If you want to run this tests, pip
    # install django_selenium_clean and add to your settings.py the snippet at
    # https://github.com/aptiko/django-selenium-clean#executing-the-test
    from django_selenium_clean import selenium, SeleniumTestCase, PageElement
    from selenium.webdriver.common.by import By
except ImportError:
    selenium = False

    # Create some dummy stuff to allow the Selenium tests to compile (even if
    # they are always skipped).
    class Dummy:
        XPATH = ''
        ID = ''

        def __init__(*args, **kwargs):
            pass
    SeleniumTestCase = TestCase
    PageElement = Dummy
    By = Dummy()


class SortTestCase(TestCase):

    def setUp(self):
        mommy.make(Station, name="Komboti",
                   water_division__name="North Syldavia Basins")
        mommy.make(Station, name="Agios Athanasios",
                   water_division__name="South Syldavia Basins")
        mommy.make(Station, name="Tharbad",
                   water_division__name="South Syldavia Basins")

    def test_sort(self):
        # Request for host.domain/?sort=water_division&sort=name
        response = self.client.get(reverse('station_list')
                                   + '?sort=water_division&sort=name')

        # Checking  test stations 'Komboti', 'Agios Athanasios', 'Tharbad'
        # alphabetical order ['water_division', 'name']
        i = response.content.decode('utf-8').index
        self.assertTrue(i('Komboti') < i('Agios Athanasios') < i('Tharbad'))

    def test_invalid_sort(self):
        # Request for host.domain/?sort=999.9
        response = self.client.get(reverse('station_list') + '?sort=999.9')

        # Sort is only made with default ['name'] term
        # Checking  test stations 'Komboti', 'Tharbad' alphabetical order index
        i = response.content.decode('utf-8').index
        self.assertLess(i('Komboti'), i('Tharbad'))

        # Order for host.domain/?sort=name&sort=999.9
        response = self.client.get(reverse('station_list')
                                   + '?sort=name&sort=999.9')

        # Order is only made with default ['name'] term
        # Checking  test stations 'Komboti', 'Tharbad' alphabetical order index
        i = response.content.decode('utf-8').index
        self.assertLess(i('Komboti'), i('Tharbad'))


class SearchTestCase(TestCase):

    def setUp(self):
        # Station owners
        rich = mommy.make(Organization,
                          name="We're rich and we fancy it SA")
        poor = mommy.make(Organization,
                          name="We're poor and dislike it Ltd")

        # Create three stations
        station_komboti = mommy.make(
            Station, name='Komboti', owner=poor,
            political_division__name='Arta',
            political_division__parent__name='Epirus',
            political_division__parent__parent__name='Greece',
            stype__descr="Important",
            water_basin__name='Arachthos',
            water_division__name="North Syldavia Basins")
        greece = station_komboti.political_division.parent.parent
        station_ai_thanassis = mommy.make(
            Station, name='Agios Athanasios', owner=poor,
            political_division__name='Karditsa',
            political_division__parent__name='Thessaly',
            political_division__parent__parent=greece,
            stype__descr=["Important", "Unimportant"],
            water_division__name="South Syldavia Basins")
        station_tharbad = mommy.make(
            Station, name='Tharbad', owner=rich,
            political_division__name='Cardolan',
            political_division__parent__name='Eriador',
            political_division__parent__parent__name='Middle Earth',
            stype__descr=["Unimportant"],
            water_basin__name='Greyflood',
            water_division__name="South Syldavia Basins")

        # Five time series
        kt = mommy.make(Timeseries, name='Air temperature',
                        variable__descr='Temperature', gentity=station_komboti)
        kr = mommy.make(Timeseries, name='Rain', gentity=station_komboti,
                        variable__descr='Rain')
        mommy.make(Timeseries, name='Air temperature',
                   gentity=station_ai_thanassis, variable=kt.variable)
        mommy.make(Timeseries, name='Rain', gentity=station_ai_thanassis,
                   variable=kr.variable)
        mommy.make(Timeseries, name='Temperature', gentity=station_tharbad,
                   variable=kt.variable,
                   remarks='This is an extremely important time series, '
                   'just because it is hugely significant and markedly '
                   'outstanding.')

        # And a station with no time series
        mommy.make(Station, name="Lefkada")

    def get_queryset(self, query_string):
        view = StationListBaseView()
        view.request = HttpRequest()
        view.request.method = 'GET'
        view.request.GET = QueryDict(query_string)
        return view.get_queryset()

    def test_search_in_timeseries_remarks(self):
        # Search for something that exists
        queryset = self.get_queryset(urlencode({
            'q': 'extremely important time series'}))
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].name, 'Tharbad')

        # Search for something that doesn't exist
        queryset = self.get_queryset(urlencode({
            'q': 'this should not exist anywhere'}))
        self.assertEqual(queryset.count(), 0)

    def test_search_by_owner(self):
        queryset = self.get_queryset(urlencode({'q': 'owner:RiCh'}))
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].owner.organization.name,
                         "We're rich and we fancy it SA")
        queryset = self.get_queryset(urlencode({'owner': 'poor'}))
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].owner.organization.name,
                         "We're poor and dislike it Ltd")
        queryset = self.get_queryset(urlencode({'owner': 'nonexistent'}))
        self.assertEqual(queryset.count(), 0)

    def test_search_by_type(self):
        # The following will find both "Important" and "Unimportant" stations,
        # because the string "important" is included in "Unimportant".
        queryset = self.get_queryset(urlencode({'q': 'type:Important'}))
        queryset = queryset.distinct()
        self.assertEqual(queryset.count(), 3)

        queryset = self.get_queryset(urlencode({'type': 'Unimportant'}))
        queryset = queryset.order_by('name')
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].name, 'Agios Athanasios')
        self.assertEqual(queryset[1].name, 'Tharbad')

        queryset = self.get_queryset(urlencode({'type': 'Nonexistent'}))
        self.assertEqual(queryset.count(), 0)

    def test_search_by_water_division(self):
        queryset = self.get_queryset(urlencode({'q': 'water_division:north'}))
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].name, 'Komboti')

        queryset = self.get_queryset(urlencode({'q': 'water_division:south'}))
        queryset = queryset.order_by('name')
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].name, 'Agios Athanasios')
        self.assertEqual(queryset[1].name, 'Tharbad')

        queryset = self.get_queryset(urlencode({'q': 'water_division:east'}))
        self.assertEqual(queryset.count(), 0)

    def test_search_by_water_basin(self):
        queryset = self.get_queryset(urlencode({'q': 'water_basin:arachthos'}))
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].name, 'Komboti')

        queryset = self.get_queryset(urlencode({'water_basin': 'greyflood'}))
        queryset = queryset.order_by('name')
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].name, 'Tharbad')

        queryset = self.get_queryset(urlencode({'water_basin': 'nonexistent'}))
        self.assertEqual(queryset.count(), 0)

    def test_search_by_variable(self):
        queryset = self.get_queryset(urlencode({'q': 'variable:rain'}))
        queryset = queryset.order_by('name')
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].name, 'Agios Athanasios')
        self.assertEqual(queryset[1].name, 'Komboti')

        queryset = self.get_queryset(urlencode({'q': 'variable:temperature'}))
        queryset = queryset.order_by('name')
        self.assertEqual(queryset.count(), 3)
        self.assertEqual(queryset[0].name, 'Agios Athanasios')
        self.assertEqual(queryset[1].name, 'Komboti')
        self.assertEqual(queryset[2].name, 'Tharbad')

        queryset = self.get_queryset(urlencode({'q': 'variable:nonexistent'}))
        self.assertEqual(queryset.count(), 0)

    def test_search_by_gentityId(self):
        station_id = Station.objects.get(name='Komboti').id
        queryset = self.get_queryset(urlencode({'gentityId': str(station_id)}))
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].name, 'Komboti')

        queryset = self.get_queryset(urlencode({'gentityId': '98765'}))
        self.assertEqual(queryset.count(), 0)

    def test_search_by_ts_only(self):
        queryset = self.get_queryset('')
        self.assertEqual(queryset.count(), 4)
        queryset = self.get_queryset(urlencode({'q': 'ts_only:'}))
        self.assertEqual(queryset.count(), 3)

    def test_search_by_political_division(self):
        queryset = self.get_queryset(
            urlencode({'political_division': 'Cardolan'}))
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].name, 'Tharbad')

        queryset = self.get_queryset(
            urlencode({'political_division': 'Arthedain'}))
        self.assertEqual(queryset.count(), 0)

        queryset = self.get_queryset(
            urlencode({'political_division': 'Karditsa'}))
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].name, 'Agios Athanasios')

        queryset = self.get_queryset(
            urlencode({'political_division': 'Arta'}))
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].name, 'Komboti')

        queryset = self.get_queryset(
            urlencode({'political_division': 'Epirus'}))
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].name, 'Komboti')

        queryset = self.get_queryset(
            urlencode({'political_division': 'Greece'}))
        queryset = queryset.order_by('name')
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].name, 'Agios Athanasios')
        self.assertEqual(queryset[1].name, 'Komboti')

        queryset = self.get_queryset(
            urlencode({'political_division': 'Middle Earth'}))
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].name, 'Tharbad')


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


class RandomEnhydrisTimeseriesDataDir(override_settings):
    """
    Override ENHYDRIS_TIMESERIES_DATA_DIR to a temporary directory.

    Specifying "@RandomEnhydrisTimeseriesDataDir()" as a decorator is the same
    as "@override_settings(ENHYDRIS_TIMESERIES_DATA_DIR=tempfile.mkdtemp())",
    except that in the end it removes the temporary directory.
    """

    def __init__(self):
        self.tmpdir = tempfile.mkdtemp()
        super(RandomEnhydrisTimeseriesDataDir, self).__init__(
            ENHYDRIS_TIMESERIES_DATA_DIR=self.tmpdir)

    def disable(self):
        super(RandomEnhydrisTimeseriesDataDir, self).disable()
        shutil.rmtree(self.tmpdir)


class GentityFileTestCase(TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    @RandomMediaRoot()
    def test_gentity_file(self):
        # Create test data
        mommy.make(User, username='admin', password=make_password('topsecret'),
                   is_active=True, is_superuser=True, is_staff=True)
        mommy.make(Station, name='Komboti')
        mommy.make(FileType, mime_type='image/gif')

        # Upload a gentity file
        gentity_id = Station.objects.get(name='Komboti').id
        r = self.client.login(username='admin', password='topsecret')
        self.assertTrue(r)
        self.assertEqual(GentityFile.objects.filter(gentity__id=gentity_id
                                                    ).count(), 0)
        filetype_id = FileType.objects.get(mime_type='image/gif').id
        small_gif = b'GIF89a\x01\x00\x01\x00\x00\xff\x00,\x00\x00\x00\x00' \
            b'\x01\x00\x01\x00\x00\x02\x00;'
        with open(os.path.join(self.tempdir, 'aaa.jpg'), 'w+b') as f:
            f.write(small_gif)
            f.seek(0)
            response = self.client.post(reverse('gentityfile_add'),
                                        {'gentity': gentity_id,
                                         'date': '',
                                         'file_type': filetype_id,
                                         'descr': 'A description',
                                         'remarks': '',
                                         'descr_alt': 'An alt description',
                                         'remarks_alt': '',
                                         'content': f,
                                         })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(GentityFile.objects.filter(gentity__id=gentity_id
                                                    ).count(), 1)

        # Now try to download that gentity file
        gentity_file_id = GentityFile.objects.all()[0].id
        response = self.client.get(reverse('gentityfile_dl',
                                           kwargs={'gf_id': gentity_file_id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, small_gif)


class TsTestCase(TestCase):
    """Test timeseries data upload/download code."""

    def setUp(self):
        # create dependecies of timeseries.
        self.stype = StationType.objects.create(descr='stype')
        self.stype.save()
        self.organization = Organization.objects.create(name='org')
        self.organization.save()
        self.var = Variable.objects.create(descr='var')
        self.var.save()
        self.unit = UnitOfMeasurement.objects.create(symbol='+')
        self.unit.variables.add(self.var)
        self.unit.save()
        self.tz = TimeZone.objects.create(code='EET', utc_offset=120)
        self.tz.save()
        self.station = Station.objects.create(
            name='station',
            owner=self.organization,
            approximate=False,
            is_automatic=True,
            point=fromstr('POINT(24.67890 38.12345)'),
            srid=4326,
            altitude=219.22)
        self.station.save()
        self.ts = Timeseries(name="tstest", gentity=self.station,
                             time_zone=self.tz,
                             unit_of_measurement=self.unit,
                             variable=self.var, precision=1)
        self.ts.save()
        self.user = User.objects.create_user('test', 'test@test.com',
                                             'test')
        self.user.save()

    def tearDown(self):
        self.stype.delete()
        self.organization.delete()
        self.var.delete()
        self.unit.delete()
        self.tz.delete()
        self.ts.delete()
        self.user.delete()

    @RandomEnhydrisTimeseriesDataDir()
    def test_timeseries_data(self):
        # Upload
        with open("enhydris/hcore/tests/tsdata.hts", "rb") as f:
            file_dict = {'data': SimpleUploadedFile(f.name, f.read())}
        post_dict = {'gentity': self.station.pk, 'variable': self.var.pk,
                     'unit_of_measurement': self.unit.pk,
                     'time_zone': self.tz.pk
                     }
        form = TimeseriesDataForm(post_dict, file_dict, instance=self.ts)
        self.assertTrue(form.is_valid())
        ts = form.save()
        ts.save()
        self.assertEqual(len(ts.get_data()), 12872)

        # Download

        def nrecords():
            lines = response.content.decode('utf-8').splitlines()
            linecount = len(lines)
            headerlinecount = sum([1 for x in takewhile(lambda x: x != '',
                                                        lines)]) + 1
            return linecount - headerlinecount

        if not settings.ENHYDRIS_TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS:
            self.client.login(username='test', password='test')

        url = "/timeseries/d/{}/download/".format(self.ts.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode('utf-8').splitlines()[0]
                         .strip(), 'Version=2')
        self.assertEqual(nrecords(), 12872)

        url = "/timeseries/d/{}/download/?version=3".format(self.ts.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        adataframe = pd2hts.read_file(StringIO(response.content.decode('utf-8')
                                               ))
        self.assertAlmostEqual(adataframe.location['abscissa'], 24.67890,
                               places=6)
        self.assertAlmostEqual(adataframe.location['ordinate'], 38.12345,
                               places=6)
        self.assertEqual(adataframe.location['srid'], 4326)
        self.assertAlmostEqual(adataframe.location['altitude'], 219.22,
                               places=2)
        self.assertTrue(adataframe.location['asrid'] is None)
        self.assertEqual(nrecords(), 12872)

        url = "/timeseries/d/{}/download/1960-11-04/".format(self.ts.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(nrecords(), 12870)

        url = "/timeseries/d/{}/download/1960-11-04/1960-11-08T08:00/".format(
            self.ts.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(nrecords(), 4)

        url = "/timeseries/d/{}/download//1960-11-08T08:00/".format(self.ts.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(nrecords(), 6)

        url = "/timeseries/d/{}/download//1960-11-08T08:00:00/".format(
            self.ts.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(nrecords(), 6)

        url = "/timeseries/d/{}/download/1950-02-02/1960-11-08T08:00/".format(
            self.ts.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(nrecords(), 6)

        url = "/timeseries/d/{}/download/1950-02-02/1960-01-01T08:00/".format(
            self.ts.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(nrecords(), 0)

        url = "/timeseries/d/{}/download/1998-02-02//".format(
            self.ts.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(nrecords(), 0)

        self.client.logout()

    @RandomEnhydrisTimeseriesDataDir()
    def test_get_empty_timeseries_data_for_chart(self):
        url = "/timeseries/data/?object_id={}".format(self.ts.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        aobject = json.loads(response.content.decode('utf-8'))
        self.assertTrue(isinstance(aobject, dict))
        self.assertEqual(len(aobject), 2)
        self.assertEqual(aobject['stats'], {})
        self.assertEqual(aobject['data'], [])

    @RandomEnhydrisTimeseriesDataDir()
    def test_timeseries_with_timezone_data(self):
        """There was this bug where you'd ask to download from start date,
        and the start date was interpreted as aware whereas the time series
        data was interpreted as naive. This test checks there's no such
        bug."""
        data = textwrap.dedent("""\
                               2005-08-23 18:53,93,
                               2005-08-23 19:53,108.7,
                               2005-08-23 20:53,28.3,
                               2005-08-23 21:53,1.7,
                               2005-08-23 22:53,42.4,
            """)
        self.ts.set_data(StringIO(data))
        url = '/timeseries/d/{}/download/2005-08-23T19:54/'.format(self.ts.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        result = response.content.decode('utf-8')

        # Remove header, leave only data
        emptylinepos = result.find('\r\n\r\n')
        self.assertTrue(emptylinepos > 0)
        result = result[emptylinepos + 4:]

        self.assertEqual(result, textwrap.dedent("""\
                                                 2005-08-23 20:53,28.3,\r
                                                 2005-08-23 21:53,1.7,\r
                                                 2005-08-23 22:53,42.4,\r
                                                 """))


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class OpenVTestCase(TestCase):
    """
    Test that the behaviour of the site when USERS_CAN_ADD_CONTENT is set to
    TRUE is as expected.
    """

    def setUp(self):
        # Create the editors group
        permitted = ["eventtype", "filetype", "garea", "gentityaltcode",
                     "gentityaltcodetype", "gentityevent", "gentityfile",
                     "gline", "instrument", "instrumenttype", "overseer",
                     "politicaldivision", "station", "stationtype",
                     "timeseries", "timestep", "timezone", "unitofmeasurement",
                     "userprofile", "variable", "waterbasin", "waterdivision",
                     "person", "organization", "gentitygenericdatatype"]
        editors = Group(name='editors')
        editors.save()
        for x in ('add', 'change', 'delete'):
            for y in permitted:
                editors.permissions.add(
                    Permission.objects.get(codename=x + '_' + y,
                                           content_type__app_label='hcore'))

        # create user and add him to editors group. this'll be the
        # creator/owner to check permissions
        self.user = User.objects.create_user('opentest', 'opentest@test.com',
                                             'opentest')
        # another user who won't have permissions over the tested objects to
        # verify that permission handling works as expected.
        self.user2 = User.objects.create_user('fail', 'fail@faildom.com',
                                              'fail')
        self.editors = Group.objects.get(name='editors')
        self.editors.user_set.add(self.user)
        self.editors.user_set.add(self.user2)

        # create a station, instrument and timeseries to check permissions
        self.stype = StationType.objects.create(descr='stype')
        self.itype = InstrumentType.objects.create(descr='itype')
        self.organization = Organization.objects.create(name='org')
        self.var = Variable.objects.create(descr='var')
        self.unit = UnitOfMeasurement.objects.create(symbol='+')
        self.unit.variables.add(self.var)
        self.tz = TimeZone.objects.create(code='UTC', utc_offset='0')
        self.station = Station.objects.create(name='station',
                                              owner=self.organization,
                                              approximate=False,
                                              is_automatic=True)
        self.ts = Timeseries(name="tstest", gentity=self.station,
                             time_zone=self.tz, unit_of_measurement=self.unit,
                             variable=self.var)
        self.ts.save()

    def tearDown(self):
        self.user.delete()
        self.stype.delete()
        self.organization.delete()
        self.var.delete()
        self.unit.delete()
        self.tz.delete()
        self.ts.delete()

    def testStatusCode(self):
        """Test that the response status code is correct"""
        self.pages = ['/stations/add/',
                      '/timeseries/add/',
                      '/instrument/add/',
                      ]

        # check that anonymous users cannot see the forms
        for page_url in self.pages:
            page = self.client.get(page_url)
            self.assertEqual(
                page.status_code, 302,
                "Status code for page '%s' was %s instead of %s" %
                (page_url, page.status_code, 302))
            self.assertRedirects(
                page, '/accounts/login/?next=%s' % page_url, status_code=302,
                target_status_code=200)

        self.assertEqual(self.client.login(username='opentest',
                                           password='opentest'), True)

        # check that logged in users can see the forms
        for page_url in self.pages:
            page = self.client.get(page_url)
            self.assertEqual(
                page.status_code, 200,
                "Status code for page '%s' was %s instead of %s" %
                (page_url, page.status_code, 200))

        self.client.logout()

    def testStationPermissions(self):
        """
        Check that edit forms honour the permissions.
        """

        self.assertEqual(self.client.login(username='opentest',
                                           password='opentest'), True)

        post_data = {
            'name': 'station_test',
            'stype': self.stype.pk,
            'owner': self.organization.pk,
            'creator': self.user.pk,
            'copyright_holder': 'Copyright Holder',
            'copyright_years': '1990-2011',
            'Overseer-TOTAL_FORMS': '1',
            'Instrument-TOTAL_FORMS': '1',
            'Timeseries-TOTAL_FORMS': '1',
            'Timeseries-INITIAL_FORMS': '0',
            'Overseer-INITIAL_FORMS': '0',
            'Instrument-INITIAL_FORMS': '0'
        }

        # create new station as a logged in user. this should work
        url = "/stations/add/"
        resp = self.client.post(url, post_data)
        self.assertEqual(resp.status_code, 302)

        s = Station.objects.get(name='station_test')

        # edit my station. this should work
        url = "/stations/edit/%s/" % str(s.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "station_edit.html")

        # delete my station. this should work
        url = "/stations/delete/%s/" % str(s.pk)
        resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Station.objects.filter(name='station_test').count(),
                         0)

        # try to edit a random station. this should fail
        url = "/stations/edit/%s/" % str(self.station.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 403)

        # try to delete a random station. this should fail
        url = "/stations/delete/%s/" % str(self.station.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 403)

        # recreate again for further tests
        url = "/stations/add/"
        resp = self.client.post(url, post_data)
        self.assertEqual(resp.status_code, 302)

        s = Station.objects.get(name='station_test')

        self.client.logout()

        # login as another user to check 403 perms
        self.assertEqual(self.client.login(username='fail', password='fail'),
                         True)

        # edit station. this shouldn't work
        url = "/stations/edit/%s/" % str(s.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 403)

        # delete station. this shouldn't work
        url = "/stations/delete/%s/" % str(s.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 403)

        # add user to maintainers and check if it's fixed.
        s.maintainers.add(self.user2)
        s.save()

        # edit maintaining station. this should work
        url = "/stations/edit/%s/" % str(s.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "station_edit.html")

        # delete maintaining station. this shouldn't work
        url = "/stations/delete/%s/" % str(s.pk)
        resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 403)

        self.client.logout()
        s.delete()

    def testTimeseriesPermissions(self):
        """
        Check that edit forms honour the permissions.
        """
        self.assertEqual(self.client.login(username='opentest',
                                           password='opentest'), True)

        post_data = {
            'name': 'station_test',
            'stype': self.stype.pk,
            'owner': self.organization.pk,
            'creator': self.user.pk,
            'copyright_holder': 'Copyright Holder',
            'copyright_years': '1990-2011',
            'Overseer-TOTAL_FORMS': '1',
            'Instrument-TOTAL_FORMS': '1',
            'Timeseries-INITIAL_FORMS': '0',
            'Timeseries-TOTAL_FORMS': '1',
            'Overseer-INITIAL_FORMS': '0',
            'Instrument-INITIAL_FORMS': '0',
        }

        # create new station as a logged in user. this should work
        url = "/stations/add/"
        resp = self.client.post(url, post_data)
        self.assertEqual(resp.status_code, 302)

        s = Station.objects.get(name='station_test')

        post_data = {
            'name': 'timeseries_test',
            'gentity': s.pk,
            'time_zone': self.tz.pk,
            'variable': self.var.pk,
            'unit_of_measurement': self.unit.pk
        }

        # create new timeseries
        url = "/timeseries/add/"
        resp = self.client.post(url, post_data)
        self.assertEqual(resp.status_code, 302)

        t = Timeseries.objects.get(name="timeseries_test")

        # edit my timeseries. this should work
        url = "/timeseries/edit/%s/" % str(t.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "timeseries_edit.html")

        # delete my timeseries. this should work
        url = "/timeseries/delete/%s/" % str(t.pk)
        resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Station.objects.filter(
            name='timeseries_test').count(), 0)

        # recreate deleted timeseries for further tests
        url = "/timeseries/add/"
        resp = self.client.post(url, post_data)
        t = Timeseries.objects.get(name="timeseries_test")
        self.assertEqual(resp.status_code, 302)

        self.client.logout()

        # login as another user to check 403 perms
        self.assertEqual(self.client.login(username='fail', password='fail'),
                         True)

        # edit my timeseries. this shouldn't work
        url = "/timeseries/edit/%s/" % str(t.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 403)

        # delete my timeseries. this shouldn't work
        url = "/timeseries/delete/%s/" % str(t.pk)
        resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 403)

        # add user to maintainers and check if it's fixed.
        s.maintainers.add(self.user2)
        s.save()

        # edit maintaining timeseries. this should work
        url = "/timeseries/edit/%s/" % str(t.pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "timeseries_edit.html")

        # delete maintaining timeseries, this should work
        url = "/timeseries/delete/%s/" % str(t.pk)
        resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Station.objects.filter(
            name='timeseries_test').count(), 0)

        s.delete()

    def testInstrumentPermissions(self):
        """
        Check that edit forms honour the permissions.
        """

        self.assertEqual(self.client.login(username='opentest',
                                           password='opentest'), True)

        post_data = {
            'name': 'station_test',
            'stype': self.stype.pk,
            'owner': self.organization.pk,
            'creator': self.user.pk,
            'copyright_holder': 'Copyright Holder',
            'copyright_years': '1990-2011',
            'Overseer-TOTAL_FORMS': '1',
            'Instrument-TOTAL_FORMS': '1',
            'Timeseries-INITIAL_FORMS': '0',
            'Timeseries-TOTAL_FORMS': '1',
            'Overseer-INITIAL_FORMS': '0',
            'Instrument-INITIAL_FORMS': '0',
        }

        # create new station as a logged in user. this should work
        url = "/stations/add/"
        resp = self.client.post(url, post_data)
        self.assertEqual(resp.status_code, 302)

        s = Station.objects.get(name='station_test')

        post_data = {
            'name': 'instrument_test',
            'station': s.pk,
            'type': self.itype.pk
        }

        # create new instrument
        url = "/instrument/add/"
        resp = self.client.post(url, post_data)
        self.assertEqual(resp.status_code, 302)

        i = Instrument.objects.get(name="instrument_test")

        # edit my instrument. this should work
        url = "/instrument/edit/%s/" % str(i.pk)
        resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "instrument_edit.html")

        # delete my station. this should work
        url = "/instrument/delete/%s/" % str(i.pk)
        resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Station.objects.filter(
            name='instrument_test').count(), 0)

        # recreate deleted instrument for further tests
        url = "/instrument/add/"
        resp = self.client.post(url, post_data)
        self.assertEqual(resp.status_code, 302)

        i = Instrument.objects.get(name="instrument_test")

        self.client.logout()

        # login as another user to check 403 perms
        self.assertEqual(self.client.login(username='fail', password='fail'),
                         True)

        # edit my instrument. this shouldn't work
        url = "/instrument/edit/%s/" % str(i.pk)
        resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 403)

        # delete my instrument. this shouldn't work
        url = "/instrument/delete/%s/" % str(i.pk)
        resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 403)

        # add user to maintainers and check if it's fixed.
        s.maintainers.add(self.user2)
        s.save()

        # edit my instrument. this should work
        url = "/instrument/edit/%s/" % str(i.pk)
        resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "instrument_edit.html")

        # delete my station. this should work
        url = "/instrument/delete/%s/" % str(i.pk)
        resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Station.objects.filter(
            name='instrument_test').count(), 0)

    def testGenericModelCreation(self):
        """
        Test the generic model forms
        """
        self.assertEqual(self.client.login(username='opentest',
                                           password='opentest'), True)

        for model in ALLOWED_TO_EDIT:
            url = "/add/%s/?_popup=1" % model
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200, "Error in page %s." % url)
            self.assertTemplateUsed(resp, "model_add.html")

        self.client.logout()


class RegisterTestCase(TestCase):
    """
    Test that "Register" link appears depending on REGISTRATION_OPEN setting.
    """

    @override_settings(REGISTRATION_OPEN=False)
    def test_register_link_absent(self):
        response = self.client.get('/')
        self.assertNotContains(response, 'Register')

    @override_settings(REGISTRATION_OPEN=True)
    def test_register_link_present(self):
        response = self.client.get('/')
        self.assertContains(response, 'Register')


class StationTestCase(TestCase):

    def setUp(self):
        mommy.make(User, username='admin', password=make_password('topsecret'),
                   is_active=True, is_superuser=True, is_staff=True)
        mommy.make(Organization, name="We're rich and we fancy it SA")
        mommy.make(StationType, descr="Important")

    @override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
    def test_add_station(self):
        """
        Test that the add station form appears properly.
        """
        r = self.client.login(username='admin', password='topsecret')
        self.assertTrue(r)
        response = self.client.get('/stations/add/')
        self.assertEqual(response.status_code, 200)

    # We cannot catch invalid SRIDs with spatialite, because spatialite
    # does not return any error. We therefore skip this test. See
    # http://stackoverflow.com/questions/37005581/ for details.
    @skipIf(settings.DATABASES['default']['ENGINE'].endswith('.spatialite'),
            'This functionality is not available on spatialite; '
            'fix it if you can.')
    @override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
    def test_station_invalid_SRID_submission(self):
        r = self.client.login(username='admin', password='topsecret')
        self.assertTrue(r)
        post_data = {
            'name': 'station_test',
            'stype': StationType.objects.get(descr="Important").id,
            'owner': Organization.objects.get(
                    name="We're rich and we fancy it SA").id,
            'copyright_holder': 'Copyright Holder',
            'copyright_years': '1990-2011',
            'ordinate': '17',
            'abscissa': '25',
            'srid': '210',
        }
        response = self.client.post('/stations/add/', post_data)
        self.assertFormError(response, 'form', 'srid', 'Invalid SRID')


class ProfileTestCase(TestCase):

    def test_profile(self):
        # Create a user
        self.auser = User.objects.create_user(
            username='auser', email='irrelevant@example.com',
            password='topsecret')
        self.auser.save()
        profile = UserProfile.objects.get(user=self.auser)
        profile.fname = 'A'
        profile.lname = 'User'
        profile.address = 'Nowhere'
        profile.email_is_public = True
        profile.save()

        # Create a second user
        self.buser = User.objects.create_user(
            username='buser', email='irrelevant_indeed@example.com',
            password='topsecret')
        self.buser.save()

        # View the first user's profile
        response = self.client.get('/profile/auser/')
        self.assertContains(response, 'irrelevant@example.com')

        # Prepare the post data that we will be attempting to post -
        # essentially this sets email_is_public to False.
        post_data = {'user': self.auser.id, 'fname': 'A', 'lname': 'User',
                     'address': 'Nowhere', 'organization': 'UN',
                     'email_is_public': False}

        # Try to modify first user's profile anonymously - should deny
        response = self.client.post('/profile/edit/', post_data)
        self.assertEqual(response.status_code, 200)

        # Try to modify first user's profile as second user - should deny
        r = self.client.login(username='buser', password='topsecret')
        self.assertTrue(r)
        response = self.client.post('/profile/edit/', post_data)
        self.assertEqual(response.status_code, 200)
        self.client.logout()

        # Try to modify first user's profile as first user - should accept.
        # Also check that email_is_public makes a difference.
        r = self.client.login(username='auser', password='topsecret')
        self.assertTrue(r)
        response = self.client.get('/profile/auser/')
        self.assertContains(response, 'irrelevant@example.com')
        response = self.client.post('/profile/edit/', post_data)
        self.assertEqual(response.status_code, 302)
        response = self.client.get('/profile/auser/')
        self.assertNotContains(response, 'irrelevant@example.com')
        self.client.logout()


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ResetPasswordTestCase(TestCase):

    def test_reset_password(self):
        # Create a user
        self.auser = User.objects.create_user(
            username='auser', email='irrelevant@example.com',
            password='topsecret1')
        self.auser.save()

        # Ooops... I thought my password was topsecret2, but apparently I
        # forgot it...
        r = self.client.login(username='auser', password='topsecret2')
        self.assertFalse(r)

        # No problem, let me submit the password reset form
        response = self.client.get('/accounts/password/reset/')
        self.assertEqual(response.status_code, 200)
        response = self.client.post('/accounts/password/reset/',
                                    {'email': 'irrelevant@example.com'})
        self.assertEqual(response.status_code, 302)

        # Did I receive an email?
        self.assertEqual(len(django.core.mail.outbox), 1)

        # Get the link from the email
        m = re.search('http://[^/]+(\S+)', django.core.mail.outbox[0].body)
        reset_link = m.group(1)

        # Visit the link and submit the form
        response = self.client.get(reset_link)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reset_link,
                                    {'new_password1': 'topsecret2',
                                     'new_password2': 'topsecret2'})
        self.assertEqual(response.status_code, 302)

        # Cool, now let me log in
        r = self.client.login(username='auser', password='topsecret2')
        self.assertTrue(r)


class GentityEventTestCase(TestCase):

    def setUp(self):
        mommy.make(User, username='admin', password=make_password('topsecret'),
                   is_active=True, is_superuser=True, is_staff=True)
        mommy.make(Station, name="Komboti")
        mommy.make(EventType, descr="WAR: World Is A Ghetto")

    def test_add_gentity_event(self):
        # Gentity and Station models share the same id
        gentity_id = Station.objects.get(name='Komboti').id

        # Before uploading, there should be 0 events in the database
        self.assertEqual(GentityEvent.objects.filter(gentity__id=gentity_id
                                                     ).count(), 0)

        # Login user as admin
        r = self.client.login(username='admin', password='topsecret')
        self.assertTrue(r)

        # Post data at 'gentityevent_add' form
        response = self.client.post(
            reverse('gentityevent_add'),
            {'date': '10/06/2015',
             'gentity': gentity_id,
             'type': EventType.objects.get(descr="WAR: World Is A Ghetto").id,
             'user': User.objects.get(username='admin').id}
        )

        # Check that form redirect to correct Station.id
        self.assertRedirects(response, reverse('station_detail',
                                               kwargs={'pk': gentity_id}))

        # Check that the database contains one event in the datebase
        self.assertEqual(GentityEvent.objects.filter(gentity__id=gentity_id
                                                     ).count(), 1)


@skipUnless(selenium, 'Selenium is missing or unconfigured')
class CoordinatesTestCase(SeleniumTestCase):

    # Elements in "Edit Station" view
    label_ordinate = PageElement(By.XPATH, '//label[@for="id_ordinate"]')
    field_ordinate = PageElement(By.ID, 'id_ordinate')
    label_abscissa = PageElement(By.XPATH, '//label[@for="id_abscissa"]')
    field_abscissa = PageElement(By.ID, 'id_abscissa')
    field_srid = PageElement(By.ID, 'id_srid')
    field_altitude = PageElement(By.ID, 'id_altitude')
    field_asrid = PageElement(By.ID, 'id_asrid')
    field_approximate = PageElement(By.ID, 'id_approximate')
    button_coordinates = PageElement(By.ID, 'btnCoordinates')
    field_stype = PageElement(By.ID, 'id_stype')
    stype_option_important = PageElement(
        By.XPATH, '//select[@id="id_stype"]/option[text()="Important"]')
    field_owner = PageElement(By.ID, 'id_owner')
    owner_option_big_tomatoes = PageElement(
        By.XPATH, '//select[@id="id_owner"]/option[text()="Big tomatoes"]')
    field_copyright_holder = PageElement(By.ID, 'id_copyright_holder')
    field_copyright_years = PageElement(By.ID, 'id_copyright_years')
    button_submit = PageElement(By.XPATH, '//button[@type="submit"]')

    # Elements in "View Station" view
    button_edit = PageElement(
        By.XPATH, '//a[starts-with(@class, "btn") and '
                  'starts-with(@href, "/stations/edit/")]')

    def setUp(self):
        mommy.make(User, username='admin', password=make_password('topsecret'),
                   is_active=True, is_superuser=True, is_staff=True)
        mommy.make(StationType, descr="Important")
        mommy.make(Organization, name="Big tomatoes")

    @override_settings(DEBUG=True)
    def test_coordinates(self):
        # Login
        r = selenium.login(username='admin', password='topsecret')
        self.assertTrue(r)

        # Go to the add new station page and check that the simple view is
        # active
        selenium.get(self.live_server_url + '/stations/add/')
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
        self.assertEqual(self.field_srid.get_attribute('value'), '4326')

        # Go back to the simple view and check it's ok
        self.button_coordinates.click()
        self.label_ordinate.wait_until_contains("Latitude")
        self.assertEqual(self.label_ordinate.text, "Latitude")
        self.assertEqual(self.label_abscissa.text, "Longitude")
        self.assertFalse(self.field_srid.is_displayed())
        self.assertFalse(self.field_asrid.is_displayed())
        self.assertFalse(self.field_approximate.is_displayed())

        # Enter a latitude and longitude and other data and submit
        self.field_ordinate.send_keys('37.97522')
        self.field_abscissa.send_keys('23.73700')
        self.stype_option_important.click()
        self.owner_option_big_tomatoes.click()
        self.field_copyright_holder.send_keys('Alice')
        self.field_copyright_years.send_keys('2015')
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
        self.assertEqual(self.field_ordinate.get_attribute('value'),
                         '37.97522')
        self.assertEqual(self.field_abscissa.get_attribute('value'),
                         '23.737')

        # Switch to the advanced view
        self.button_coordinates.click()
        self.label_ordinate.wait_until_contains("Ordinate")
        self.assertEqual(self.label_ordinate.text, "Ordinate")
        self.assertEqual(self.label_abscissa.text, "Abscissa")
        self.assertTrue(self.field_srid.is_displayed())
        self.assertTrue(self.field_asrid.is_displayed())
        self.assertTrue(self.field_approximate.is_displayed())
        self.assertEqual(self.field_srid.get_attribute('value'), '4326')

        # Enter some advanced data and submit
        self.field_ordinate.clear()
        self.field_ordinate.send_keys('4202810.33')
        self.field_abscissa.clear()
        self.field_abscissa.send_keys('476751.84')
        self.field_srid.clear()
        self.field_srid.send_keys('2100')
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
        self.assertEqual(self.field_srid.get_attribute('value'), '2100')
        self.assertEqual(self.field_ordinate.get_attribute('value'),
                         '4202810.33')
        self.assertEqual(self.field_abscissa.get_attribute('value'),
                         '476751.84')

        # It should be impossible to change to the simple view
        self.assertFalse(self.button_coordinates.is_displayed())


@skipUnless(selenium, 'Selenium is missing or unconfigured')
class ListStationsVisibleOnMapTestCase(SeleniumTestCase):

    button_limit_to_map = PageElement(By.ID, 'limit-to-map')
    td_komboti = PageElement(By.XPATH, '//td[text()="Komboti"]')
    td_agios_athanasios = PageElement(By.XPATH,
                                      '//td[text()="Agios Athanasios"]')
    td_tharbad = PageElement(By.XPATH, '//td[text()="Tharbad"]')

    def setUp(self):
        mommy.make(Station, name="Komboti",
                   point=Point(x=21.06071, y=39.09518, srid=4326), srid=4326)
        mommy.make(Station, name="Agios Athanasios",
                   point=Point(x=21.60121, y=39.22440, srid=4326), srid=4326)
        mommy.make(Station, name="Tharbad",
                   point=Point(x=-176.48368, y=0.19377, srid=4326), srid=4326)

    def test_list_stations_visible_on_map(self):
        # Visit site and wait until three stations are shown
        selenium.get(self.live_server_url)
        self.td_komboti.wait_until_is_displayed()
        self.td_agios_athanasios.wait_until_is_displayed()
        self.td_tharbad.wait_until_is_displayed()

        # Zoom station to an area that covers only two of these stations.
        # The co-ordinates below are 21, 39, 22, 40 in srid=3857.
        selenium.execute_script("""
            enhydris.map.zoomToExtent([2337700, 4721700, 2449000, 4865900]);
            """)

        # Click on "List stations visible on map"
        self.button_limit_to_map.click()

        # Now only two stations should be displayed
        self.td_komboti.wait_until_is_displayed()
        self.td_agios_athanasios.wait_until_is_displayed()
        self.assertFalse(self.td_tharbad.exists())
