"""
These template tags are for converting from srid 2100 to the one that google is
using.
"""

from django.template import Library, Node, TemplateSyntaxError
from pyproj import Proj, transform
from enhydris.conf import settings
from enhydris.hcore.models import Station

register = Library()

def get_longitude(station_id):
    """
    Get station longitude in 4326 srid
    """

    try:
        station = Station.objects.get(id=station_id)
    except:
        return None

    if station.abscissa == station.ordinate == None:
        return None

    p1 = Proj(init='epsg:2100')
    p2 = Proj(init='epsg:4326')
    (latitude, longitude) = transform(p1, p2, station.abscissa,
                                        station.ordinate)

    return longitude


def get_latitude(station_id):
    """
    Get station latitude in 4326 srid
    """

    try:
        station = Station.objects.get(id=station_id)
    except:
        return None

    p1 = Proj(init='epsg:2100')
    p2 = Proj(init='epsg:4326')

    if station.abscissa == station.ordinate == None:
        return None

    (latitude, longitude) = transform(p1, p2, station.abscissa,
                                        station.ordinate)

    return latitude


register.simple_tag(get_longitude)
register.simple_tag(get_latitude)
