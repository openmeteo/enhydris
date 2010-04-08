import mimetypes
import os
from django.core import serializers
from django.core.servers.basehttp import FileWrapper
from django.db import connection as django_db_connection
from django.http import HttpResponse
from piston.emitters import Emitter
from pthelma.timeseries import Timeseries as pts
from enhydris.hcore.models import Timeseries, TimeStep

class CFEmitter(Emitter):
    """
    Custom Fixture emitter.

    Creates JSON fixtures of a model the same way the dumpdata management
    command does. The client, running code similar to loaddata, reads the JSON
    fixtures and updates the db.
    """
    def render(self, request):
        """
        Render function which serializes the actual data.
        """
        cb = request.GET.get('callback')
        seria = serializers.serialize('json', self.data, indent=1)

        # Callback
        if cb:
            return '%s(%s)' % (cb, seria)

        return seria


class TSEmitter(Emitter):
    """
    This emitter takes care of export all ts data from the db and then sending
    them back to the user as a file.
    """
    def construct(self):

        return None

    def render(self, request):
        timeseries = self.data
        # Determine time step and convert it to old format
        t = timeseries.time_step
        if t:
            minutes, months = (t.length_minutes, t.length_months)
        else:
            minutes, months = ( 5, 0)
        old_timestep = 0
        if   (minutes, months) == (   5,  0): old_timestep = 7
        elif (minutes, months) == (  10,  0): old_timestep = 1
        elif (minutes, months) == (  60,  0): old_timestep = 2
        elif (minutes, months) == (1440,  0): old_timestep = 3
        elif (minutes, months) == (   0,  1): old_timestep = 4
        elif (minutes, months) == (   0, 12): old_timestep = 5
        time_step_strict = (not timeseries.nominal_offset_minutes) and (
                                            not timeseries.nominal_offset_months)
        time_step_strict = time_step_strict and 'True' or 'False'

        # Create a proper title and comment
        title = timeseries.name
        if not title: title = 'id=%d' % (timeseries.id)
        title = title.encode('iso-8859-7')
        symbol = timeseries.unit_of_measurement.symbol.encode('iso-8859-7')
        comment = [timeseries.variable.descr.encode('iso-8859-7'),
                   timeseries.gentity.name.encode('iso-8859-7')]

        ts = pts(int(timeseries.id))
        ts.read_from_db(django_db_connection)
        for k in ts.keys(): ts[k] = (ts[k], "") # Remove flags
        response = HttpResponse(mimetype=
                                'text/vnd.openmeteo.timeseries; charset=iso-8859-7')
        response['Content-Disposition'] = "attachment;filename=%s.hts"%(timeseries.id,)
        response.write("Delimiter=,\r\n")
        response.write('FlagDelimiter=" "\r\n')
        response.write("DecimalSeparator=.\r\n")
        response.write("DateFormat=yyyy-mm-dd HH:nn\r\n")
        response.write("TimeStep=%d\r\n" % (old_timestep,))
        response.write("TimeStepStrict=%s\r\n" % (time_step_strict,))
        response.write("MUnit=%s\r\n" % (symbol,))
        response.write('Flags=""\r\n')
        response.write("Variable=0\r\n")# % (timeseries.variable.descr,))
        response.write("VariableType=Unknown\r\n")
        response.write("Title=%s\r\n" % (title,))
        for c in comment: response.write("Comment=%s\r\n" % (c,))
        response.write("\r\n")
        ts.write(response)

        return response

class GFEmitter(Emitter):
    """
    This emitter takes care of reading the GentityFile contents and then
    neding them back to the user as a file.
    """
    def construct(self):
        return None

    def render(self, request):
        gfile = self.data
        filename = gfile.content.file.name
        wrapper = FileWrapper(open(filename))
        download_name = gfile.content.name.split('/')[-1]
        content_type = mimetypes.guess_type(filename)[0]
        response = HttpResponse(mimetype=content_type)
        response['Content-Length'] = os.path.getsize(filename)
        response['Content-Disposition'] = "attachment;filename=%s"%download_name

        for chunk in wrapper:
            response.write(chunk)

        return response
