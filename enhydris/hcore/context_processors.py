from django.conf import settings


def registration(request):
    """
    Includes settings.REGISTRATION_OPEN in the template context, so that the
    template can decide whether to show the "Register" link. This should be in
    django-registration, however.
    """
    return {'REGISTRATION_OPEN': getattr(settings, 'REGISTRATION_OPEN', True)}


def osm(request):
    osm_base_layers_js = 'base_layers=[{0}];'.format(
        ','.join(['new ' + layer.strip()
                 for layer in settings.ENHYDRIS_OSM_BASE_LAYERS]))
    return {'osm_base_layers_js': osm_base_layers_js}
