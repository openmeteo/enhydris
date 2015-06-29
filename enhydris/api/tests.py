from datetime import datetime
import json

from django.contrib.auth.models import User, Permission
from django.db import connection
from django.test import TestCase
from django.test.client import MULTIPART_CONTENT, BOUNDARY, encode_multipart
from django.test.utils import override_settings

from rest_framework.test import APITestCase

from pthelma.timeseries import Timeseries
from enhydris.hcore import models


def get_gentities_from_fixture():
    """
    This function is used internally by ReadTestCase.testGentityList.
    It gets the fixture data, gets only the gentities from there,
    flattens it, and converts the datetime field to a datetime. The result
    should be a list of dictionaries identical to the one the API returns when
    it is queried for the list of gentities.
    """
    fixture_data = json.load(open('enhydris/api/testdata.json'))
    result = []
    for item in fixture_data:
        if item['model'] != 'hcore.gentity':
            continue
        nitem = {}
        nitem['id'] = item['pk']
        for key in item['fields']:
            if key == 'model':
                continue
            nitem[key] = item['fields'][key]
        result.append(nitem)
    result.sort(key=lambda x: x['id'])
    return result


class ReadTestCase(APITestCase):
    fixtures = ['enhydris/api/testdata.json']

    def testGentityList(self):

        response = self.client.get("/api/Gentity/")
        response.data.sort(key=lambda x: x['id'])
        reference_data = get_gentities_from_fixture()
        self.assertEqual(len(response.data), len(reference_data))
        for res_datum, ref_datum in zip(response.data, reference_data):
            self.assertEqual(len(res_datum), len(ref_datum))
            for key in res_datum:
                if key == 'last_modified':
                    res_datum[key] = datetime.strptime(res_datum[key],
                                                       '%Y-%m-%dT%H:%M:%S')
                    ref_datum[key] = datetime.strptime(ref_datum[key],
                                                       '%Y-%m-%d %H:%M:%S')
                self.assertEqual(res_datum[key], ref_datum[key])

        # Same thing, but test with modified_after
        n_all_gentities = len(reference_data)
        for item in reference_data[:]:
            if item['last_modified'] < datetime(2010, 5, 11):
                reference_data.remove(item)
        n_recent_gentities = len(reference_data)
        self.assertTrue(n_recent_gentities < n_all_gentities)
        response = self.client.get(
            '/api/Gentity/modified_after/2010-05-11 00:00/')
        response.data.sort(key=lambda x: x['id'])
        self.assertEqual(len(response.data), len(reference_data))
        for res_datum, ref_datum in zip(response.data, reference_data):
            self.assertEqual(len(res_datum), len(ref_datum))
            for key in res_datum:
                if key == 'last_modified':
                    res_datum[key] = datetime.strptime(res_datum[key],
                                                       '%Y-%m-%dT%H:%M:%S')
                self.assertEqual(res_datum[key], ref_datum[key])


class WriteTestCase(TestCase):
    fixtures = ['enhydris/api/testdata.json']

    def testTimeSeries(self):
        # Get an existing time series
        obj = models.Timeseries.objects.filter(name='Test Timeseries')[0]
        response = self.client.get("/api/Timeseries/%d/" % (obj.id,))
        t = json.loads(response.content)

        # Change some of its attributes
        t['id'] = None
        t['name'] = "Test Timeseries 1221"
        t['remarks'] = "Yet another timeseries test"

        # Attempt to upload unauthenticated - should deny
        d = json.dumps(t)
        response = self.client.post("/api/Timeseries/", data=d,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(models.Timeseries.objects.filter(
                         name='Test Timeseries 1221').count(), 0)

        # Now try again, this time logged on as user 2; again should deny
        self.assert_(self.client.login(username='user2', password='password2'))
        response = self.client.post("/api/Timeseries/", data=d,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(models.Timeseries.objects.filter(
                         name='Test Timeseries 1221').count(), 0)
        self.client.logout()

        # Now try again, this time logged on as user 1; should accept
        self.assert_(self.client.login(username='user1', password='password1'))
        response = self.client.post("/api/Timeseries/", data=d,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(models.Timeseries.objects.filter(
                         name='Test Timeseries 1221').count(), 1)
        self.client.logout()

    def testTimeseriesDelete(self):
        # Check the number of timeseries available
        ntimeseries = models.Timeseries.objects.count()

        # 1 is not enough; we need to know we aren't
        # deleting more than necessary.
        assert(ntimeseries > 1)

        # Attempt to delete unauthenticated - should fail
        response = self.client.delete("/api/Timeseries/1/")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(models.Timeseries.objects.filter(pk=1).count(), 1)
        self.assertEqual(models.Timeseries.objects.count(), ntimeseries)

        # Try again as user2 - should fail
        self.assert_(self.client.login(username='user2', password='password2'))
        response = self.client.delete("/api/Timeseries/1/")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(models.Timeseries.objects.filter(pk=1).count(), 1)
        self.assertEqual(models.Timeseries.objects.count(), ntimeseries)
        self.client.logout()

        # Try again as user1 - should succeed
        self.assert_(self.client.login(username='user1', password='password1'))
        response = self.client.delete("/api/Timeseries/1/")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(models.Timeseries.objects.filter(pk=1).count(), 0)
        self.assertEqual(models.Timeseries.objects.count(), ntimeseries - 1)
        self.client.logout()

    def testUploadTsDataUnauthenticated(self):
        # Attempt to upload some timeseries data, unauthenticated
        response = self.client.put(
            "/api/tsdata/1/",
            encode_multipart(BOUNDARY,
                             {'timeseries_records': '2012-11-06 18:17,20,\n'}),
            content_type=MULTIPART_CONTENT)
        t = Timeseries(1)
        t.read_from_db(connection)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(t), 0)

    def testUploadTsDataAsWrongUser(self):
        # Attempt to upload some timeseries data as user 2; should deny
        self.assert_(self.client.login(username='user2', password='password2'))
        response = self.client.put(
            "/api/tsdata/1/",
            encode_multipart(BOUNDARY,
                             {'timeseries_records': '2012-11-06 18:17,20,\n'}),
            content_type=MULTIPART_CONTENT)
        t = Timeseries(1)
        t.read_from_db(connection)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(t), 0)
        self.client.logout()

    def testUploadTsDataGarbage(self):
        self.assert_(self.client.login(username='user1', password='password1'))
        response = self.client.put(
            "/api/tsdata/1/",
            encode_multipart(BOUNDARY,
                             {'timeseries_records': '2012-aa-06 18:17,20,\n'}),
            content_type=MULTIPART_CONTENT)
        t = Timeseries(1)
        t.read_from_db(connection)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(t), 0)
        self.client.logout()

    def testUploadTsData(self):
        self.assert_(self.client.login(username='user1', password='password1'))
        response = self.client.put(
            "/api/tsdata/1/",
            encode_multipart(BOUNDARY,
                             {'timeseries_records': '2012-11-06 18:17,20,\n'}),
            content_type=MULTIPART_CONTENT)
        t = Timeseries(1)
        t.read_from_db(connection)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '1')
        self.assertEqual(len(t), 1)
        self.assertEqual(t.items(0)[0], datetime(2012, 11, 06, 18, 17, 0))
        self.assertEqual(t.items(0)[1], 20)
        self.client.logout()

        # Append two more records
        self.assert_(self.client.login(username='user1', password='password1'))
        response = self.client.put(
            "/api/tsdata/1/",
            encode_multipart(BOUNDARY,
                             {'timeseries_records':
                              '2012-11-06 18:18,21,\n2012-11-07 18:18,23,\n'}),
            content_type=MULTIPART_CONTENT)
        t = Timeseries(1)
        t.read_from_db(connection)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '2')
        self.assertEqual(len(t), 3)
        self.assertEqual(t.items(0)[0], datetime(2012, 11, 06, 18, 17, 0))
        self.assertEqual(t.items(0)[1], 20)
        self.assertEqual(t.items(1)[0], datetime(2012, 11, 06, 18, 18, 0))
        self.assertEqual(t.items(1)[1], 21)
        self.assertEqual(t.items(2)[0], datetime(2012, 11, 07, 18, 18, 0))
        self.assertEqual(t.items(2)[1], 23)
        self.client.logout()

        # Try to append an earlier record; should fail
        self.assert_(self.client.login(username='user1', password='password1'))
        response = self.client.put(
            "/api/tsdata/1/",
            encode_multipart(BOUNDARY,
                             {'timeseries_records': '2012-11-05 18:18,21,\n'}),
            content_type=MULTIPART_CONTENT)
        self.client.logout()
        t = Timeseries(1)
        t.read_from_db(connection)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(len(t), 3)
        self.client.logout()


class WriteStationTestCase(TestCase):
    fixtures = ['enhydris/api/testdata.json']

    def test_edit_station(self):
        # Get an existing station
        obj = models.Station.objects.get(name='Test Station')
        response = self.client.get("/api/Station/{}/".format(obj.id))
        station = json.loads(response.content)

        # Change some of its attributes
        station_id = station['id']
        del station['id']
        station['name'] = 'Test Station 1222'
        station['remarks'] = 'Yet another station test'

        # Attempt to upload unauthenticated - should deny
        d = json.dumps(station)
        response = self.client.put('/api/Station/{}/'.format(station_id),
                                   data=d, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(models.Station.objects.filter(
                         name='Test Station 1222').count(), 0)

        # Try again, this time logged on as user 2; again should deny
        self.assertTrue(self.client.login(username='user2',
                                          password='password2'))
        response = self.client.put('/api/Station/{}/'.format(station_id),
                                   data=d, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(models.Station.objects.filter(
                         name='Test Station 1222').count(), 0)
        self.client.logout()

        # Try again, as user 1; should accept
        self.assertTrue(self.client.login(username='user1',
                                          password='password1'))
        response = self.client.put('/api/Station/{}/'.format(station_id),
                                   data=d, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(models.Station.objects.filter(
                         name='Test Station 1222').count(), 1)
        self.client.logout()

    def test_station_delete(self):
        # Check the number of stations available
        nstations = models.Station.objects.count()

        # 1 is not enough; we need to know we aren't
        # deleting more than necessary.
        assert(nstations > 1)

        # Attempt to delete unauthenticated - should fail
        response = self.client.delete('/api/Station/4/')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(models.Station.objects.filter(pk=4).count(), 1)
        self.assertEqual(models.Station.objects.count(), nstations)

        # Try again as user2 - should fail
        self.assertTrue(self.client.login(username='user2',
                                          password='password2'))
        response = self.client.delete('/api/Station/4/')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(models.Station.objects.filter(pk=4).count(), 1)
        self.assertEqual(models.Station.objects.count(), nstations)
        self.client.logout()

        # Try again as user1 - should succeed
        self.assertTrue(self.client.login(username='user1',
                                          password='password1'))
        response = self.client.delete('/api/Station/4/')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(models.Station.objects.filter(pk=4).count(), 0)
        self.assertEqual(models.Station.objects.count(), nstations - 1)
        self.client.logout()


class CreateStationTestCase(TestCase):
    fixtures = ['enhydris/api/testdata.json']

    def setUp(self):
        # Get an existing station
        obj = models.Station.objects.get(name='Test Station')
        response = self.client.get("/api/Station/{}/".format(obj.id))
        self.station = json.loads(response.content)

        # Change some of its attributes
        del self.station['id']
        self.station['name'] = 'Test Station 1507'
        self.station['remarks'] = 'Yet another station test'

    def test_create_unauthenticated(self):
        response = self.client.post('/api/Station/',
                                    data=json.dumps(self.station),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(models.Station.objects.filter(
                         name='Test Station 1507').count(), 0)

    @override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
    def test_create_station_on_database_allowing_any_user(self):
        self.assertTrue(self.client.login(username='user2',
                                          password='password2'))
        response = self.client.post('/api/Station/',
                                    data=json.dumps(self.station),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(models.Station.objects.filter(
            name='Test Station 1507').count(), 1)
        self.client.logout()

    @override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=False)
    def test_create_station_by_disallowed_user(self):
        self.assertTrue(self.client.login(username='user2',
                                          password='password2'))
        response = self.client.post('/api/Station/',
                                    data=json.dumps(self.station),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(models.Station.objects.filter(
            name='Test Station 1507').count(), 0)
        self.client.logout()

    @override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=False)
    def test_create_station_by_allowed_user(self):
        # Give the appropriate permissions to the user
        user = User.objects.get(username='user2')
        permission = Permission.objects.get(codename='add_station')
        user.user_permissions.add(permission)
        user.save()

        self.assertTrue(self.client.login(username='user2',
                                          password='password2'))
        response = self.client.post('/api/Station/',
                                    data=json.dumps(self.station),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(models.Station.objects.filter(
            name='Test Station 1507').count(), 1)
        self.client.logout()
