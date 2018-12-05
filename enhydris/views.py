import os
from tempfile import mkstemp
from wsgiref.util import FileWrapper

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404

import iso8601
import pandas as pd
import pd2hts

from .models import GentityGenericData, Timeseries


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
def download_gentitygenericdata(request, gg_id):
    """
    This function handles requests for gentitygenericdata downloads and serves
    the content to the user.
    """
    ggenericdata = get_object_or_404(GentityGenericData, pk=int(gg_id))
    s = ggenericdata.content
    if s.find("\r") < 0:
        s = s.replace("\n", "\r\n")
    (afile_handle, afilename) = mkstemp()
    os.write(afile_handle, s)
    afile = open(afilename, "r")
    wrapper = FileWrapper(afile)
    download_name = "GenericData-id_%s.%s" % (
        gg_id,
        ggenericdata.data_type.file_extension,
    )
    content_type = "text/plain"
    response = HttpResponse(content_type=content_type)
    response["Content-Length"] = os.fstat(afile_handle).st_size
    response["Content-Disposition"] = "attachment; filename=%s" % download_name
    for chunk in wrapper:
        response.write(chunk)
    return response


def get_date_from_string(adate, tz):
    if not adate:
        return None
    result = iso8601.parse_date(adate, default_timezone=tz)
    if result.isoformat() < pd.Timestamp.min.isoformat():
        result = pd.Timestamp.min
    if result.isoformat() > pd.Timestamp.max.isoformat():
        result = pd.Timestamp.max
    return result


@download_permission_required
def download_timeseries(request, object_id, start_date=None, end_date=None):
    timeseries = get_object_or_404(Timeseries, pk=int(object_id))
    tz = timeseries.time_zone.as_tzinfo
    start_date = get_date_from_string(start_date, tz)
    end_date = get_date_from_string(end_date, tz)

    # The time series data are naive, so we also make start_date and end_date
    # naive.
    if start_date:
        start_date = start_date.replace(tzinfo=None)
    if end_date:
        end_date = end_date.replace(tzinfo=None)

    adataframe = timeseries.get_data(start_date=start_date, end_date=end_date)
    response = HttpResponse(content_type="text/vnd.openmeteo.timeseries; charset=utf-8")
    response["Content-Disposition"] = "attachment; filename=%s.hts" % (object_id,)
    try:
        file_version = int(request.GET.get("version", "2"))
    except ValueError:
        raise Http404
    if file_version not in (2, 3):
        raise Http404
    pd2hts.write_file(adataframe, response, version=file_version)
    return response


@download_permission_required
def timeseries_bottom(request, object_id):
    try:
        atimeseries = Timeseries.objects.get(pk=int(object_id))
    except Timeseries.DoesNotExist:
        raise Http404
    response = HttpResponse(content_type="text/plain; charset=utf-8")
    response.write(atimeseries.get_last_line())
    return response
