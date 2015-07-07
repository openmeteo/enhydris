"""
These template tags are for counting. Used in the frontpage stats
"""

from django.conf import settings
from django.template import Library, Node, TemplateSyntaxError
from django.db.models import get_model

from enhydris.hcore.models import *

register = Library()

def do_count(appmodel):
    try:
        model = get_model(*appmodel.split('.'))
        count = model.objects.all().count()
    except:
        count = 0

    return count

register.simple_tag( do_count )


class LastModifiedStations(Node):
    def __init__(self, number=5):
        self.number = number

    def render(self, context):
        try:
            station_objects = Station.objects.all()
            if len(settings.ENHYDRIS_SITE_STATION_FILTER)>0:
                station_objects = station_objects.filter(**settings.ENHYDRIS_SITE_STATION_FILTER)
            latest_stations = station_objects.all().order_by('last_modified').reverse()[:self.number]
        except ValueError:
            latest_stations = None

        context['latest_stations'] = latest_stations
        return ''

class DoGetLatestStations:

    def __init__(self):
        pass

    def __call__(self, parser, token):
        tokens = token.contents.split()
        if not tokens[1].isdigit():
            raise TemplateSyntaxError, (
                "The argument for '%s' must be an integer" % tokens[0])
        return LastModifiedStations(tokens[1])

register.tag('get_latest_stations', DoGetLatestStations())
