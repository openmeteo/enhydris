import mimetypes
import os
from tempfile import mkstemp
from wsgiref.util import FileWrapper

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.gis.db.models import Extent
from django.contrib.gis.geos import Polygon
from django.db.models import Count, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import ListView

import iso8601
import pandas as pd
import pd2hts

from .csv import prepare_csv
from .models import GentityFile, GentityGenericData, Station, Timeseries


class StationListBaseView(ListView):
    template_name = ""
    model = Station

    def get_paginate_by(self, queryset):
        return getattr(settings, "ENHYDRIS_STATIONS_PER_PAGE", 100)

    def get_context_data(self, **kwargs):
        context = super(StationListBaseView, self).get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        context["enabled_user_content"] = settings.ENHYDRIS_USERS_CAN_ADD_CONTENT
        return context


class StationListView(StationListBaseView):
    template_name = "station_list.html"

    def get_sort_order(self):
        """Get sort_order as a list: from the request parameters, otherwise
        from request.session, otherwise it's the default, ['name']. Removes
        duplicate column occurences from the list.
        """
        sort_order = self.request.GET.getlist("sort")

        # Ensure sort order term to match with Station model field names
        field_names = [x.name for x in Station._meta.get_fields()]
        sort_order = [x for x in sort_order if x in field_names]

        if not sort_order:
            sort_order = self.request.session.get("sort", ["name"])

        sort_order = sort_order[:]
        for i in range(len(sort_order) - 1, -1, -1):
            s = sort_order[i]
            if s[0] == "-":
                s = s[1:]
            if (s in sort_order[:i]) or ("-" + s in sort_order[:i]):
                del sort_order[i]
        self.sort_order = sort_order

    def get(self, request, *args, **kwargs):
        # The CSV is an undocumented feature we quickly and dirtily created
        # for some people who needed it.
        if request.GET.get("format", "").lower() == "csv":
            zipfilename = prepare_csv(self.get_queryset())
            response = HttpResponse(
                open(zipfilename, "rb").read(), content_type="application/zip"
            )
            response["Content-Disposition"] = "attachment; filename=data.zip"
            response["Content-Length"] = str(os.path.getsize(zipfilename))
            return response
        else:
            return super(StationListView, self).get(request, *args, **kwargs)

    def get_queryset(self, **kwargs):
        result = super(StationListView, self).get_queryset(**kwargs)

        # Sort results
        self.get_sort_order()
        self.request.session["sort"] = self.sort_order
        result = result.order_by(*self.sort_order)

        return result

    def get_context_data(self, **kwargs):
        context = super(StationListView, self).get_context_data(**kwargs)
        context["sort"] = self.sort_order
        return context


class BoundingBoxView(StationListBaseView):
    def get(self, request, *args, **kwargs):
        # Determine queryset's extent
        queryset = self.get_queryset(distinct=False)
        try:
            extent = list(queryset.aggregate(Extent("point")))["point__extent"]
        except TypeError:
            # Type error is raised if queryset is empty, or if all the
            # stations it contains are with unspecified co-ordinates.
            extent = settings.ENHYDRIS_MAP_DEFAULT_VIEWPORT

        # Increase extent if it's too small
        min_viewport = settings.ENHYDRIS_MIN_VIEWPORT_IN_DEGS
        if abs(extent[2] - extent[0]) < min_viewport:
            extent[2] += 0.5 * min_viewport
            extent[0] -= 0.5 * min_viewport
        if abs(extent[3] - extent[1]) < min_viewport:
            extent[3] += 0.5 * min_viewport
            extent[1] -= 0.5 * min_viewport

        return HttpResponse(
            ",".join([str(e) for e in extent]), content_type="text/plain"
        )


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
def download_gentityfile(request, gf_id):
    """
    This function handles requests for gentityfile downloads and serves the
    content to the user.
    """

    gfile = get_object_or_404(GentityFile, pk=int(gf_id))
    try:
        filename = gfile.content.file.name
        wrapper = FileWrapper(open(filename, "rb"))
    except IOError:
        raise Http404
    download_name = gfile.content.name.split("/")[-1]
    content_type = mimetypes.guess_type(filename)[0]
    response = HttpResponse(content_type=content_type)
    response["Content-Length"] = os.path.getsize(filename)
    response["Content-Disposition"] = "attachment; filename=%s" % download_name

    for chunk in wrapper:
        response.write(chunk)

    return response


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
