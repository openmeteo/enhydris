from itertools import takewhile
import re
from StringIO import StringIO
from tempfile import TemporaryFile
from urllib import urlencode

import django
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Group, Permission
from django.contrib.gis.geos import fromstr
from django.db import connection as dj_connection
from django.http import HttpRequest, QueryDict
from django.test import TestCase
from django.test.utils import override_settings

from pthelma import timeseries

from django.conf import settings

from enhydris.hcore.models import (
    FileType, GentityFile, Instrument, InstrumentType, IntervalType,
    Organization, PoliticalDivision, Station, StationType, TimeZone,
    Timeseries, UnitOfMeasurement, UserProfile, Variable, WaterBasin,
    WaterDivision)
from enhydris.hcore.forms import TimeseriesDataForm
from enhydris.hcore.views import ALLOWED_TO_EDIT, StationListBaseView


def create_test_data():
    user1 = User.objects.create_user('admin', 'anthony@itia.ntua.gr',
                                     'topsecret')
    user1.is_active = True
    user1.is_superuser = True
    user1.is_staff = True
    user1.save()

    organization1 = Organization.objects.create(
        name="We're rich and we fancy it SA")
    organization2 = Organization.objects.create(
        name="We're poor and dislike it Ltd")
    organization3 = Organization.objects.create(
        name="We get all your money and enjoy it plc")

    water_division1 = WaterDivision.objects.create(
        name="North Syldavia Basins")
    water_division2 = WaterDivision.objects.create(
        name="South Syldavia Basins")
    # water_division3
    WaterDivision.objects.create(name="East Syldavia Basins")
    # water_division4
    WaterDivision.objects.create(name="West Syldavia Basins")

    water_basin1 = WaterBasin.objects.create(name="Arachthos")
    water_basin2 = WaterBasin.objects.create(name="Pinios")
    water_basin3 = WaterBasin.objects.create(name="Greyflood")

    # Political divisions
    # +-> Greece       +-> Epirus   +-> Preveza
    # |                |            +-> Arta
    # |                +-> Thessaly +-> Karditsa
    # |                             +-> Magnisia
    # +-> Middle Earth +-> Eriador  +-> Arthedain
    #                  |            +-> Cardolan
    #                  +-> Gondor   +-> Lamedon
    #                               +-> Lebbenin
    pd = PoliticalDivision
    pd_greece = pd.objects.create(name="Greece")
    pd_epirus = pd.objects.create(name="Epirus", parent=pd_greece)
    pd_thessaly = pd.objects.create(name="Thessaly", parent=pd_greece)
    # pd_preveza
    pd.objects.create(name="Preveza", parent=pd_epirus)
    pd_arta = pd.objects.create(name="Arta", parent=pd_epirus)
    pd_karditsa = pd.objects.create(name="Karditsa", parent=pd_thessaly)
    # pd_magnisia
    pd.objects.create(name="Magnisia", parent=pd_thessaly)
    pd_middleearth = pd.objects.create(name="Middle Earth")
    pd_eriador = pd.objects.create(name="Eriador", parent=pd_middleearth)
    pd_gondor = pd.objects.create(name="Gondor", parent=pd_middleearth)
    # pd_arthedain
    pd.objects.create(name="Arthedain", parent=pd_eriador)
    pd_cardolan = pd.objects.create(name="Cardolan", parent=pd_eriador)
    # pd_lamedon
    pd.objects.create(name="Lamedon", parent=pd_gondor)
    # pd_lebbenin
    pd.objects.create(name="Lamedon", parent=pd_gondor)

    stype1 = StationType.objects.create(descr="Important")
    stype2 = StationType.objects.create(descr="Unimportant")
    stype3 = StationType.objects.create(descr="Even less significant")

    # filetype1
    FileType.objects.create(mime_type='image/jpeg')

    variable1 = Variable.objects.create(descr='Rainfall')
    variable2 = Variable.objects.create(descr='Temperature')

    unit_of_measurement1 = UnitOfMeasurement.objects.create(
        descr='millimeter', symbol='mm')
    unit_of_measurement1.variables = [variable1]
    unit_of_measurement1.save()
    unit_of_measurement2 = UnitOfMeasurement.objects.create(
        descr='Degrees Celsius', symbol=u'\u00b0C')
    unit_of_measurement2.variables = [variable2]
    unit_of_measurement2.save()

    timezone1 = TimeZone.objects.create(code='EET', utc_offset=120)

    # interval_type1
    IntervalType.objects.create(
        descr='Sum', value='SUM', descr_alt='Sum')
    # interval_type2
    IntervalType.objects.create(
        descr='Average value', value='AVERAGE', descr_alt='Average value')
    # interval_type3
    IntervalType.objects.create(
        descr='Minimum', value='MINIMUM', descr_alt='Minimum')
    # interval_type4
    IntervalType.objects.create(
        descr='Maximum', value='MAXIMUM', descr_alt='Maximum')
    # interval_type5
    IntervalType.objects.create(
        descr='Vector average', value='VECTOR_AVERAGE',
        descr_alt='Vector average')

    station1 = Station.objects.create(
        name='Komboti',
        approximate=False,
        is_active=False,
        is_automatic=False,
        copyright_holder="We're poor and dislike it Ltd",
        copyright_years='2013',
        owner=organization2,
        water_division=water_division1,
        water_basin=water_basin1,
        political_division=pd_arta)
    station1.stype = [stype1]
    station1.save()
    station2 = Station.objects.create(
        name='Agios Athanasios',
        approximate=False,
        is_active=False,
        is_automatic=False,
        copyright_holder="We're poor and dislike it Ltd",
        copyright_years='2013',
        owner=organization2,
        water_division=water_division2,
        water_basin=water_basin2,
        political_division=pd_karditsa)
    station2.stype = [stype1, stype2]
    station2.save()
    station3 = Station.objects.create(
        name='Tharbad',
        approximate=False,
        is_active=False,
        is_automatic=False,
        copyright_holder="Isaac Newton",
        copyright_years='1687',
        owner=organization1,
        water_division=water_division2,
        water_basin=water_basin3,
        political_division=pd_cardolan)
    station3.stype = [stype2]
    station3.save()

    # Station 4 has no time series
    station4 = Station.objects.create(
        name='Lefkada',
        approximate=False,
        is_active=False,
        is_automatic=False,
        copyright_holder='Alice Brown',
        copyright_years='2014',
        owner=organization3)
    station4.stype = [stype3]
    station4.save()

    # timeseries1
    Timeseries.objects.create(
        unit_of_measurement=unit_of_measurement1,
        gentity=station1,
        time_zone=timezone1,
        variable=variable1,
        name='Rain')
    # timeseries2
    Timeseries.objects.create(
        unit_of_measurement=unit_of_measurement2,
        gentity=station1,
        time_zone=timezone1,
        variable=variable2,
        name='Air temperature')
    # timeseries3
    Timeseries.objects.create(
        unit_of_measurement=unit_of_measurement1,
        gentity=station2,
        time_zone=timezone1,
        variable=variable1,
        name='Rain')
    # timeseries4
    Timeseries.objects.create(
        unit_of_measurement=unit_of_measurement2,
        gentity=station2,
        time_zone=timezone1,
        variable=variable2,
        name='Air temperature')
    # timeseries5
    Timeseries.objects.create(
        unit_of_measurement=unit_of_measurement2,
        gentity=station3,
        time_zone=timezone1,
        variable=variable2,
        name='Temperature',
        remarks='This is an extremely important time series, just because it '
                'is hugely significant and markedly outstanding.')


class SearchTestCase(TestCase):

    def setUp(self):
        create_test_data()

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
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset[0].name, 'Tharbad')

        # Search for something that doesn't exist
        queryset = self.get_queryset(urlencode({
            'q': 'this should not exist anywhere'}))
        self.assertEquals(queryset.count(), 0)

    def test_search_by_owner(self):
        queryset = self.get_queryset(urlencode({'q': 'owner:RiCh'}))
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset[0].owner.organization.name,
                          "We're rich and we fancy it SA")
        queryset = self.get_queryset(urlencode({'owner': 'poor'}))
        self.assertEquals(queryset.count(), 2)
        self.assertEquals(queryset[0].owner.organization.name,
                          "We're poor and dislike it Ltd")
        queryset = self.get_queryset(urlencode({'owner': 'nonexistent'}))
        self.assertEquals(queryset.count(), 0)

    def test_search_by_type(self):
        # The following will find both "Important" and "Unimportant" stations,
        # because the string "important" is included in "Unimportant".
        queryset = self.get_queryset(urlencode({'q': 'type:Important'}))
        queryset = queryset.distinct()
        self.assertEquals(queryset.count(), 3)

        queryset = self.get_queryset(urlencode({'type': 'Unimportant'}))
        queryset = queryset.order_by('name')
        self.assertEquals(queryset.count(), 2)
        self.assertEquals(queryset[0].name, 'Agios Athanasios')
        self.assertEquals(queryset[1].name, 'Tharbad')

        queryset = self.get_queryset(urlencode({'type': 'Nonexistent'}))
        self.assertEquals(queryset.count(), 0)

    def test_search_by_water_division(self):
        queryset = self.get_queryset(urlencode({'q': 'water_division:north'}))
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset[0].name, 'Komboti')

        queryset = self.get_queryset(urlencode({'q': 'water_division:south'}))
        queryset = queryset.order_by('name')
        self.assertEquals(queryset.count(), 2)
        self.assertEquals(queryset[0].name, 'Agios Athanasios')
        self.assertEquals(queryset[1].name, 'Tharbad')

        queryset = self.get_queryset(urlencode({'q': 'water_division:east'}))
        self.assertEquals(queryset.count(), 0)

    def test_search_by_water_basin(self):
        queryset = self.get_queryset(urlencode({'q': 'water_basin:arachthos'}))
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset[0].name, 'Komboti')

        queryset = self.get_queryset(urlencode({'water_basin': 'greyflood'}))
        queryset = queryset.order_by('name')
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset[0].name, 'Tharbad')

        queryset = self.get_queryset(urlencode({'water_basin': 'nonexistent'}))
        self.assertEquals(queryset.count(), 0)

    def test_search_by_variable(self):
        queryset = self.get_queryset(urlencode({'q': 'variable:rain'}))
        queryset = queryset.order_by('name')
        self.assertEquals(queryset.count(), 2)
        self.assertEquals(queryset[0].name, 'Agios Athanasios')
        self.assertEquals(queryset[1].name, 'Komboti')

        queryset = self.get_queryset(urlencode({'q': 'variable:temperature'}))
        queryset = queryset.order_by('name')
        self.assertEquals(queryset.count(), 3)
        self.assertEquals(queryset[0].name, 'Agios Athanasios')
        self.assertEquals(queryset[1].name, 'Komboti')
        self.assertEquals(queryset[2].name, 'Tharbad')

        queryset = self.get_queryset(urlencode({'q': 'variable:nonexistent'}))
        self.assertEquals(queryset.count(), 0)

    def test_search_by_gentityId(self):
        station_id = Station.objects.get(name='Komboti').id
        queryset = self.get_queryset(urlencode({'gentityId': str(station_id)}))
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset[0].name, 'Komboti')

        queryset = self.get_queryset(urlencode({'gentityId': '98765'}))
        self.assertEquals(queryset.count(), 0)

    def test_search_by_ts_only(self):
        queryset = self.get_queryset('')
        self.assertEquals(queryset.count(), 4)
        queryset = self.get_queryset(urlencode({'q': 'ts_only:'}))
        self.assertEquals(queryset.count(), 3)

    def test_search_by_political_division(self):
        queryset = self.get_queryset(
            urlencode({'political_division': 'Cardolan'}))
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset[0].name, 'Tharbad')

        queryset = self.get_queryset(
            urlencode({'political_division': 'Arthedain'}))
        self.assertEquals(queryset.count(), 0)

        queryset = self.get_queryset(
            urlencode({'political_division': 'Karditsa'}))
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset[0].name, 'Agios Athanasios')

        queryset = self.get_queryset(
            urlencode({'political_division': 'Arta'}))
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset[0].name, 'Komboti')

        queryset = self.get_queryset(
            urlencode({'political_division': 'Epirus'}))
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset[0].name, 'Komboti')

        queryset = self.get_queryset(
            urlencode({'political_division': 'Greece'}))
        queryset = queryset.order_by('name')
        self.assertEquals(queryset.count(), 2)
        self.assertEquals(queryset[0].name, 'Agios Athanasios')
        self.assertEquals(queryset[1].name, 'Komboti')

        queryset = self.get_queryset(
            urlencode({'political_division': 'Middle Earth'}))
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset[0].name, 'Tharbad')


class GentityFileTestCase(TestCase):

    def setUp(self):
        create_test_data()

    def test_gentity_file(self):

        # Upload a gentity file
        gentity_id = Station.objects.get(name='Komboti').id
        r = self.client.login(username='admin', password='topsecret')
        self.assertTrue(r)
        self.assertEquals(GentityFile.objects.filter(gentity__id=gentity_id
                                                     ).count(), 0)
        filetype_id = FileType.objects.get(mime_type='image/jpeg').id
        with TemporaryFile(suffix='.jpg') as tmpfile:
            tmpfile.write('Irrelevant data\n')
            tmpfile.seek(0)
            response = self.client.post(reverse('gentityfile_add'),
                                        {'gentity': gentity_id,
                                         'date': '',
                                         'file_type': filetype_id,
                                         'descr': 'A description',
                                         'remarks': '',
                                         'descr_alt': 'An alt description',
                                         'remarks_alt': '',
                                         'content': tmpfile,
                                         })
        self.assertEquals(response.status_code, 302)
        self.assertEquals(GentityFile.objects.filter(gentity__id=gentity_id
                                                     ).count(), 1)

        # Now try to download that gentity file
        gentity_file_id = GentityFile.objects.all()[0].id
        response = self.client.get(reverse('gentityfile_dl',
                                           kwargs={'gf_id': gentity_file_id}))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, 'Irrelevant data\n')


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
        self.tz = TimeZone.objects.create(code='UTC', utc_offset='0')
        self.tz.save()
        self.station = Station.objects.create(
            name='station',
            owner=self.organization,
            approximate=False,
            is_active=True,
            is_automatic=True,
            point=fromstr('POINT(24.67890 38.12345)'),
            srid=4326,
            altitude=219.22)
        self.station.save()
        self.ts = Timeseries(name="tstest", gentity=self.station,
                             time_zone=self.tz,
                             unit_of_measurement=self.unit,
                             variable=self.var)
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

    def test_timeseries_data(self):
        # Upload
        with open("enhydris/hcore/tests/tsdata.hts", "r") as f:
            file_dict = {'data': SimpleUploadedFile(f.name, f.read())}
        post_dict = {'gentity': self.station.pk, 'variable': self.var.pk,
                     'unit_of_measurement': self.unit.pk,
                     'time_zone': self.tz.pk
                     }
        form = TimeseriesDataForm(post_dict, file_dict, instance=self.ts)
        self.assertTrue(form.is_valid())
        ts = form.save()
        ts.save()
        pts = timeseries.Timeseries(ts.id)
        pts.read_from_db(dj_connection)
        self.assertEqual(len(pts.items()), 12872)

        # Download

        def nrecords():
            lines = response.content.splitlines()
            linecount = len(lines)
            headerlinecount = sum([1 for x in takewhile(lambda x: x != '',
                                                        lines)]) + 1
            return linecount - headerlinecount

        if not settings.ENHYDRIS_TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS:
            self.client.login(username='test', password='test')

        url = "/timeseries/d/{}/download/".format(self.ts.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.splitlines()[0].strip(), 'Version=2')
        self.assertEqual(nrecords(), 12872)

        url = "/timeseries/d/{}/download/?version=3".format(self.ts.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        ats = timeseries.Timeseries()
        ats.read_file(StringIO(response.content))
        self.assertAlmostEqual(ats.location['abscissa'], 24.67890, places=6)
        self.assertAlmostEqual(ats.location['ordinate'], 38.12345, places=6)
        self.assertEqual(ats.location['srid'], 4326)
        self.assertAlmostEqual(ats.location['altitude'], 219.22, places=2)
        self.assertTrue(ats.location['asrid'] is None)
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
                                              is_active=True,
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
            self.assertEquals(
                page.status_code, 302,
                "Status code for page '%s' was %s instead of %s" %
                (page_url, page.status_code, 302))
            self.assertRedirects(
                page, '/accounts/login/?next=%s' % page_url, status_code=302,
                target_status_code=200)

        self.assertEquals(self.client.login(username='opentest',
                                            password='opentest'), True)

        # check that logged in users can see the forms
        for page_url in self.pages:
            page = self.client.get(page_url)
            self.assertEquals(
                page.status_code, 200,
                "Status code for page '%s' was %s instead of %s" %
                (page_url, page.status_code, 200))

        self.client.logout()

    def testStationPermissions(self):
        """
        Check that edit forms honour the permissions.
        """

        self.assertEquals(self.client.login(username='opentest',
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
        self.assertEquals(resp.status_code, 302)

        s = Station.objects.get(name='station_test')

        # edit my station. this should work
        url = "/stations/edit/%s/" % str(s.pk)
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed(resp, "station_edit.html")

        # delete my station. this should work
        url = "/stations/delete/%s/" % str(s.pk)
        resp = self.client.get(url, follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(Station.objects.filter(name='station_test').count(),
                          0)

        # try to edit a random station. this should fail
        url = "/stations/edit/%s/" % str(self.station.pk)
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 403)

        # try to delete a random station. this should fail
        url = "/stations/delete/%s/" % str(self.station.pk)
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 403)

        # recreate again for further tests
        url = "/stations/add/"
        resp = self.client.post(url, post_data)
        self.assertEquals(resp.status_code, 302)

        s = Station.objects.get(name='station_test')

        self.client.logout()

        # login as another user to check 403 perms
        self.assertEquals(self.client.login(username='fail', password='fail'),
                          True)

        # edit station. this shouldn't work
        url = "/stations/edit/%s/" % str(s.pk)
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 403)

        # delete station. this shouldn't work
        url = "/stations/delete/%s/" % str(s.pk)
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 403)

        # add user to maintainers and check if it's fixed.
        s.maintainers.add(self.user2)
        s.save()

        # edit maintaining station. this should work
        url = "/stations/edit/%s/" % str(s.pk)
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed(resp, "station_edit.html")

        # delete maintaining station. this shouldn't work
        url = "/stations/delete/%s/" % str(s.pk)
        resp = self.client.get(url, follow=True)
        self.assertEquals(resp.status_code, 403)

        self.client.logout()
        s.delete()

    def testTimeseriesPermissions(self):
        """
        Check that edit forms honour the permissions.
        """
        self.assertEquals(self.client.login(username='opentest',
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
        self.assertEquals(resp.status_code, 302)

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
        self.assertEquals(resp.status_code, 302)

        t = Timeseries.objects.get(name="timeseries_test")

        # edit my timeseries. this should work
        url = "/timeseries/edit/%s/" % str(t.pk)
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed(resp, "timeseries_edit.html")

        # delete my timeseries. this should work
        url = "/timeseries/delete/%s/" % str(t.pk)
        resp = self.client.get(url, follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(Station.objects.filter(
            name='timeseries_test').count(), 0)

        # recreate deleted timeseries for further tests
        url = "/timeseries/add/"
        resp = self.client.post(url, post_data)
        t = Timeseries.objects.get(name="timeseries_test")
        self.assertEquals(resp.status_code, 302)

        self.client.logout()

        # login as another user to check 403 perms
        self.assertEquals(self.client.login(username='fail', password='fail'),
                          True)

        # edit my timeseries. this shouldn't work
        url = "/timeseries/edit/%s/" % str(t.pk)
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 403)

        # delete my timeseries. this shouldn't work
        url = "/timeseries/delete/%s/" % str(t.pk)
        resp = self.client.get(url, follow=True)
        self.assertEquals(resp.status_code, 403)

        # add user to maintainers and check if it's fixed.
        s.maintainers.add(self.user2)
        s.save()

        # edit maintaining timeseries. this should work
        url = "/timeseries/edit/%s/" % str(t.pk)
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed(resp, "timeseries_edit.html")

        # delete maintaining timeseries, this should work
        url = "/timeseries/delete/%s/" % str(t.pk)
        resp = self.client.get(url, follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(Station.objects.filter(
            name='timeseries_test').count(), 0)

        s.delete()

    def testInstrumentPermissions(self):
        """
        Check that edit forms honour the permissions.
        """

        self.assertEquals(self.client.login(username='opentest',
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
        self.assertEquals(resp.status_code, 302)

        s = Station.objects.get(name='station_test')

        post_data = {
            'name': 'instrument_test',
            'station': s.pk,
            'type': self.itype.pk
        }

        # create new instrument
        url = "/instrument/add/"
        resp = self.client.post(url, post_data)
        self.assertEquals(resp.status_code, 302)

        i = Instrument.objects.get(name="instrument_test")

        # edit my instrument. this should work
        url = "/instrument/edit/%s/" % str(i.pk)
        resp = self.client.get(url, follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed(resp, "instrument_edit.html")

        # delete my station. this should work
        url = "/instrument/delete/%s/" % str(i.pk)
        resp = self.client.get(url, follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(Station.objects.filter(
            name='instrument_test').count(), 0)

        # recreate deleted instrument for further tests
        url = "/instrument/add/"
        resp = self.client.post(url, post_data)
        self.assertEquals(resp.status_code, 302)

        i = Instrument.objects.get(name="instrument_test")

        self.client.logout()

        # login as another user to check 403 perms
        self.assertEquals(self.client.login(username='fail', password='fail'),
                          True)

        # edit my instrument. this shouldn't work
        url = "/instrument/edit/%s/" % str(i.pk)
        resp = self.client.get(url, follow=True)
        self.assertEquals(resp.status_code, 403)

        # delete my instrument. this shouldn't work
        url = "/instrument/delete/%s/" % str(i.pk)
        resp = self.client.get(url, follow=True)
        self.assertEquals(resp.status_code, 403)

        # add user to maintainers and check if it's fixed.
        s.maintainers.add(self.user2)
        s.save()

        # edit my instrument. this should work
        url = "/instrument/edit/%s/" % str(i.pk)
        resp = self.client.get(url, follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed(resp, "instrument_edit.html")

        # delete my station. this should work
        url = "/instrument/delete/%s/" % str(i.pk)
        resp = self.client.get(url, follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(Station.objects.filter(
            name='instrument_test').count(), 0)

    def testGenericModelCreation(self):
        """
        Test the generic model forms
        """
        self.assertEquals(self.client.login(username='opentest',
                                            password='opentest'), True)

        for model in ALLOWED_TO_EDIT:
            url = "/add/%s/?_popup=1" % model
            resp = self.client.get(url)
            self.assertEquals(resp.status_code, 200, "Error in page %s." % url)
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
        self.auser = User.objects.create_user(
            username='auser', email='irrelevant@example.com',
            password='topsecret')
        self.auser.save()
        self.auser.user_permissions.add(
            Permission.objects.get(codename='add_station'))

    def tearDown(self):
        self.auser.delete()

    @override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
    def test_add_station(self):
        """
        Test that the add station form appears properly.
        """
        r = self.client.login(username='auser', password='topsecret')
        self.assertTrue(r)
        response = self.client.get('/stations/add/')
        self.assertEqual(response.status_code, 200)


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
        self.assertEquals(response.status_code, 302)
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
