import mimetypes
import os
from django.core import serializers
from django.core.servers.basehttp import FileWrapper
from django.http import HttpResponse
from piston.emitters import Emitter


class PlainEmitter(Emitter):

    def render(self, request):
        if isinstance(self.data, HttpResponse):
            return self.data
        return HttpResponse(self.data, content_type="text/plain")


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
        if isinstance(self.data, HttpResponse):
            return self.data

        cb = request.GET.get('callback')

        # if self.data has object or queryset serialize and return this
        try:
            seria = serializers.serialize('json', self.data, indent=1)
        except TypeError:
            seria = serializers.serialize('json', [ self.data ], indent=1)

        # Callback
        if cb:
            return '%s(%s)' % (cb, seria)

        return seria


class GFEmitter(Emitter):
    """
    This emitter takes care of reading the GentityFile contents and then
    neding them back to the user as a file.
    """
    def construct(self):
        return None

    def render(self, request):
        """
        In here we do a nasty hack to work around the fact that the emitter
        only allows a specific mimetype per Emitter. We unregister and
        reregister our Emitter after we've guessed the files content_type.
        This may cause problems if content type is guessed wrong.
        """

        # if object wasn't found self data already contains the response
        if isinstance(self.data, HttpResponse):
            Emitter.unregister('gfd')
            Emitter.register('gfd',GFEmitter,'text/plain;utf-8')
            return self.data

        gfile = self.data
        filename = gfile.content.file.name
        wrapper = FileWrapper(open(filename))
        download_name = gfile.content.name.split('/')[-1]
        content_type = mimetypes.guess_type(filename)[0]
        Emitter.unregister('gfd')
        Emitter.register('gfd',GFEmitter,content_type)
        response = HttpResponse(mimetype=content_type)
        response['Content-Length'] = os.path.getsize(filename)
        response['Content-Disposition'] = "attachment;filename=%s"%download_name

        for chunk in wrapper:
            response.write(chunk)

        return response
