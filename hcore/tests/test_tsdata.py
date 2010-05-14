from itertools import takewhile
import unittest
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection as dj_connection
from django.test.client import Client
from enhydris.hcore.models import (Station, StationType, Organization, Timeseries,
                            TimeZone, Variable, UnitOfMeasurement)
from enhydris.hcore.forms import TimeseriesDataForm

class TsTestCase(unittest.TestCase):
    """Test timeseries data upload/download code."""

    def setUp(self):
        self.client = Client()
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
        self.station = Station.objects.create(name='station', type=self.stype,
            owner=self.organization)
        self.station.save()
        self.ts = Timeseries(name="tstest", gentity=self.station,
            time_zone=self.tz, unit_of_measurement=self.unit, variable=self.var)
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
        f = open("hcore/tests/tsdata.hts","r")

        file_dict = {'data': SimpleUploadedFile(f.name, f.read())}
        post_dict = {'gentity':self.station.pk, 'variable':self.var.pk,
                        'unit_of_measurement': self.unit.pk,
                        'time_zone':self.tz.pk}
        form = TimeseriesDataForm(post_dict, file_dict, instance=self.ts)

        self.assertEqual(form.is_valid(), True)
        ts = form.save()

        ts.save()
        pts = timeseries.Timeseries(ts.id)
        pts.read_from_db(dj_connection)
        self.assertEqual(len(pts.items()), 12872)

        #check downloading
        url= "/timeseries/d/%d/download/" % self.ts.pk
        response = self.client.get(url)
        if hasattr(settings, 'TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS') and\
          settings.TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS:
            self.assertEqual(response.status_code, 200)
        else:
            self.assertEqual(response.status_code, 302)
            self.assertEquals(self.client.login(username='test',
                            password='test'), True)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        # check fiLe
        lines = sum(1 for line in response.content.split('\n'))
        start = takewhile(lambda x: not x=='', response.content.split('\n'))
        lines = lines - sum(1 for s in start.next())

        self.assertEqual(lines,12872)

        self.client.logout()
