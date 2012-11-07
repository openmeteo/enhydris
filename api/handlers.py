import string
from StringIO import StringIO

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import connection
from piston.handler import BaseHandler
from piston.utils import rc

from enhydris.hcore import models
from enhydris.api.authentication import RemoteInstanceAuthentication
from pthelma.timeseries import Timeseries, TimeStep

ts_auth = RemoteInstanceAuthentication(realm="Timeseries realm")


class StationHandler(BaseHandler):
    model = models.Station
    fields = ('id', 'name', 'srid', 'abscissa', 'ordinate', 'altitude',
                'asrid','is_active',
                ('water_basin',('name',)),
                ('water_division',('name',)),
                ('political_division',('name',)),
                ('type',('descr',)),
                ('owner',('name_any',)))


class StationListHandler(BaseHandler):
    allowed_methods = ('POST')
    model = models.Station
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
                    station = models.Station.objects.get(id=station_id)
                    response.append(station)
                except models.Station.DoesNotExist:
                    pass

        return response


class TSDATA_Handler(BaseHandler):
    """
    This handler is responsible for taking a timeseries id and returning the
    actual timeseries data to the client, or for updating a time series with
    new records.
    """

    def read(self, request, ts_id, *args, **kwargs):
        # We perform an authentication test here. Normally this should be done
        # in urls.py, by passing ts_auth as the "authentication" parameter to
        # Resource. However, we need different authentication mechanisms for
        # "read" and for "create". "read" is only meant for remote instances
        # when Enhydris works in distributed mode; "create" is for anyone
        # (provided he has permissions on that particular time series). So we
        # do this hack. It's not well tested, and, really, piston must be
        # replaced with tastypie or django-rest-framework, and all this must be
        # rethought.
        if not ts_auth.is_authenticated(request):
            return ts_auth.challenge()
        try:
            timeseries = models.Timeseries.objects.get(pk=int(ts_id))
        except:
            return rc.NOT_FOUND

        t = timeseries # Nick because we use it a lot below
        time_step = TimeStep(
            length_minutes = t.time_step.length_minutes if t.time_step else 0,
            length_months = t.time_step.length_months if t.time_step else 0)
        nominal_offset = (t.nominal_offset_minutes, t.nominal_offset_months)\
            if t.nominal_offset_minutes and t.nominal_offset_months else None
        actual_offset = (t.actual_offset_minutes, t.actual_offset_months)\
            if t.actual_offset_minutes and t.actual_offset_months else (0,0)
        ts = Timeseries(id = int(t.id),
            time_step = time_step,
            nominal_offset = nominal_offset,
            actual_offset = actual_offset,
            unit = t.unit_of_measurement.symbol,
            title = t.name,
            timezone = '%s (UTC+%02d%02d)' % (t.time_zone.code,
                t.time_zone.utc_offset / 60, t.time_zone.utc_offset % 60),
            variable = t.variable.descr,
            precision = t.precision,
            comment = '%s\n\n%s' % (t.gentity.name, t.remarks)
        )
        ts.read_from_db(connection)
        response = HttpResponse(mimetype=
                                'text/vnd.openmeteo.timeseries; charset=utf-8')
        response['Content-Disposition'] = "attachment; filename=%s.hts"%(t.id,)
        ts.write_file(response)
        return response

    def create(self, request, ts_id):
        try:
            timeseries = models.Timeseries.objects.get(id = ts_id)
        except models.Timeseries.DoesNotExist as e:
            resp = rc.NOT_FOUND
            resp.content = 'Timeseries with id={0} does not exist'.format(ts_id)
            return resp
        if (not hasattr(request.user, 'has_row_perm')) or (not request.user.
                    has_row_perm(timeseries.gentity.gpoint.station, 'edit')):
            return rc.FORBIDDEN
        ts = Timeseries(id = int(ts_id))
        try:
            result_if_error=rc.BAD_REQUEST
            ts.read(StringIO(request.POST['timeseries_records']))
            result_if_error=rc.DUPLICATE_ENTRY
            ts.append_to_db(connection, commit=False)
        except ValueError as e:
            result_if_error.content = str(e)
            return result_if_error
        return str(len(ts))


class GFDATA_Handler(BaseHandler):
    """
    This handler serves the GentityFile contents using piston API.
    """

    def read(self, request, gf_id, *args, **kwargs):
        try:
            gfile = models.GentityFile.objects.get(pk=int(gf_id))
        except:
            return rc.NOT_FOUND

        return gfile


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


class Lookup_Handler(GenericHandler):
    model = models.Lookup
    exclude = ()


class Lentity_Handler(GenericHandler):
    model = models.Lentity
    exclude = ()


class Person_Handler(GenericHandler):
    model = models.Person
    exclude = ()


class Organization_Handler(GenericHandler):
    model = models.Organization
    exclude = ()


class Gentity_Handler(GenericHandler):
    model = models.Gentity
    exclude = ()


class Gpoint_Handler(GenericHandler):
    model = models.Gpoint
    exclude = ()


class Gline_Handler(GenericHandler):
    model = models.Gline
    exclude = ()


class Garea_Handler(GenericHandler):
    model = models.Garea
    exclude = ()


class PoliticalDivisionManager_Handler(GenericHandler):
    model = models.PoliticalDivisionManager
    exclude = ()


class PoliticalDivision_Handler(GenericHandler):
    model = models.PoliticalDivision
    exclude = ()


class WaterDivision_Handler(GenericHandler):
    model = models.WaterDivision
    exclude = ()


class WaterBasin_Handler(GenericHandler):
    model = models.WaterBasin
    exclude = ()


class GentityAltCodeType_Handler(GenericHandler):
    model = models.GentityAltCodeType
    exclude = ()


class GentityAltCode_Handler(GenericHandler):
    model = models.GentityAltCode
    exclude = ()


class FileType_Handler(GenericHandler):
    model = models.FileType
    exclude = ()


class GentityFile_Handler(GenericHandler):
    model = models.GentityFile
    exclude = ()


class EventType_Handler(GenericHandler):
    model = models.EventType
    exclude = ()


class GentityEvent_Handler(GenericHandler):
    model = models.GentityEvent
    exclude = ()


class StationType_Handler(GenericHandler):
    model = models.StationType
    exclude = ()


class StationManager_Handler(GenericHandler):
    model = models.StationManager
    exclude = ()


class Station_Handler(GenericHandler):
    model = models.Station
    exclude = ('creator',)


class Overseer_Handler(GenericHandler):
    model = models.Overseer
    exclude = ()


class InstrumentType_Handler(GenericHandler):
    model = models.InstrumentType
    exclude = ()


class Instrument_Handler(GenericHandler):
    model = models.Instrument
    exclude = ()


class Variable_Handler(GenericHandler):
    model = models.Variable
    exclude = ()


class UnitOfMeasurement_Handler(GenericHandler):
    model = models.UnitOfMeasurement
    exclude = ()


class TimeZone_Handler(GenericHandler):
    model = models.TimeZone
    exclude = ()


class TimeStep_Handler(GenericHandler):
    model = models.TimeStep
    exclude = ()


class Timeseries_Handler(GenericHandler):
    model = models.Timeseries
    exclude = ()

    def create(self, request):
        if not request.content_type:
            return rc.FORBIDDEN
        fields = request.data[0]['fields']

        # The keys to fields must be strings, not unicode, for Python versions
        # up to 2.6.4, because of http://bugs.python.org/issue4978, otherwise
        # the statement "t = self.model(**fields)" below fails.
        for x in fields:
            if x.__class__==unicode:
                val = fields[x]
                del fields[x]
                fields[str(x)] = val

        for x in ('unit_of_measurement', 'instrument', 'gentity',
                    'interval_type', 'time_zone', 'time_step', 'variable'):
            fields[x+'_id'] = fields[x]
            del(fields[x])
        station = get_object_or_404(models.Station, id=fields['gentity_id'])
        if not hasattr(request.user, 'has_row_perm'
                    ) or not request.user.has_row_perm(station, 'edit'):
            return rc.FORBIDDEN
        t = self.model(**fields)
        t.save()
        return HttpResponse(str(t.id), mimetype="text/plain")
