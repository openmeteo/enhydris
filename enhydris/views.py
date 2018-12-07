from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse

from .models import Timeseries


def download_permission_required(func):
    """Decorator to check for download permission.

    Use like this:

        @download_permission_required
        def do_something():
            ...

    If setting ENHYDRIS_TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS is set, it does nothing.
    Otherwise it is the same as Django's login_required decorator.
    """
    if settings.ENHYDRIS_TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS:
        return func
    else:
        return login_required(func)


@download_permission_required
def timeseries_bottom(request, object_id):
    try:
        atimeseries = Timeseries.objects.get(pk=int(object_id))
    except Timeseries.DoesNotExist:
        raise Http404
    response = HttpResponse(content_type="text/plain; charset=utf-8")
    response.write(atimeseries.get_last_line())
    return response
