import string
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from piston.handler import BaseHandler
from piston.utils import rc
from enhydris.hcore.models import *

class StationHandler(BaseHandler):
    model = Station
    fields = ('id', 'name', 'srid', 'abscissa', 'ordinate', 'altitude',
                'asrid','is_active',
                ('water_basin',('name',)),
                ('water_division',('name',)),
                ('political_division',('name',)),
                ('type',('descr',)),
                ('owner',('name_any',)))

class StationListHandler(BaseHandler):
    allowed_methods = ('POST')
    model = Station
    fields = ('id', 'name', 'srid', 'abscissa', 'ordinate', 'altitude',
                'asrid','is_active',
                ('water_basin',('name',)),
                ('water_division',('name',)),
                ('political_division',('name',)),
                ('type',('descr',)),
                ('owner',('name_any',)))

    def create(self, request, *args, **kwargs):
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

# Timeseries handler for ts data
class TSDATA_Handler(BaseHandler):
    """
    This handler is responsible for taking a timeseries id and returning the
    actual timeseries data to the client.
    """
    def read(self, request, ts_id, *args, **kwargs):
        try:
            timeseries = Timeseries.objects.get(pk=int(ts_id))
        except:
            return rc.NOT_FOUND
        return timeseries

class GFDATA_Handler(BaseHandler):
    """
    This handler serves the GentityFile contents using piston API.
    """
    def read(self, request, gf_id, *args, **kwargs):
        try:
            gfile = GentityFile.objects.get(pk=int(gf_id))
        except:
            return rc.NOT_FOUND

        return gfile


# Generic Handler including modification date filtering

class GenericHandler(BaseHandler):
    """
    Generic handler which adds support to request all models modified after a
    specific date.
    """
    def queryset(self, request):
        return self.model.objects.all()

    def read(self, request, *args, **kwargs):
        if not self.has_model():
            return rc.NOT_IMPLEMENTED

        pkfield = self.model._meta.pk.name

        if pkfield in kwargs:
            try:
                return self.queryset(request).get(pk=kwargs.get(pkfield))
            except ObjectDoesNotExist:
                return rc.NOT_FOUND
            except MultipleObjectsReturned: # should never happen, since we're using a PK
                return rc.BAD_REQUEST
        elif 'date' in kwargs:
            return self.queryset(request).filter(last_modified__gt=("%s")
                            % (kwargs['date']))
        else:
            return self.queryset(request).filter(*args, **kwargs)

# Regular handlers for the rest of the models
class Lookup_Handler(GenericHandler):
    model = Lookup
    exclude = ()

class Lentity_Handler(GenericHandler):
    model = Lentity
    exclude = ()

class Person_Handler(GenericHandler):
    model = Person
    exclude = ()

class Organization_Handler(GenericHandler):
    model = Organization
    exclude = ()

class Gentity_Handler(GenericHandler):
    model = Gentity
    exclude = ()

class Gpoint_Handler(GenericHandler):
    model = Gpoint
    exclude = ()

class Gline_Handler(GenericHandler):
    model = Gline
    exclude = ()

class Garea_Handler(GenericHandler):
    model = Garea
    exclude = ()

class PoliticalDivisionManager_Handler(GenericHandler):
    model = PoliticalDivisionManager
    exclude = ()

class PoliticalDivision_Handler(GenericHandler):
    model = PoliticalDivision
    exclude = ()

class WaterDivision_Handler(GenericHandler):
    model = WaterDivision
    exclude = ()

class WaterBasin_Handler(GenericHandler):
    model = WaterBasin
    exclude = ()

class GentityAltCodeType_Handler(GenericHandler):
    model = GentityAltCodeType
    exclude = ()

class GentityAltCode_Handler(GenericHandler):
    model = GentityAltCode
    exclude = ()

class FileType_Handler(GenericHandler):
    model = FileType
    exclude = ()

class GentityFile_Handler(GenericHandler):
    model = GentityFile
    exclude = ()

class EventType_Handler(GenericHandler):
    model = EventType
    exclude = ()

class GentityEvent_Handler(GenericHandler):
    model = GentityEvent
    exclude = ()

class StationType_Handler(GenericHandler):
    model = StationType
    exclude = ()

class StationManager_Handler(GenericHandler):
    model = StationManager
    exclude = ()

class Station_Handler(GenericHandler):
    model = Station
    exclude = ('creator',)

class Overseer_Handler(GenericHandler):
    model = Overseer
    exclude = ()

class InstrumentType_Handler(GenericHandler):
    model = InstrumentType
    exclude = ()

class Instrument_Handler(GenericHandler):
    model = Instrument
    exclude = ()

class Variable_Handler(GenericHandler):
    model = Variable
    exclude = ()

class UnitOfMeasurement_Handler(GenericHandler):
    model = UnitOfMeasurement
    exclude = ()

class TimeZone_Handler(GenericHandler):
    model = TimeZone
    exclude = ()

class TimeStep_Handler(GenericHandler):
    model = TimeStep
    exclude = ()

class Timeseries_Handler(GenericHandler):
    model = Timeseries
    exclude = ()

    def create(self, request):
        if request.content_type:
            fields = request.data[0]['fields']
            for x in ('unit_of_measurement', 'instrument', 'gentity',
                        'interval_type', 'time_zone', 'time_step', 'variable'):
                fields[x+'_id'] = fields[x]
                del(fields[x])
            station = get_object_or_404(Station, id=fields['gentity_id'])
            if not hasattr(request.user, 'has_row_perm'
                        ) or not request.user.has_row_perm(station, 'edit'):
                response = rc.FORBIDDEN
                return response
            t = self.model(**fields)
            t.save()
            return HttpResponse(str(t.id), mimetype="text/plain")
        else:
            super(Timeseries, self).create(request)
