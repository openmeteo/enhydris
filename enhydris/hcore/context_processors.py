import json

from django.conf import settings


def registration(request):
    """
    Includes settings.REGISTRATION_OPEN in the template context, so that the
    template can decide whether to show the "Register" link. This should be in
    django-registration, however.
    """
    return {'REGISTRATION_OPEN': getattr(settings, 'REGISTRATION_OPEN', True)}


def map(request):
    map_js = 'enhydris.mapBaseLayers=[{0}];'.format(
        ','.join(['new ' + layer.strip()
                 for layer in settings.ENHYDRIS_MAP_BASE_LAYERS]))
    map_js += 'enhydris.mapBounds={0};'.format(
        json.dumps(settings.ENHYDRIS_MAP_BOUNDS))
    map_js += 'enhydris.mapMarkers={0};'.format(
        json.dumps(settings.ENHYDRIS_MAP_MARKERS))
    return {'map_js': map_js}
