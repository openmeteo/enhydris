from django.conf import settings
from django.contrib.auth.models import User, Group, Permission
from django.test import TestCase
from enhydris.hcore.views import ALLOWED_TO_EDIT
from enhydris.hcore.models import *


class OpenVTestCase(TestCase):
    """
    Test that the behaviour of the site when USERS_CAN_ADD_CONTENT is set to
    TRUE is as expected.
    """

    def setUp(self):
        self.assertEqual(settings.USERS_CAN_ADD_CONTENT, True, ("You need to"
        " have USERS_CAN_ADD_CONTENT=True in your settings for this test to"
        " run"))

        # Create the editors group
        permitted = ["eventtype", "filetype", "garea", "gentityaltcode",
            "gentityaltcodetype", "gentityevent", "gentityfile", "gline",
            "instrument", "instrumenttype", "overseer", "politicaldivision",
            "station", "stationtype", "timeseries", "timestep", "timezone",
            "unitofmeasurement", "userprofile", "variable", "waterbasin",
            "waterdivision", "person", "organization", "gentitygenericdatatype"]
        editors = Group(name='editors')
        editors.save()
        for x in ('add', 'change', 'delete'):
            for y in permitted:
                editors.permissions.add(
                            Permission.objects.get(codename=x+'_'+y))

        # create user and add him to editors group. this'll be the
        # creator/owner to check permissions
        self.user = User.objects.create_user('opentest', 'opentest@test.com', 'opentest')
        # another user who won't have permissions over the tested objects to
        # verify that permission handling works as expected.
        self.user2 = User.objects.create_user('fail', 'fail@faildom.com', 'fail')
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
        self.station = Station.objects.create(name='station', type=self.stype,
            owner=self.organization)
        self.ts = Timeseries(name="tstest", gentity=self.station,
            time_zone=self.tz, unit_of_measurement=self.unit, variable=self.var)
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
        self.assertEquals(Station.objects.filter(name='station_test').count(),0)

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
        self.assertEquals(self.client.login(username='fail',
                password='fail'), True)

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
            'name' : 'station_test',
            'type' : self.stype.pk,
            'owner' : self.organization.pk,
            'creator' : self.user.pk,
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
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed(resp, "timeseries_edit.html")

        # delete my timeseries. this should work
        url = "/timeseries/delete/%s/" % str(t.pk)
        resp = self.client.get(url, follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(Station.objects.filter(name='timeseries_test').count(),0)

        # recreate deleted timeseries for further tests
        url = "/timeseries/add/"
        resp = self.client.post(url, post_data)
        t = Timeseries.objects.get(name="timeseries_test")
        self.assertEquals(resp.status_code, 302)

        self.client.logout()

        # login as another user to check 403 perms
        self.assertEquals(self.client.login(username='fail',
                password='fail'), True)

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
        self.assertEquals(Station.objects.filter(name='timeseries_test').count(),0)


        s.delete()

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
        self.assertEquals(Station.objects.filter(name='instrument_test').count(),0)

        # recreate deleted instrument for further tests
        url = "/instrument/add/"
        resp = self.client.post(url, post_data)
        self.assertEquals(resp.status_code, 302)

        i = Instrument.objects.get(name="instrument_test")

        self.client.logout()

        # login as another user to check 403 perms
        self.assertEquals(self.client.login(username='fail',
                password='fail'), True)

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
        self.assertEquals(Station.objects.filter(name='instrument_test').count(),0)

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
