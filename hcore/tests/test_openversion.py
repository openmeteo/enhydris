from django.conf import settings
from django.contrib.auth.models import User, Group
from django.test import TestCase
from enhydris.hcore.views import ALLOWED_TO_EDIT
from enhydris.hcore.models import *

class OpenVTestCase(TestCase):
    """
    Test that the behaviour of the site when USERS_CAN_ADD_CONTENT is set to
    TRUE is as expected.
    """
    fixtures = ['hcore/initial_data/groups.json',]

    def setUp(self):
        # change settings
        self.old_setting = settings.USERS_CAN_ADD_CONTENT
        settings.USERS_CAN_ADD_CONTENT = True
        # create user and add him to editors group
        self.user = User.objects.create_user('opentest', 'opentest@test.com', 'opentest')
        self.editors = Group.objects.get(name='editors')
        self.editors.user_set.add(self.user)

        # create a station, instrument and timeseries to check permissions
        self.stype = StationType.objects.create(descr='stype')
        self.itype = InstrumentType.objects.create(descr='itype')
        self.organization = Organization.objects.create(name='org')
        self.var = Variable.objects.create(descr='var')
        self.unit = UnitOfMeasurement.objects.create(symbol='+')
        self.unit.variables.add(self.var)
        self.tz = TimeZone.objects.create(code='UTC', utc_offset='0')
        self.station = Station.objects.create(name='station', type=self.stype,
            owner=self.organization)
        self.ts = Timeseries(name="tstest", gentity=self.station,
            time_zone=self.tz, unit_of_measurement=self.unit, variable=self.var)
        self.ts.save()

    def tearDown(self):
        settings.USERS_CAN_ADD_CONTENT = self.old_setting
        self.user.delete()
        self.stype.delete()
        self.organization.delete()
        self.var.delete()
        self.unit.delete()
        self.tz.delete()
        self.ts.delete()

    def testStatusCode(self):
        """Test that the response status code is correct"""
        self.pages = [
                '/stations/add/',
                '/timeseries/add/',
                '/instrument/add/'
        ]

        # check that anonymous users cannot see the forms
        for page_url in self.pages:
            page = self.client.get(page_url)
            self.assertEquals(page.status_code, 302,
                "Status code for page '%s' was %s instead of %s" %
                (page_url, page.status_code, 302))
            self.assertRedirects(page, '/accounts/login/?next=%s' % page_url,
                 status_code=302,target_status_code=200)

        self.assertEquals(self.client.login(username='opentest',
                password='opentest'), True)

        # check that logged in users can see the forms
        for page_url in self.pages:
            page = self.client.get(page_url)
            self.assertEquals(page.status_code, 200,
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
            'name' : 'station_test',
            'type' : self.stype.pk,
            'owner' : self.organization.pk,
            'creator' : self.user.pk,
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
        resp = self.client.get(url, follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed(resp, "hcore/station_edit.html")

        # delete my station. this should work
        url = "/stations/delete/%s/" % str(s.pk)
        resp = self.client.get(url, follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(Station.objects.filter(name='station_test').count(),0)

        # try to edit a random station. this should fail
        url = "/stations/edit/%s/" % str(self.station.pk)
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 403)

        self.client.logout()

    def testTimeseriesPermissions(self):
        """
        Check that edit forms honour the permissions.
        """
        self.assertEquals(self.client.login(username='opentest',
                password='opentest'), True)

        post_data = {
            'name' : 'station_test',
            'type' : self.stype.pk,
            'owner' : self.organization.pk,
            'creator' : self.user.pk,
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
            'name' : 'timeseries_test',
            'gentity' : s.pk,
            'time_zone' : self.tz.pk,
            'variable' : self.var.pk,
            'unit_of_measurement' : self.unit.pk
        }

        # create new timeseries
        url = "/timeseries/add/"
        resp = self.client.post(url, post_data)
        self.assertEquals(resp.status_code, 302)

        t = Timeseries.objects.get(name="timeseries_test")

        # edit my timeseries. this should work
        url = "/timeseries/edit/%s/" % str(t.pk)
        resp = self.client.get(url, follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed(resp, "hcore/timeseries_edit.html")

        # delete my station. this should work
        url = "/timeseries/delete/%s/" % str(t.pk)
        resp = self.client.get(url, follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(Station.objects.filter(name='timeseries_test').count(),0)

        self.client.logout()

    def testInstrumentPermissions(self):
        """
        Check that edit forms honour the permissions.
        """

        self.assertEquals(self.client.login(username='opentest',
                password='opentest'), True)

        post_data = {
            'name' : 'station_test',
            'type' : self.stype.pk,
            'owner' : self.organization.pk,
            'creator' : self.user.pk,
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
        self.assertTemplateUsed(resp, "hcore/instrument_edit.html")

        # delete my station. this should work
        url = "/instrument/delete/%s/" % str(i.pk)
        resp = self.client.get(url, follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(Station.objects.filter(name='instrument_test').count(),0)

        self.client.logout()

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
            self.assertTemplateUsed(resp, "hcore/model_add.html")

        self.client.logout()


