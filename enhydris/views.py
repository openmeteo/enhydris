import mimetypes
import os
from tempfile import mkstemp
from wsgiref.util import FileWrapper

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login as auth_login
from django.contrib.gis.db.models import Extent
from django.contrib.gis.geos import Polygon
from django.core.urlresolvers import reverse
from django.db.models import Count, Q
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, ListView, UpdateView
from django.utils.functional import lazy

import iso8601
import pandas as pd
import pd2hts

from .csv import prepare_csv
from .models import (
    GentityFile, GentityGenericData, Instrument, Station, Timeseries, UserProfile,
)


class ProfileDetailView(DetailView):
    model = UserProfile
    template_name = "profile_detail.html"
    slug_field = "user__username"

    def get_object(self, queryset=None):
        if self.kwargs.get("slug", None):
            return super(ProfileDetailView, self).get_object(queryset)
        if not self.request.user.is_authenticated():
            return None
        if queryset is None:
            queryset = self.get_queryset()
        return queryset.get(user=self.request.user)


class ProfileEditView(UpdateView):
    model = UserProfile
    template_name = "profile_edit.html"
    success_url = lazy(reverse, str)("current_user_profile")
    fields = ("user", "fname", "lname", "address", "organization", "email_is_public")

    def get_object(self, queryset=None):
        if not self.request.user.is_authenticated():
            return None
        if queryset is None:
            queryset = self.get_queryset()
        return queryset.get(user=self.request.user)


def login(request, *args, **kwargs):
    if request.user.is_authenticated():
        redir_url = request.GET.get("next", reverse("station_list"))
        messages.info(request, "You are already logged on; " "logout to log in again.")
        return HttpResponseRedirect(redir_url)
    else:
        return auth_login(request, *args, **kwargs)


class StationListBaseView(ListView):
    template_name = ""
    model = Station

    def get_paginate_by(self, queryset):
        return getattr(settings, "ENHYDRIS_STATIONS_PER_PAGE", 100)

    def get_queryset(self, distinct=True, **kwargs):
        result = super(StationListBaseView, self).get_queryset(**kwargs)

        # Apply SITE_STATION_FILTER
        if len(settings.ENHYDRIS_SITE_STATION_FILTER) > 0:
            result = result.filter(**settings.ENHYDRIS_SITE_STATION_FILTER)

        # If kml, only stations with location
        if self.template_name.endswith(".kml"):
            result = result.filter(point__isnull=False)

        # Perform the search specified by the user
        query_string = self.request.GET.get("q", "")
        for search_term in query_string.split():
            result = self.refine_queryset(result, search_term)

        # Perform search specified by query parameters
        for param in self.request.GET:
            result = self.specific_filter(
                result, param, self.request.GET[param], ignore_invalid=True
            )

        # By default, only return distinct rows. We provide a way to
        # override this by calling with distinct=False, because distinct()
        # is incompatible with some things (namely extent()).
        if distinct:
            result = result.distinct()

        return result

    def refine_queryset(self, queryset, search_term):
        """
        Return the queryset refined according to search_term.
        search_term can either be a word or a "name:value" string, such as
        political_division:greece.
        """
        if not (":" in search_term):
            result = self.general_filter(queryset, search_term)
        else:
            name, dummy, value = search_term.partition(":")
            result = self.specific_filter(queryset, name, value)
        return result

    def general_filter(self, queryset, search_term):
        """
        Return the queryset refined according to search_term.
        search_term is a simple word searched in various places.
        """
        return queryset.filter(
            Q(name__icontains=search_term)
            | Q(name_alt__icontains=search_term)
            | Q(short_name__icontains=search_term)
            | Q(short_name_alt__icontains=search_term)
            | Q(remarks__icontains=search_term)
            | Q(remarks_alt__icontains=search_term)
            | Q(water_basin__name__icontains=search_term)
            | Q(water_basin__name_alt__icontains=search_term)
            | Q(water_division__name__icontains=search_term)
            | Q(water_division__name_alt__icontains=search_term)
            | Q(political_division__name__icontains=search_term)
            | Q(political_division__name_alt__icontains=search_term)
            | Q(owner__organization__name__icontains=search_term)
            | Q(owner__person__first_name__icontains=search_term)
            | Q(owner__person__last_name__icontains=search_term)
            | Q(timeseries__remarks__icontains=search_term)
            | Q(timeseries__remarks_alt__icontains=search_term)
        )

    def specific_filter(self, queryset, name, value, ignore_invalid=False):
        """
        Return the queryset refined according to the specified name
        and value; e.g. name can be "political_division" and value can be
        "greece". Value can also be an integer, in which case it refers to the
        id.
        """
        method_name = "filter_by_" + name
        try:
            method = getattr(self, method_name)
        except AttributeError:
            if not ignore_invalid:
                # FIXME: This must be changed to empty result with error
                # message.
                raise Http404
            return queryset
        return method(queryset, value)

    def filter_by_owner(self, queryset, value):
        return queryset.filter(
            Q(owner__organization__name__icontains=value)
            | Q(owner__organization__name_alt__icontains=value)
            | Q(owner__person__first_name__icontains=value)
            | Q(owner__person__first_name_alt__icontains=value)
            | Q(owner__person__last_name_alt__icontains=value)
            | Q(owner__person__last_name__icontains=value)
        )

    def filter_by_type(self, queryset, value):
        return queryset.filter(
            Q(stype__descr__icontains=value) | Q(stype__descr_alt__icontains=value)
        )

    def filter_by_water_division(self, queryset, value):
        return queryset.filter(
            Q(water_division__name__icontains=value)
            | Q(water_division__name_alt__icontains=value)
        )

    def filter_by_water_basin(self, queryset, value):
        return queryset.filter(
            Q(water_basin__name__icontains=value)
            | Q(water_basin__name_alt__icontains=value)
        )

    def filter_by_variable(self, queryset, value):
        return queryset.filter(
            Q(timeseries__variable__descr__icontains=value)
            | Q(timeseries__variable__descr_alt__icontains=value)
        )

    def filter_by_bbox(self, queryset, value):
        try:
            minx, miny, maxx, maxy = [float(i) for i in value.split(",")]
        except ValueError:
            raise Http404  # FIXME: Return empty result plus error message
        geom = Polygon(
            ((minx, miny), (minx, maxy), (maxx, maxy), (maxx, miny), (minx, miny)),
            srid=4326,
        )
        return queryset.filter(point__contained=geom)

    def filter_by_gentityId(self, queryset, value):
        """
        Normally the user won't perform the advanced search "gentity_id:1334"
        (and if he wants to do it we should find a simpler way than for him
        to type all that); so this filter is useful primarily for the kml view,
        when the client requests a specific station in order to show on the
        map.
        """
        if not value:
            return queryset
        try:
            gentity_id = int(value)
        except ValueError:
            raise Http404  # FIXME: Return empty result plus error message
        return queryset.filter(pk=gentity_id)

    def filter_by_ts_only(self, queryset, value):
        return queryset.annotate(tsnum=Count("timeseries")).exclude(tsnum=0)

    def filter_by_ts_has_years(self, queryset, value):
        try:
            years = [int(y) for y in value.split(",")]
        except ValueError:
            raise Http404  # FIXME: Return empty result plus error message
        return queryset.extra(
            where=[
                " AND ".join(
                    [
                        "enhydris_station.gpoint_ptr_id IN "
                        "(SELECT t.gentity_id FROM enhydris_timeseries t "
                        "WHERE " + str(year) + " BETWEEN "
                        "EXTRACT(YEAR FROM t.start_date_utc) AND "
                        "EXTRACT(YEAR FROM t.end_date_utc))"
                        for year in years
                    ]
                )
            ]
        )

    def filter_by_political_division(self, queryset, value):
        return queryset.extra(
            where=[
                """
            enhydris_station.gpoint_ptr_id IN (
              SELECT id FROM enhydris_gentity WHERE political_division_id IN (
                WITH RECURSIVE mytable(garea_ptr_id) AS (
                    SELECT garea_ptr_id FROM enhydris_politicaldivision
                    WHERE garea_ptr_id IN (
                        SELECT id FROM enhydris_gentity
                        WHERE LOWER(name) LIKE LOWER('%%{}%%')
                        OR LOWER(name_alt) LIKE LOWER('%%{}%%'))
                  UNION ALL
                    SELECT pd.garea_ptr_id
                    FROM enhydris_politicaldivision pd, mytable
                    WHERE pd.parent_id=mytable.garea_ptr_id
                )
                SELECT g.id FROM enhydris_gentity g, mytable
                WHERE g.id=mytable.garea_ptr_id))
                                     """.format(
                    value, value
                )
            ]
        )

    filter_by_country = filter_by_political_division  # synonym

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


class TimeseriesDetailView(DetailView):

    model = Timeseries
    template_name = "timeseries_detail.html"

    def get_context_data(self, **kwargs):
        context = super(TimeseriesDetailView, self).get_context_data(**kwargs)
        context["related_station"] = self.object.related_station
        context["enabled_user_content"] = settings.ENHYDRIS_USERS_CAN_ADD_CONTENT
        context["display_copyright"] = settings.ENHYDRIS_DISPLAY_COPYRIGHT_INFO
        context[
            "anonymous_can_download_data"
        ] = settings.ENHYDRIS_TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS
        return context


class InstrumentDetailView(DetailView):

    model = Instrument
    template_name = "instrument_detail.html"

    def get_context_data(self, **kwargs):
        context = super(InstrumentDetailView, self).get_context_data(**kwargs)
        context["related_station"] = self.object.station
        context["enabled_user_content"] = settings.ENHYDRIS_USERS_CAN_ADD_CONTENT
        context["timeseries"] = Timeseries.objects.filter(instrument__id=self.object.id)
        return context


def map_view(request, *args, **kwargs):
    return render(request, "map_page.html")


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


TS_ERROR = (
    "There seems to be some problem with our internal infrastuctrure. "
    "The admins have been notified of this and will try to resolve "
    "the matter as soon as possible.  Please try again later."
)


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
    timeseries.set_extra_timeseries_properties(adataframe)
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
