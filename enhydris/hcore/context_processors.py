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
    map_js = 'enhydris.map_base_layers=[{0}];'.format(
        ','.join(['new ' + layer.strip()
                 for layer in settings.ENHYDRIS_MAP_BASE_LAYERS]))
    map_js += 'enhydris.map_bounds={0};'.format(
        json.dumps(settings.ENHYDRIS_MAP_BOUNDS))
    map_js += 'enhydris.map_markers={0};'.format(
        json.dumps(settings.ENHYDRIS_MAP_MARKERS))
    return {'map_js': map_js}
