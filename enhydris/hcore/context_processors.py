from django.conf import settings


def registration(request):
    """
    Includes settings.REGISTRATION_OPEN in the template context, so that the
    template can decide whether to show the "Register" link. This should be in
    django-registration, however.
    """
    return {'REGISTRATION_OPEN': getattr(settings, 'REGISTRATION_OPEN', True)}
