from itertools import takewhile

from django.test import TestCase
from django.test.utils import override_settings
from django.utils.unittest import skipUnless
from django.contrib.auth.models import User, Group, Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection as dj_connection

from enhydris.conf import settings
from enhydris.hcore.models import StationType, Organization, Variable, \
    UnitOfMeasurement, TimeZone, Station, Timeseries, InstrumentType, \
    Instrument
from enhydris.hcore.forms import TimeseriesDataForm
from enhydris.hcore.views import ALLOWED_TO_EDIT
from enhydris.hcore.views import get_search_query


class SearchTestCase(TestCase):
    fixtures = ['testdata.json']

    def test_search_in_timeseries_remarks(self):
        # Search for something that exists
        query = get_search_query(['extremely important time series'])
        result = Station.objects.filter(query).distinct()
        self.assertEquals(result.count(), 1)
        self.assertEquals(result[0].id, 3)

        # Search for something that doesn't exist
        query = get_search_query(['this should not exist anywhere'])
        result = Station.objects.filter(query).distinct()
        self.assertEquals(result.count(), 0)


class SmokeTestCase(TestCase):
    """Test that all project URLs return correct status code."""
    #TODO: Run this for all applications, somehow
    #TODO: More customization: 404s, etc
    #TODO: Make this run automatic for all

    pages = {
        200: ['/',
                '/stations/l/',
                '/accounts/login/',
                '/accounts/logout/',
                '/accounts/register/',
                '/accounts/password/reset/',
                '/accounts/password/reset/done/',
                '/admin/',
                '/map/',
                ],
        404: ['/nonexistent/',
                '/stations/d/',
                '/stations/d/nonexistent/',
                '/timeseries/d/',
                '/timeseries/d/nonexistent/',
                '/instruments/d/',
                '/instruments/d/nonexistent/',
                '/account/foob4r/',
                ],
    }

    @override_settings(REGISTRATION_OPEN=True)
    def testStatusCode(self):
        """Test that the response status code is correct"""

        for expected_code in self.pages:
            for page_url in self.pages[expected_code]:
                page = self.client.get(page_url)
                self.assertEquals(
                    page.status_code, expected_code,
                    "Status code for page '%s' was %s instead of %s" %
                    (page_url, page.status_code, expected_code))


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
        self.station = Station.objects.create(name='station',
                                              owner=self.organization)
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

    def testTimeseriesData(self):
        """Test that the timeseries data upload/download is correct"""

        from pthelma import timeseries
        # check uploading
        f = open("enhydris/hcore/tests/tsdata.hts", "r")

        file_dict = {'data': SimpleUploadedFile(f.name, f.read())}
        post_dict = {'gentity': self.station.pk, 'variable': self.var.pk,
                     'unit_of_measurement': self.unit.pk,
                     'time_zone': self.tz.pk
                     }
        form = TimeseriesDataForm(post_dict, file_dict, instance=self.ts)

        self.assertEqual(form.is_valid(), True)
        ts = form.save()

        ts.save()
        pts = timeseries.Timeseries(ts.id)
        pts.read_from_db(dj_connection)
        self.assertEqual(len(pts.items()), 12872)

        #check downloading
        url = "/timeseries/d/%d/download/" % self.ts.pk
        response = self.client.get(url)
        if settings.ENHYDRIS_TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS:
            self.assertEqual(response.status_code, 200)
        else:
            self.assertEqual(response.status_code, 302)
            self.assertEquals(self.client.login(username='test',
                                                password='test'), True)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        # check fiLe
        lines = response.content.splitlines()
        linecount = len(lines)
        headerlinecount = sum([1 for x in takewhile(lambda x: x != '',
                                                    lines)]) + 1
        datalinecount = linecount - headerlinecount

        self.assertEqual(datalinecount, 12872)

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
                                              owner=self.organization)
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
