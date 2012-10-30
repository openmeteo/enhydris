from django.core.serializers import serialize, deserialize
from django.test import TestCase
from enhydris.hcore import models


class PermissionsTestCase(TestCase):
    fixtures = ['api/testdata.json']

    def testEventType(self):
        # Generic call
        url = "/api/EventType/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        objects = deserialize('json', response.content)
        num_obj = sum(1 for obj in objects)
        self.assertEqual(num_obj, models.EventType.objects.all().count())

        # Call for specific object
        object = models.EventType.objects.filter(descr='Test Event Type')[0]
        url = "/api/EventType/%d/" % object.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        o_gen = deserialize('json', response.content)
        d_obj = o_gen.next()
        d_obj.object.id = d_obj.object.pk
        self.assertEqual( getattr(object, 'id'),
                          getattr(d_obj.object, 'pk'))

        # Call for date based filtering

        # Call for non-existent object
        url = "/api/EventType/nonexistent/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def testFileType(self):
        # Generic call
        url = "/api/FileType/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        objects = deserialize('json', response.content)
        num_obj = sum(1 for obj in objects)
        self.assertEqual(num_obj, models.FileType.objects.all().count())

        # Call for specific object
        object = models.FileType.objects.filter(descr='Test File Type')[0]
        url = "/api/FileType/%d/" % object.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        o_gen = deserialize('json', response.content)
        d_obj = o_gen.next()
        d_obj.object.id = d_obj.object.pk
        self.assertEqual( getattr(object, 'id'),
                          getattr(d_obj.object, 'pk'))

        # Call for date based filtering

        # Call for non-existent object
        url = "/api/FileType/nonexistent/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def testGarea(self):
        # Generic call
        url = "/api/Garea/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        objects = deserialize('json', response.content)
        num_obj = sum(1 for obj in objects)
        self.assertEqual(num_obj, models.Garea.objects.all().count())

        # Call for specific object
        object = models.Garea.objects.filter(name='Test Garea')[0]
        url = "/api/Garea/%d/" % object.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        o_gen = deserialize('json', response.content)
        d_obj = o_gen.next()
        d_obj.object.id = d_obj.object.pk
        self.assertEqual( getattr(object, 'id'),
                          getattr(d_obj.object, 'pk'))

        # Call for date based filtering

        # Call for non-existent object
        url = "/api/Garea/nonexistent/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def testGpoint(self):
        # Generic call
        url = "/api/Gpoint/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        objects = deserialize('json', response.content)
        num_obj = sum(1 for obj in objects)
        self.assertEqual(num_obj, models.Gpoint.objects.all().count())

        # Call for specific object
        object = models.Gpoint.objects.all()[0]
        url = "/api/Gpoint/%d/" % object.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        o_gen = deserialize('json', response.content)
        d_obj = o_gen.next()
        d_obj.object.id = d_obj.object.pk
        self.assertEqual( getattr(object, 'id'),
                          getattr(d_obj.object, 'pk'))

        # Call for date based filtering

        # Call for non-existent object
        url = "/api/Gpoint/nonexistent/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def testGentity(self):
        # Generic call
        url = "/api/Gentity/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        objects = deserialize('json', response.content)
        num_obj = sum(1 for obj in objects)
        self.assertEqual(num_obj, models.Gentity.objects.all().count())

        # Call for specific object
        object = models.Gentity.objects.filter(name='Test Gentity')[0]
        url = "/api/Gentity/%d/" % object.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        o_gen = deserialize('json', response.content)
        d_obj = o_gen.next()
        d_obj.object.id = d_obj.object.pk
        self.assertEqual( getattr(object, 'id'),
                          getattr(d_obj.object, 'pk'))

        # Call for date based filtering

        # Call for non-existent object
        url = "/api/Gentity/nonexistent/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

#    def testGentityAltCode(self):
# 
#        # Generic call
#        url = "/api/GentityAltCode/"
#        response = self.client.get(url)
#        self.assertEqual(response.status_code, 200)
#        objects = deserialize('json', response.content)
#        num_obj = sum(1 for obj in objects)
#        self.assertEqual(num_obj, GentityAltCode.objects.all().count())
#
#        # Call for specific object
#        object = GentityAltCode.objects.filter(type='Test Gentity Alt Code')[0]
#        url = "/api/GentityAltCode/%d/" % object.id
#        response = self.client.get(url)
#        self.assertEqual(response.status_code, 200)
#        o_gen = deserialize('json', response.content)
#        d_obj = o_gen.next()
#        for f in object._meta.fields:
#            self.assertEqual( getattr(object, f.name),
#                              getattr(d_obj.object, f.name))
#
#        # Call for date based filtering
#
#        # Call for non-existent object
#        url = "/api/GentityAltCode/nonexistent/"
#        response = self.client.get(url)
#        self.assertEqual(response.status_code, 404)

    def testGentityAltCodeType(self):
        # Generic call
        url = "/api/GentityAltCodeType/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        objects = deserialize('json', response.content)
        num_obj = sum(1 for obj in objects)
        self.assertEqual(num_obj,
                            models.GentityAltCodeType.objects.all().count())

        # Call for specific object
        object = models.GentityAltCodeType.objects.filter(
                                        descr='Test Gentity Alt Code Type')[0]
        url = "/api/GentityAltCodeType/%d/" % object.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        o_gen = deserialize('json', response.content)
        d_obj = o_gen.next()
        d_obj.object.id = d_obj.object.pk
        self.assertEqual( getattr(object, 'id'),
                          getattr(d_obj.object, 'pk'))

        # Call for date based filtering

        # Call for non-existent object
        url = "/api/GentityAltCodeType/nonexistent/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def testGentityFile(self):
        # Generic call
        url = "/api/GentityFile/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        objects = deserialize('json', response.content)
        num_obj = sum(1 for obj in objects)
        self.assertEqual(num_obj, models.GentityFile.objects.all().count())

        # Call for specific object
        object = models.GentityFile.objects.filter(descr='Test Gentity File')[0]
        url = "/api/GentityFile/%d/" % object.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        o_gen = deserialize('json', response.content)
        d_obj = o_gen.next()
        d_obj.object.id = d_obj.object.pk
        self.assertEqual( getattr(object, 'id'),
                          getattr(d_obj.object, 'pk'))

        # Call for date based filtering

        # Call for non-existent object
        url = "/api/GentityFile/nonexistent/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def testInstrument(self):
        # Generic call
        url = "/api/Instrument/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        objects = deserialize('json', response.content)
        num_obj = sum(1 for obj in objects)
        self.assertEqual(num_obj, models.Instrument.objects.all().count())

        # Call for specific object
        object = models.Instrument.objects.filter(name='Test Instrument')[0]
        url = "/api/Instrument/%d/" % object.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        o_gen = deserialize('json', response.content)
        d_obj = o_gen.next()
        self.assertEqual( getattr(object, 'id'),
                          getattr(d_obj.object, 'pk'))
        d_obj.object.id = d_obj.object.pk

        # Call for date based filtering

        # Call for non-existent object
        url = "/api/Instrument/nonexistent/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def testInstrumentType(self):
        # Generic call
        url = "/api/InstrumentType/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        objects = deserialize('json', response.content)
        num_obj = sum(1 for obj in objects)
        self.assertEqual(num_obj, models.InstrumentType.objects.all().count())

        # Call for specific object
        object = models.InstrumentType.objects.filter(
                                            descr='Test Instrument Type')[0]
        url = "/api/InstrumentType/%d/" % object.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        o_gen = deserialize('json', response.content)
        d_obj = o_gen.next()
        d_obj.object.id = d_obj.object.pk
        self.assertEqual( getattr(object, 'id'),
                          getattr(d_obj.object, 'pk'))

        # Call for date based filtering

        # Call for non-existent object
        url = "/api/InstrumentType/nonexistent/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def testLentity(self):
        # Generic call
        url = "/api/Lentity/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        objects = deserialize('json', response.content)
        num_obj = sum(1 for obj in objects)
        self.assertEqual(num_obj, models.Lentity.objects.all().count())

        # Call for specific object
        object = models.Lentity.objects.filter(remarks='Test Owner')[0]
        url = "/api/Lentity/%d/" % object.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        o_gen = deserialize('json', response.content)
        d_obj = o_gen.next()
        d_obj.object.id = d_obj.object.pk
        self.assertEqual( getattr(object, 'id'),
                          getattr(d_obj.object, 'pk'))

        # Call for date based filtering

        # Call for non-existent object
        url = "/api/Lentity/nonexistent/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def testPerson(self):
        # Generic call
        url = "/api/Person/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        objects = deserialize('json', response.content)
        num_obj = sum(1 for obj in objects)
        self.assertEqual(num_obj, models.Person.objects.all().count())

        # Call for specific object
        object = models.Person.objects.filter(last_name='Test Person')[0]
        url = "/api/Person/%d/" % object.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        o_gen = deserialize('json', response.content)
        d_obj = o_gen.next()
        d_obj.object.id = d_obj.object.pk
        self.assertEqual( getattr(object, 'id'),
                          getattr(d_obj.object, 'pk'))

        # Call for date based filtering

        # Call for non-existent object
        url = "/api/Person/nonexistent/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def testOrganization(self):
        # Generic call
        url = "/api/Organization/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        objects = deserialize('json', response.content)
        num_obj = sum(1 for obj in objects)
        self.assertEqual(num_obj, models.Organization.objects.all().count())

        # Call for specific object
        object = models.Organization.objects.filter(name='Test Organization')[0]
        url = "/api/Organization/%d/" % object.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        o_gen = deserialize('json', response.content)
        d_obj = o_gen.next()
        d_obj.object.id = d_obj.object.pk
        self.assertEqual( getattr(object, 'id'),
                          getattr(d_obj.object, 'pk'))

        # Call for date based filtering

        # Call for non-existent object
        url = "/api/Organization/nonexistent/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def testPoliticalDivision(self):
        # Generic call
        url = "/api/PoliticalDivision/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        objects = deserialize('json', response.content)
        num_obj = sum(1 for obj in objects)
        self.assertEqual(num_obj,
                            models.PoliticalDivision.objects.all().count())

        # Call for specific object
        object = models.PoliticalDivision.objects.filter(
                                            name='Test Political Division')[0]
        url = "/api/PoliticalDivision/%d/" % object.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        o_gen = deserialize('json', response.content)
        d_obj = o_gen.next()
        d_obj.object.id = d_obj.object.pk
        self.assertEqual( getattr(object, 'id'),
                          getattr(d_obj.object, 'pk'))

        # Call for date based filtering

        # Call for non-existent object
        url = "/api/PoliticalDivision/nonexistent/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def testStation(self):
        # Generic call
        url = "/api/Station/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        objects = deserialize('json', response.content)
        num_obj = sum(1 for obj in objects)
        self.assertEqual(num_obj, models.Station.objects.all().count())

        # Call for specific object
        object = models.Station.objects.filter(name='Test Station')[0]
        url = "/api/Station/%d/" % object.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        o_gen = deserialize('json', response.content)
        d_obj = o_gen.next()
        d_obj.object.id = d_obj.object.pk
        self.assertEqual( getattr(object, 'id'),
                          getattr(d_obj.object, 'pk'))

        # Call for date based filtering

        # Call for non-existent object
        url = "/api/Station/nonexistent/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def testStationType(self):
        # Generic call
        url = "/api/StationType/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        objects = deserialize('json', response.content)
        num_obj = sum(1 for obj in objects)
        self.assertEqual(num_obj, models.StationType.objects.all().count())

        # Call for specific object
        object = models.StationType.objects.filter(descr='Test Station Type')[0]
        url = "/api/StationType/%d/" % object.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        o_gen = deserialize('json', response.content)
        d_obj = o_gen.next()
        d_obj.object.id = d_obj.object.pk
        self.assertEqual( getattr(object, 'id'),
                          getattr(d_obj.object, 'pk'))

        # Call for date based filtering

        # Call for non-existent object
        url = "/api/StationType/nonexistent/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def testTimeSeries(self):
        # Generic call
        url = "/api/Timeseries/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        objects = deserialize('json', response.content)
        num_obj = sum(1 for obj in objects)
        self.assertEqual(num_obj, models.Timeseries.objects.all().count())

        # Call for specific object
        object = models.Timeseries.objects.filter(name='Test Timeseries')[0]
        url = "/api/Timeseries/%d/" % object.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        o_gen = deserialize('json', response.content)
        d_obj = o_gen.next()
        d_obj.object.id = d_obj.object.pk
        self.assertEqual( getattr(object, 'id'),
                          getattr(d_obj.object, 'pk'))


        # Call for date based filtering

        # Call for non-existent object
        url = "/api/Timeseries/nonexistent/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def testTimeZone(self):
        # Generic call
        url = "/api/TimeZone/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        objects = deserialize('json', response.content)
        num_obj = sum(1 for obj in objects)
        self.assertEqual(num_obj, models.TimeZone.objects.all().count())

        # Call for specific object
        object = models.TimeZone.objects.filter(code='Test Time Zone')[0]
        url = "/api/TimeZone/%d/" % object.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        o_gen = deserialize('json', response.content)
        d_obj = o_gen.next()
        d_obj.object.id = d_obj.object.pk
        self.assertEqual( getattr(object, 'id'),
                          getattr(d_obj.object, 'pk'))

        # Call for date based filtering

        # Call for non-existent object
        url = "/api/TimeZone/nonexistent/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def testTimeStep(self):
        # Generic call
        url = "/api/TimeStep/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        objects = deserialize('json', response.content)
        num_obj = sum(1 for obj in objects)
        self.assertEqual(num_obj, models.TimeStep.objects.all().count())

        # Call for specific object
        object = models.TimeStep.objects.filter(descr='Test Time Step')[0]
        url = "/api/TimeStep/%d/" % object.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        o_gen = deserialize('json', response.content)
        d_obj = o_gen.next()
        d_obj.object.id = d_obj.object.pk
        self.assertEqual( getattr(object, 'id'),
                          getattr(d_obj.object, 'pk'))
        # Call for date based filtering

        # Call for non-existent object
        url = "/api/TimeStep/nonexistent/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def testVariable(self):
        # Generic call
        url = "/api/Variable/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        objects = deserialize('json', response.content)
        num_obj = sum(1 for obj in objects)
        self.assertEqual(num_obj, models.Variable.objects.all().count())

        # Call for specific object
        object = models.Variable.objects.filter(descr='Test Variable')[0]
        url = "/api/Variable/%d/" % object.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        o_gen = deserialize('json', response.content)
        d_obj = o_gen.next()
        d_obj.object.id = d_obj.object.pk
        self.assertEqual( getattr(object, 'id'),
                          getattr(d_obj.object, 'pk'))

        # Call for date based filtering

        # Call for non-existent object
        url = "/api/Variable/nonexistent/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def testUnitOfMeasurements(self):
        # Generic call
        url = "/api/UnitOfMeasurement/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        objects = deserialize('json', response.content)
        num_obj = sum(1 for obj in objects)
        self.assertEqual(num_obj,
                                models.UnitOfMeasurement.objects.all().count())

        # Call for specific object
        object = models.UnitOfMeasurement.objects.filter(
                                            descr='Test Unit Of Measurement')[0]
        url = "/api/UnitOfMeasurement/%d/" % object.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        o_gen = deserialize('json', response.content)
        d_obj = o_gen.next()
        d_obj.object.id = d_obj.object.pk
        self.assertEqual( getattr(object, 'id'),
                          getattr(d_obj.object, 'pk'))
        # Call for date based filtering

        # Call for non-existent object
        url = "/api/UnitOfMeasurement/nonexistent/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def testWaterBasin(self):
        # Generic call
        url = "/api/WaterBasin/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        objects = deserialize('json', response.content)
        num_obj = sum(1 for obj in objects)
        self.assertEqual(num_obj, models.WaterBasin.objects.all().count())

        # Call for specific object
        object = models.WaterBasin.objects.filter(name='Test Water Basin')[0]
        url = "/api/WaterBasin/%d/" % object.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        o_gen = deserialize('json', response.content)
        d_obj = o_gen.next()
        d_obj.object.id = d_obj.object.pk
        self.assertEqual( getattr(object, 'id'),
                          getattr(d_obj.object, 'pk'))


        # Call for date based filtering

        # Call for non-existent object
        url = "/api/WaterBasin/nonexistent/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def testWaterDivision(self):
        # Generic call
        url = "/api/WaterDivision/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        objects = deserialize('json', response.content)
        num_obj = sum(1 for obj in objects)
        self.assertEqual(num_obj, models.WaterDivision.objects.all().count())

        # Call for specific object
        object = models.WaterDivision.objects.filter(
                                                name='Test Water Division')[0]
        url = "/api/WaterDivision/%d/" % object.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        o_gen = deserialize('json', response.content)
        d_obj = o_gen.next()
        self.assertEqual( getattr(object, 'id'),
                          getattr(d_obj.object, 'pk'))

        # Call for date based filtering

        # Call for non-existent object
        url = "/api/WaterDivision/nonexistent/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

class WriteTestCase(TestCase):
    fixtures = ['api/testdata.json']

    def testTimeSeries(self):
        # Get an existing time series
        obj = models.Timeseries.objects.filter(name='Test Timeseries')[0]
        response = self.client.get("/api/Timeseries/%d/" % (obj.id,))
        t = deserialize('json', response.content).next().object

        # Change some of its attributes
        t.id = None
        t.name = "Test Timeseries 1221"
        t.remarks = "Yet another timeseries test"

        # Attempt to upload unauthenticated
        d = serialize('json', [t])
        response = self.client.post("/api/Timeseries/", data=d,
                                            content_type='application/json')
        # Status code should say forbidden. However, due to some bug somewhere
        # (maybe a piston bug), it says OK, though in fact the request has been
        # denied and the row has not been created. Therefore (until the bug
        # is fixed) we don't check the status code, we check only whether the
        # record has been created.
        #self.assertEqual(response.status_code, 403)
        self.assertEqual(models.Timeseries.objects.filter(
                                    name='Test Timeseries 1221').count(), 0)

        # Now try again, this time logged on as user 2; again should deny
        self.assert_(self.client.login(username='user2', password='password2'))
        response = self.client.post("/api/Timeseries/", data=d,
                                            content_type='application/json')
        self.assertEqual(models.Timeseries.objects.filter(
                                    name='Test Timeseries 1221').count(), 0)
        self.client.logout()

        # Now try again, this time logged on as user 1; should accept
        self.assert_(self.client.login(username='user1', password='password1'))
        response = self.client.post("/api/Timeseries/", data=d,
                                            content_type='application/json')
        self.assertEqual(models.Timeseries.objects.filter(
                                    name='Test Timeseries 1221').count(), 1)
        self.client.logout()
