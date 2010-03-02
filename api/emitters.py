from django.core import serializers
from piston.emitters import Emitter

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
