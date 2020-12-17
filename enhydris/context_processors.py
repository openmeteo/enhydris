import json

from django.conf import settings


def registration(request):
    """
    Includes settings.REGISTRATION_OPEN in the template context, so that the
    template can decide whether to show the "Register" link. This should be in
    django-registration, however.
    """
    return {"REGISTRATION_OPEN": getattr(settings, "REGISTRATION_OPEN", True)}


def map(request):
    map_base_layers = (
        "{\n"
        + ",\n".join(
            [
                '"{}": {}'.format(name, layer.strip())
                for name, layer in settings.ENHYDRIS_MAP_BASE_LAYERS.items()
            ]
        )
        + "\n}"
    )
    return {
        "map_base_layers": map_base_layers,
        "map_default_base_layer": settings.ENHYDRIS_MAP_DEFAULT_BASE_LAYER,
        "map_viewport": getattr(request, "map_viewport", "[0, 0, 0, 0]"),
        "searchString": json.dumps(request.GET.get("q", "")),
    }
