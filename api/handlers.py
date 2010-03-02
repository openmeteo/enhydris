import string
from piston.handler import BaseHandler
from piston.utils import rc
from hydroscope.hcore.models import *


class StationHandler(BaseHandler):
    allowed_methods = ('GET',)
    model = Station

    def read(self, request, station_id):
        """Return a station object"""
        station = None
        try:
            station = Station.objects.get(id=station_id)
        except Station.DoesNotExist:
            pass
        return station

#WARNING!!! This part accepts XHR requests only in the last version crafted by
# yml, so it must be cloned from the following url:
# hg clone https://bitbucket.org/yml/django-piston/

class StationListHandler(BaseHandler):
    allowed_methods = ('POST',)
    model = Station

    def create(self, request):
        """
        Return a set of station objects.

        In fact there is no creation of object in this function. This function
        just reads a set of station ids and returns the corresponding station
        objects.
        """
        response = []
        if not request.POST.has_key('station_list'):
            return rc.BAD_REQUEST
        ids = string.split(request.POST['station_list'],sep=",")
        for station_id in ids:
            if station_id:
                try:
                    station = Station.objects.get(id=station_id)
                    response.append(station)
                except Station.DoesNotExist:
                    pass
        return response

class Lookup_Handler(BaseHandler):
    """
    API handler for hcore model Lookup.
    """
    model = Lookup
    exclude = ()

class Lentity_Handler(BaseHandler):
    """
    API handler for hcore model Lentity.
    """
    model = Lentity
    exclude = ()

class Person_Handler(BaseHandler):
    """
    API handler for hcore model Person.
    """
    model = Person
    exclude = ()

class Organization_Handler(BaseHandler):
    """
    API handler for hcore model Organization.
    """
    model = Organization
    exclude = ()

class Gentity_Handler(BaseHandler):
    """
    API handler for hcore model Gentity.
    """
    model = Gentity
    exclude = ()

class Gpoint_Handler(BaseHandler):
    """
    API handler for hcore model Gpoint.
    """
    model = Gpoint
    exclude = ()

class Gline_Handler(BaseHandler):
    """
    API handler for hcore model Gline.
    """
    model = Gline
    exclude = ()

class Garea_Handler(BaseHandler):
    """
    API handler for hcore model Garea.
    """
    model = Garea
    exclude = ()

class PoliticalDivisionManager_Handler(BaseHandler):
    """
    API handler for hcore model PoliticalDivisionManager.
    """
    model = PoliticalDivisionManager
    exclude = ()

class PoliticalDivision_Handler(BaseHandler):
    """
    API handler for hcore model PoliticalDivision.
    """
    model = PoliticalDivision
    exclude = ()

class WaterDivision_Handler(BaseHandler):
    """
    API handler for hcore model WaterDivision.
    """
    model = WaterDivision
    exclude = ()

class WaterBasin_Handler(BaseHandler):
    """
    API handler for hcore model WaterBasin.
    """
    model = WaterBasin
    exclude = ()

class GentityAltCodeType_Handler(BaseHandler):
    """
    API handler for hcore model GentityAltCodeType.
    """
    model = GentityAltCodeType
    exclude = ()

class GentityAltCode_Handler(BaseHandler):
    """
    API handler for hcore model GentityAltCode.
    """
    model = GentityAltCode
    exclude = ()

class FileType_Handler(BaseHandler):
    """
    API handler for hcore model FileType.
    """
    model = FileType
    exclude = ()

class GentityFile_Handler(BaseHandler):
    """
    API handler for hcore model GentityFile.
    """
    model = GentityFile
    exclude = ()

class EventType_Handler(BaseHandler):
    """
    API handler for hcore model EventType.
    """
    model = EventType
    exclude = ()

class GentityEvent_Handler(BaseHandler):
    """
    API handler for hcore model GentityEvent.
    """
    model = GentityEvent
    exclude = ()

class StationType_Handler(BaseHandler):
    """
    API handler for hcore model StationType.
    """
    model = StationType
    exclude = ()

class StationManager_Handler(BaseHandler):
    """
    API handler for hcore model StationManager.
    """
    model = StationManager
    exclude = ()

class Station_Handler(BaseHandler):
    """
    API handler for hcore model Station.
    """
    model = Station
    exclude = ('creator',)

class Overseer_Handler(BaseHandler):
    """
    API handler for hcore model Overseer.
    """
    model = Overseer
    exclude = ()

class InstrumentType_Handler(BaseHandler):
    """
    API handler for hcore model InstrumentType.
    """
    model = InstrumentType
    exclude = ()

class Instrument_Handler(BaseHandler):
    """
    API handler for hcore model Instrument.
    """
    model = Instrument
    exclude = ()

class Variable_Handler(BaseHandler):
    """
    API handler for hcore model Variable.
    """
    model = Variable
    exclude = ()

class UnitOfMeasurement_Handler(BaseHandler):
    """
    API handler for hcore model UnitOfMeasurement.
    """
    model = UnitOfMeasurement
    exclude = ()

class TimeZone_Handler(BaseHandler):
    """
    API handler for hcore model TimeZone.
    """
    model = TimeZone
    exclude = ()

class TimeStep_Handler(BaseHandler):
    """
    API handler for hcore model TimeStep.
    """
    model = TimeStep
    exclude = ()

class Timeseries_Handler(BaseHandler):
    """
    API handler for hcore model Timeseries.
    """
    model = Timeseries
    exclude = ()
