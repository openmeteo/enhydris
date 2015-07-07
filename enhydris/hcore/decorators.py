from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q
from django.contrib.gis.geos import Polygon
from django.http import Http404
from django.conf import settings
from django.core.exceptions import FieldError

from enhydris.hcore.models import *


def timeseries_permission(function=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for timeseries_download view that checks if only authenticated
    users have access to the data and then acts like the login_required
    decorator. Otherwise, it just calls the function.
    """

    if settings.ENHYDRIS_TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS:
        return function

    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated(),
        redirect_field_name=redirect_field_name
    )

    if function:
        return actual_decorator(function)
    return actual_decorator


def gentityfile_permission(function=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for gentityfile_download view that checks if only authenticated
    users have access to the data and then acts like the login_required
    decorator. Otherwise, it just calls the function.
    """

    if settings.ENHYDRIS_TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS:
        return function

    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated(),
        redirect_field_name=redirect_field_name
    )

    if function:
        return actual_decorator(function)
    return actual_decorator
