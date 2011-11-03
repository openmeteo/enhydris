import os.path
from django.core.serializers import serialize, deserialize
from django.contrib.auth.models import User, Group
from django.test import TestCase, Client
from enhydris.hcore.models import *


class PermissionsTestCase(TestCase):
    fixtures = ['api/testdata.json']

    def testEventType(self):
        # Generic call
        url = "/api/EventType/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        objects = deserialize('json', response.content)
        num_obj = sum(1 for obj in objects)
        self.assertEqual(num_obj, EventType.objects.all().count())

        # Call for specific object
        object = EventType.objects.filter(descr='Test Event Type')[0]
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
        self.assertEqual(num_obj, FileType.objects.all().count())

        # Call for specific object
        object = FileType.objects.filter(descr='Test File Type')[0]
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
        self.assertEqual(num_obj, Garea.objects.all().count())

        # Call for specific object
        object = Garea.objects.filter(name='Test Garea')[0]
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
        self.assertEqual(num_obj, Gpoint.objects.all().count())

        # Call for specific object
        object = Gpoint.objects.all()[0]
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
        self.assertEqual(num_obj, Gentity.objects.all().count())

        # Call for specific object
        object = Gentity.objects.filter(name='Test Gentity')[0]
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
        self.assertEqual(num_obj, GentityAltCodeType.objects.all().count())

        # Call for specific object
        object = GentityAltCodeType.objects.filter(descr='Test Gentity Alt Code Type')[0]
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
        self.assertEqual(num_obj, GentityFile.objects.all().count())

        # Call for specific object
        object = GentityFile.objects.filter(descr='Test Gentity File')[0]
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
        self.assertEqual(num_obj, Instrument.objects.all().count())

        # Call for specific object
        object = Instrument.objects.filter(name='Test Instrument')[0]
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
        self.assertEqual(num_obj, InstrumentType.objects.all().count())

        # Call for specific object
        object = InstrumentType.objects.filter(descr='Test Instrument Type')[0]
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
        self.assertEqual(num_obj, Lentity.objects.all().count())

        # Call for specific object
        object = Lentity.objects.filter(remarks='Test Owner')[0]
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
        self.assertEqual(num_obj, Person.objects.all().count())

        # Call for specific object
        object = Person.objects.filter(last_name='Test Person')[0]
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
        self.assertEqual(num_obj, Organization.objects.all().count())

        # Call for specific object
        object = Organization.objects.filter(name='Test Organization')[0]
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
        self.assertEqual(num_obj, PoliticalDivision.objects.all().count())

        # Call for specific object
        object = PoliticalDivision.objects.filter(name='Test Political Division')[0]
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
        self.assertEqual(num_obj, Station.objects.all().count())

        # Call for specific object
        object = Station.objects.filter(name='Test Station')[0]
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
        self.assertEqual(num_obj, StationType.objects.all().count())

        # Call for specific object
        object = StationType.objects.filter(descr='Test Station Type')[0]
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
        self.assertEqual(num_obj, Timeseries.objects.all().count())

        # Call for specific object
        object = Timeseries.objects.filter(name='Test Timeseries')[0]
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
        self.assertEqual(num_obj, TimeZone.objects.all().count())

        # Call for specific object
        object = TimeZone.objects.filter(code='Test Time Zone')[0]
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
        self.assertEqual(num_obj, TimeStep.objects.all().count())

        # Call for specific object
        object = TimeStep.objects.filter(descr='Test Time Step')[0]
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
        self.assertEqual(num_obj, Variable.objects.all().count())

        # Call for specific object
        object = Variable.objects.filter(descr='Test Variable')[0]
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
        self.assertEqual(num_obj, UnitOfMeasurement.objects.all().count())

        # Call for specific object
        object = UnitOfMeasurement.objects.filter(descr='Test Unit Of Measurement')[0]
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
        self.assertEqual(num_obj, WaterBasin.objects.all().count())

        # Call for specific object
        object = WaterBasin.objects.filter(name='Test Water Basin')[0]
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
        self.assertEqual(num_obj, WaterDivision.objects.all().count())

        # Call for specific object
        object = WaterDivision.objects.filter(name='Test Water Division')[0]
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
        obj = Timeseries.objects.filter(name='Test Timeseries')[0]
        response = self.client.get("/api/Timeseries/%d/" % (obj.id,))
        t = deserialize('json', response.content).next().object

        # Change some of its attributes
        t.id = None
        t.name = "Test Timeseries 1221"
        t.remarks = "Yet another timeseries test"

        # Upload
        d = serialize('json', [t])
        response = self.client.post("/api/Timeseries/", data=d,
                                            content_type='application/json')
        # Status code should say forbidden. However, due to some bug somewhere
        # (maybe a piston bug), it says OK, though in fact the request has been
        # denied and the row has not been created. Therefore (until the bug
        # is fixed) we don't check the status code, we check only whether the
        # record has been created.
        #self.assertEqual(response.status_code, 403)
        self.assertEqual(
            Timeseries.objects.filter(name='Test Timeseries 1221').count(), 0)
