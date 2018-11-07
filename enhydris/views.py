import mimetypes
import os
from tempfile import mkstemp
from wsgiref.util import FileWrapper

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.views import login as auth_login
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db.models import Extent
from django.contrib.gis.geos import Polygon
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Count, Q
from django.db.utils import InternalError
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, render
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.utils.decorators import method_decorator
from django.utils.functional import lazy
from django.utils.translation import ugettext_lazy as _

import iso8601
import pandas as pd
import pd2hts

from .csv import prepare_csv
from .models import (
    GentityAltCode,
    GentityEvent,
    GentityFile,
    GentityGenericData,
    Instrument,
    Overseer,
    Station,
    Timeseries,
    UserProfile,
)
from .forms import (
    GentityAltCodeForm,
    GentityEventForm,
    GentityFileForm,
    GentityGenericDataForm,
    InstrumentForm,
    OverseerForm,
    StationForm,
    TimeseriesForm,
    TimeseriesDataForm,
    TimeStepForm,
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


class StationDetailView(DetailView):

    model = Station
    template_name = "station_detail.html"

    def get_context_data(self, **kwargs):
        context = super(StationDetailView, self).get_context_data(**kwargs)
        anonymous_can_download_data = (
            settings.ENHYDRIS_TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS
        )
        display_copyright = settings.ENHYDRIS_DISPLAY_COPYRIGHT_INFO
        context.update(
            {
                "owner": self.object.owner,
                "enabled_user_content": settings.ENHYDRIS_USERS_CAN_ADD_CONTENT,
                "anonymous_can_download_data": anonymous_can_download_data,
                "display_copyright": display_copyright,
                "wgs84_name": settings.ENHYDRIS_WGS84_NAME,
            }
        )
        return context


class StationBriefView(DetailView):
    model = Station
    template_name = "station_brief.html"


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


"""
Model management views.
"""


def _station_edit_or_create(request, station_id=None):
    """
    This function updates existing stations and creates new ones.
    """
    user = request.user
    if station_id:
        # User is editing a station
        station = get_object_or_404(Station, id=station_id)
        if not user.has_perm("enhydris.change_station", station):
            return HttpResponseForbidden("Forbidden", content_type="text/plain")
    else:
        # User is creating a new station
        station = None
        if not user.has_perm("enhydris.add_station"):
            return HttpResponseForbidden("Forbidden", content_type="text/plain")

    if request.method == "POST":
        if station:
            form = StationForm(request.POST, instance=station)
        else:
            form = StationForm(request.POST)

        if form.is_valid():
            try:
                # Try/Except to cacth Invalid SRID
                with transaction.atomic():
                    # http://stackoverflow.com/questions/20130507/
                    # django-transactionmanagementerror-when-using-signals
                    station = form.save()
                    if settings.ENHYDRIS_USERS_CAN_ADD_CONTENT:
                        # Make creating user the station creator
                        if not station_id:
                            station.creator = request.user
                    station.save()
                    # Save maintainers, many2many, then save again to
                    # set correctly row permissions
                    form.save_m2m()
                    station.save()
                    if not station_id:
                        station_id = str(station.id)
                    return HttpResponseRedirect(
                        reverse("station_detail", kwargs={"pk": station_id})
                    )
            except InternalError as e:
                if "Cannot find SRID" not in str(e):
                    raise
                form.add_error("srid", _("Invalid SRID"))

    else:
        if station:
            form = StationForm(
                instance=station,
                initial={
                    "abscissa": station.original_abscissa,
                    "ordinate": station.original_ordinate,
                },
            )
        else:
            form = StationForm()

    return render(request, "station_edit.html", {"form": form})


@login_required
def station_edit(request, station_id):
    """
    Edit station details.

    Permissions for editing stations are handled by row level permissions
    """
    return _station_edit_or_create(request, station_id)


@permission_required("enhydris.add_station")
def station_add(request):
    """
    Create a new station.

    Permissions for creating stations are handled by django.contrib.auth.
    """
    return _station_edit_or_create(request)


@login_required
def station_delete(request, station_id):
    """
    Delete existing station.

    Permissions for deleting stations are handled by our custom permissions app
    and django.contrib.auth since a user may be allowed to delete a specific
    station but not all of them (specified with row level permissions) or in
    case he is an admin, manager, etc he must be able to delete all of them
    (handled by django.contrib.auth)
    """
    station = get_object_or_404(Station, id=station_id)

    # Check permissions
    if not request.user.has_perm("enhydris.delete_station", station):
        return HttpResponseForbidden("Forbidden", content_type="text/plain")

    # Proceed with the deletion if it's a POST request
    if request.method == "POST":
        station.delete()
        return render(request, "success.html", {"msg": "Station deleted successfully"})

    # Ask for confirmation if it's a GET request
    if request.method == "GET":
        return render(
            request,
            "delete_confirm.html",
            {"object_description": _("station {}").format(station.id)},
        )

    return HttpResponseBadRequest("Bad request", content_type="text/plain")


"""
Timeseries views
"""


def _timeseries_edit_or_create(request, tseries_id=None):
    station_id = request.GET.get("station_id", None)
    station = None
    instrument_id = request.GET.get("instrument_id", None)
    instrument = None
    if tseries_id:
        # Edit
        tseries = get_object_or_404(Timeseries, id=tseries_id)
    else:
        # Add
        tseries = None
    if tseries:
        station = tseries.related_station
        station_id = station.id
        if tseries.instrument:
            instrument = tseries.instrument
    if instrument_id and not tseries:
        instrument = get_object_or_404(Instrument, id=instrument_id)
        station_id = instrument.station.id
    if station_id and not tseries:
        station = get_object_or_404(Station, id=station_id)
    if station:
        if not request.user.has_perm("enhydris.change_station", station):
            return HttpResponseForbidden("Forbidden", content_type="text/plain")
    if station and not tseries:
        tseries = Timeseries(gentity=station, instrument=instrument)

    user = request.user
    # Done with checks
    if request.method == "POST":
        if tseries and tseries.id:
            form = TimeseriesDataForm(
                request.POST,
                request.FILES,
                instance=tseries,
                user=user,
                gentity_id=station_id,
                instrument_id=instrument_id,
            )
        else:
            form = TimeseriesForm(
                request.POST,
                request.FILES,
                user=user,
                gentity_id=station_id,
                instrument_id=instrument_id,
            )
        if form.is_valid():
            tseries = form.save()
            # do stuff
            tseries.save()
            if not tseries_id:
                tseries_id = str(tseries.id)
            return HttpResponseRedirect(
                reverse("timeseries_detail", kwargs={"pk": tseries_id})
            )
    else:
        if tseries and tseries.id:
            form = TimeseriesDataForm(
                instance=tseries,
                user=user,
                gentity_id=station_id,
                instrument_id=instrument_id,
            )
        else:
            form = TimeseriesForm(
                instance=tseries,
                user=user,
                gentity_id=station_id,
                instrument_id=instrument_id,
            )

    return render(request, "timeseries_edit.html", {"form": form})


@permission_required("enhydris.add_timeseries")
def timeseries_add(request):
    """
    Create new timeseries. Timeseries can only be added as part of an existing
    station.
    """
    return _timeseries_edit_or_create(request)


@login_required
def timeseries_edit(request, timeseries_id):
    """
    Edit existing timeseries. Permissions are checked against the relative
    station that the timeseries is part of.
    """
    return _timeseries_edit_or_create(request, tseries_id=timeseries_id)


def timeseries_delete(request, timeseries_id):
    """
    Delete existing timeseries. Permissions are checked against the relative
    station that the timeseries is part of.
    """
    tseries = get_object_or_404(Timeseries, id=timeseries_id)
    related_station = tseries.related_station

    # Check permissions
    if not tseries or not request.user.has_perm("enhydris.delete_timeseries", tseries):
        return HttpResponseForbidden("Forbidden", content_type="text/plain")

    # Proceed with the deletion if it's a POST request
    if request.method == "POST":
        tseries.delete()
        return render(
            request, "success.html", {"msg": "Timeseries deleted successfully"}
        )

    # Ask for confirmation if it's a GET request
    if request.method == "GET":
        return render(
            request,
            "delete_confirm.html",
            {"object_description": _("timeseries {}").format(tseries.id)},
        )

    return HttpResponseBadRequest("Bad request", content_type="text/plain")


"""
GentityFile/GenericData/Event Views
"""


def _gentityfile_edit_or_create(request, gfile_id=None):
    station_id = request.GET.get("station_id", None)
    if gfile_id:
        # Edit
        gfile = get_object_or_404(GentityFile, id=gfile_id)
    else:
        # Add
        gfile = None

    if gfile_id:
        station = gfile.related_station
        station_id = station.id
        if not request.user.is_superuser:
            return HttpResponseForbidden("Forbidden", content_type="text/plain")

    if station_id and not gfile_id:
        # Adding new
        station = get_object_or_404(Station, id=station_id)
        if not request.user.is_superuser:
            return HttpResponseForbidden("Forbidden", content_type="text/plain")

    user = request.user
    # Done with checks
    if request.method == "POST":
        if gfile:
            form = GentityFileForm(
                request.POST, request.FILES, instance=gfile, user=user
            )
        else:
            form = GentityFileForm(request.POST, request.FILES, user=user)
        if form.is_valid():
            gfile = form.save()
            # do stuff
            gfile.save()
            if not gfile_id:
                gfile_id = str(gfile.id)
            return HttpResponseRedirect(
                reverse("station_detail", kwargs={"pk": str(gfile.gentity.id)})
            )
    else:
        if gfile:
            form = GentityFileForm(instance=gfile, user=user, gentity_id=station_id)
        else:
            form = GentityFileForm(user=user, gentity_id=station_id)

    return render(request, "gentityfile_edit.html", {"form": form})


@permission_required("enhydris.add_gentityfile")
def gentityfile_add(request):
    """
    Create new gentityfile. GentityFile can only be added as part of an
    existing station.
    """
    return _gentityfile_edit_or_create(request)


@login_required
def gentityfile_edit(request, gentityfile_id):
    """
    Edit existing gentityfile. Permissions are checked against the relative
    station that the gentityfile is part of.
    """
    return _gentityfile_edit_or_create(request, gfile_id=gentityfile_id)


@login_required
def gentityfile_delete(request, gentityfile_id):
    """
    Delete existing gentityfile. Permissions are checked against the relative
    station that the gentityfile is part of.
    """
    gfile = get_object_or_404(GentityFile, id=gentityfile_id)
    related_station = gfile.related_station

    # Check permissions
    if not gfile or not related_station or not request.user.is_superuser:
        return HttpResponseForbidden("Forbidden", content_type="text/plain")

    # Proceed with the deletion if it's a POST request
    if request.method == "POST":
        gfile.delete()
        return render(
            request, "success.html", {"msg": "GentityFile deleted successfully"}
        )

    # Ask for confirmation if it's a GET request
    if request.method == "GET":
        return render(
            request,
            "delete_confirm.html",
            {"object_description": _("file {}").format(gfile.id)},
        )

    return HttpResponseBadRequest("Bad request", content_type="text/plain")


"""
GentityGenericData View
"""


def _gentitygenericdata_edit_or_create(request, ggenericdata_id=None):
    station_id = request.GET.get("station_id", None)
    if ggenericdata_id:
        # Edit
        ggenericdata = get_object_or_404(GentityGenericData, id=ggenericdata_id)
    else:
        # Add
        ggenericdata = None

    if ggenericdata_id:
        station = ggenericdata.related_station
        station_id = station.id
        if not request.user.is_superuser:
            return HttpResponseForbidden("Forbidden", content_type="text/plain")

    if station_id and not ggenericdata_id:
        # Adding new
        station = get_object_or_404(Station, id=station_id)
        if not request.user.is_superuser:
            return HttpResponseForbidden("Forbidden", content_type="text/plain")

    user = request.user
    # Done with checks
    if request.method == "POST":
        if ggenericdata:
            form = GentityGenericDataForm(
                request.POST, request.FILES, instance=ggenericdata, user=user
            )
        else:
            form = GentityGenericDataForm(request.POST, request.FILES, user=user)
        if form.is_valid():
            ggenericdata = form.save()
            # do stuff
            ggenericdata.save()
            if not ggenericdata_id:
                ggenericdata_id = str(ggenericdata.id)
            return HttpResponseRedirect(
                reverse(
                    "station_detail", kwargs={"object_id": str(ggenericdata.gentity.id)}
                )
            )
    else:
        if ggenericdata:
            form = GentityGenericDataForm(
                instance=ggenericdata, user=user, gentity_id=station_id
            )
        else:
            form = GentityGenericDataForm(user=user, gentity_id=station_id)

    return render(request, "gentitygenericdata_edit.html", {"form": form})


@permission_required("enhydris.add_gentityfile")
def gentitygenericdata_add(request):
    """
    Create new gentitygenericdata. GentityGenericData can only be added as part
    of an existing station.
    """
    return _gentitygenericdata_edit_or_create(request)


@login_required
def gentitygenericdata_edit(request, ggenericdata_id):
    """
    Edit existing gentitygenericdata. Permissions are checked against the
    relative station that the gentitygenericdata is part of.
    """
    return _gentitygenericdata_edit_or_create(request, ggenericdata_id=ggenericdata_id)


@login_required
def gentitygenericdata_delete(request, ggenericdata_id):
    """
    Delete existing gentitygenericdata. Permissions are checked against the
    relative station that the gentitygenericdata is part of.
    """
    ggenericdata = get_object_or_404(GentityGenericData, id=ggenericdata_id)
    related_station = ggenericdata.related_station

    # Check permissions
    if not ggenericdata or not related_station or not request.user.is_superuser:
        return HttpResponseForbidden("Forbidden", content_type="text/plain")

    # Proceed with the deletion if it's a POST request
    if request.method == "POST":
        ggenericdata.delete()
        return render(
            request, "success.html", {"msg": "GentityGenericData deleted successfully"}
        )

    # Ask for confirmation if it's a GET request
    if request.method == "GET":
        return render(
            request,
            "delete_confirm.html",
            {"object_description": _("generic data {}").format(ggenericdata.id)},
        )

    return HttpResponseBadRequest("Bad request", content_type="text/plain")


"""
GentityEvent View
"""


def _gentityevent_edit_or_create(request, gevent_id=None):
    station_id = request.GET.get("station_id", None)
    if gevent_id:
        # Edit
        gevent = get_object_or_404(GentityEvent, id=gevent_id)
    else:
        # Add
        gevent = None

    if gevent_id:
        station = gevent.related_station
        station_id = station.id
        if not request.user.is_superuser:
            return HttpResponseForbidden("Forbidden", content_type="text/plain")

    if station_id and not gevent_id:
        # Adding new
        station = get_object_or_404(Station, id=station_id)
        if not request.user.is_superuser:
            return HttpResponseForbidden("Forbidden", content_type="text/plain")
        gevent = GentityEvent(gentity=station)

    user = request.user
    # Done with checks
    if request.method == "POST":
        if gevent:
            form = GentityEventForm(
                request.POST, request.FILES, instance=gevent, user=user
            )
        else:
            form = GentityEventForm(request.POST, request.FILES, user=user)
        if form.is_valid():
            gevent = form.save()
            # do stuff
            gevent.save()
            if not gevent_id:
                gevent_id = str(gevent.id)

            return HttpResponseRedirect(
                reverse("station_detail", kwargs={"pk": str(gevent.gentity.id)})
            )
    else:
        if gevent:
            form = GentityEventForm(instance=gevent, user=user, gentity_id=station_id)
        else:
            form = GentityEventForm(user=user, gentity_id=station_id)

    return render(request, "gentityevent_edit.html", {"form": form})


@permission_required("enhydris.add_gentityevent")
def gentityevent_add(request):
    """
    Create new gentityevent. GentityEvent can only be added as part of an
    existing station.
    """
    return _gentityevent_edit_or_create(request)


@login_required
def gentityevent_edit(request, gentityevent_id):
    """
    Edit existing gentityevent. Permissions are checked against the relative
    station that the gentityevent is part of.
    """
    return _gentityevent_edit_or_create(request, gevent_id=gentityevent_id)


@login_required
def gentityevent_delete(request, gentityevent_id):
    """
    Delete existing gentityevent. Permissions are checked against the relative
    station that the gentityevent is part of.
    """
    gevent = get_object_or_404(GentityEvent, id=gentityevent_id)
    related_station = gevent.related_station

    # Check permissions
    if not gevent or not related_station or not request.user.is_superuser:
        return HttpResponseForbidden("Forbidden", content_type="text/plain")

    # Proceed with the deletion if it's a POST request
    if request.method == "POST":
        gevent.delete()
        return render(
            request, "success.html", {"msg": "GentityEvent deleted successfully"}
        )

    # Ask for confirmation if it's a GET request
    if request.method == "GET":
        return render(
            request,
            "delete_confirm.html",
            {"object_description": _("event {}").format(gevent.id)},
        )

    return HttpResponseBadRequest("Bad request", content_type="text/plain")


def _gentityaltcode_edit_or_create(request, galtcode_id=None):
    station_id = request.GET.get("station_id", None)
    if galtcode_id:
        # Edit
        galtcode = get_object_or_404(GentityAltCode, id=galtcode_id)
    else:
        # Add
        galtcode = None

    if galtcode_id:
        station = galtcode.related_station
        station_id = station.id
        if not request.user.is_superuser:
            return HttpResponseForbidden("Forbidden", content_type="text/plain")

    if station_id and not galtcode_id:
        # Adding new
        station = get_object_or_404(Station, id=station_id)
        if not request.user.is_superuser:
            return HttpResponseForbidden("Forbidden", content_type="text/plain")

    user = request.user
    # Done with checks
    if request.method == "POST":
        if galtcode:
            form = GentityAltCodeForm(
                request.POST, request.FILES, instance=galtcode, user=user
            )
        else:
            form = GentityAltCodeForm(request.POST, request.FILES, user=user)
        if form.is_valid():
            galtcode = form.save()
            # do stuff
            galtcode.save()
            if not galtcode_id:
                galtcode_id = str(galtcode.id)
            return HttpResponseRedirect(
                reverse(
                    "station_detail", kwargs={"object_id": str(galtcode.gentity.id)}
                )
            )
    else:
        if galtcode:
            form = GentityAltCodeForm(
                instance=galtcode, user=user, gentity_id=station_id
            )
        else:
            form = GentityAltCodeForm(user=user, gentity_id=station_id)

    return render(request, "gentityaltcode_edit.html", {"form": form})


@permission_required("enhydris.add_gentityaltcode")
def gentityaltcode_add(request):
    """
    Create new gentityaltcode. GentityAltCode can only be added as part of an
    existing station.
    """
    return _gentityaltcode_edit_or_create(request)


@login_required
def gentityaltcode_edit(request, gentityaltcode_id):
    """
    Edit existing gentityaltcode. Permissions are checked against the relative
    station that the gentityaltcode is part of.
    """
    return _gentityaltcode_edit_or_create(request, galtcode_id=gentityaltcode_id)


@login_required
def gentityaltcode_delete(request, gentityaltcode_id):
    """
    Delete existing gentityaltcode. Permissions are checked against the
    relative station that the gentityaltcode is part of.
    """
    galtcode = get_object_or_404(GentityAltCode, id=gentityaltcode_id)
    related_station = galtcode.related_station

    # Check permissions
    if not galtcode or not related_station or not request.user.is_superuser:
        return HttpResponseForbidden("Forbidden", content_type="text/plain")

    # Proceed with the deletion if it's a POST request
    if request.method == "POST":
        galtcode.delete()
        return render(
            request, "success.html", {"msg": "GentityAltCode deleted successfully"}
        )

    # Ask for confirmation if it's a GET request
    if request.method == "GET":
        return render(
            request,
            "delete_confirm.html",
            {"object_description": _("code {}").format(galtcode.id)},
        )

    return HttpResponseBadRequest("Bad request", content_type="text/plain")


"""
Overseer Views
"""


def _overseer_edit_or_create(request, overseer_id=None, station_id=None):
    station_id = request.GET.get("station_id", None)
    if overseer_id:
        # Edit
        overseer = get_object_or_404(Overseer, id=overseer_id)
    else:
        # Add
        overseer = None

    if overseer_id:
        station = overseer.station
        station_id = station.id
        if not request.user.is_superuser:
            return HttpResponseForbidden("Forbidden", content_type="text/plain")

    if station_id and not overseer_id:
        # Adding new
        station = get_object_or_404(Station, id=station_id)
        if not request.user.is_superuser:
            return HttpResponseForbidden("Forbidden", content_type="text/plain")
        overseer = Overseer(station=station)

    user = request.user
    # Done with checks
    if request.method == "POST":
        if overseer:
            form = OverseerForm(
                request.POST, request.FILES, instance=overseer, user=user
            )
        else:
            form = OverseerForm(request.POST, request.FILES, user=user)
        if form.is_valid():
            overseer = form.save()
            # do stuff
            overseer.save()
            if not overseer_id:
                overseer_id = str(overseer.id)
            return HttpResponseRedirect(
                reverse(
                    "station_detail", kwargs={"object_id": str(overseer.station.id)}
                )
            )
    else:
        if overseer:
            form = OverseerForm(instance=overseer, user=user, gentity_id=station_id)
        else:
            form = OverseerForm(user=user, gentity_id=station_id)

    return render(request, "overseer_edit.html", {"form": form})


@permission_required("enhydris.add_overseer")
def overseer_add(request):
    """
    Create new overseer. Overseer can only be added as part of an existing
    station.
    """
    return _overseer_edit_or_create(request)


@login_required
def overseer_edit(request, overseer_id):
    """
    Edit existing overseer. Permissions are checked against the relative
    station that the overseer is part of.
    """
    return _overseer_edit_or_create(request, overseer_id=overseer_id)


@login_required
def overseer_delete(request, overseer_id):
    """
    Delete existing overseer. Permissions are checked against the relative
    station that the overseer is part of.
    """
    overseer = get_object_or_404(Overseer, id=overseer_id)
    related_station = overseer.station

    # Check permissions
    if not overseer or not related_station or not request.user.is_superuser:
        return HttpResponseForbidden("Forbidden", content_type="text/plain")

    # Proceed with the deletion if it's a POST request
    if request.method == "POST":
        overseer.delete()
        return render(request, "success.html", {"msg": "Overseer deleted successfully"})

    # Ask for confirmation if it's a GET request
    if request.method == "GET":
        return render(
            request,
            "delete_confirm.html",
            {"object_description": _("overseer {}").format(overseer.id)},
        )

    return HttpResponseBadRequest("Bad request", content_type="text/plain")


"""
Instument views
"""


def _instrument_edit_or_create(request, instrument_id=None):
    station_id = request.GET.get("station_id", None)
    if instrument_id:
        # Edit
        instrument = get_object_or_404(Instrument, id=instrument_id)
    else:
        # Add
        instrument = None

    if instrument_id:
        station = instrument.station
        station_id = station.id
        if not request.user.has_perm("enhydris.change_instrument", instrument):
            return HttpResponseForbidden("Forbidden", content_type="text/plain")

    if station_id and not instrument_id:
        station = get_object_or_404(Station, id=station_id)
        if not request.user.has_perm("enhydris.change_station", station):
            return HttpResponseForbidden("Forbidden", content_type="text/plain")
        instrument = Instrument(station=station)

    user = request.user
    # Done with checks
    if request.method == "POST":
        if instrument:
            form = InstrumentForm(request.POST, instance=instrument, user=user)
        else:
            form = InstrumentForm(request.POST, user=user)
        if form.is_valid():
            instrument = form.save()
            # do stuff
            instrument.save()
            if not instrument_id:
                instrument_id = str(instrument.id)
            return HttpResponseRedirect(
                reverse("instrument_detail", kwargs={"pk": instrument_id})
            )
    else:
        if instrument:
            form = InstrumentForm(instance=instrument, user=user, gentity_id=station_id)
        else:
            form = InstrumentForm(user=user, gentity_id=station_id)

    return render(request, "instrument_edit.html", {"form": form})


@permission_required("enhydris.add_instrument")
def instrument_add(request):
    """
    Create new instrument. Timeseries can only be added as part of an existing
    station.
    """
    return _instrument_edit_or_create(request)


@login_required
def instrument_edit(request, instrument_id):
    """
    Edit existing instrument. Permissions are checked against the relative
    station that the instrument is part of.
    """
    return _instrument_edit_or_create(request, instrument_id=instrument_id)


def instrument_delete(request, instrument_id):
    """
    Delete existing instrument. Permissions are checked against the relative
    station that the instrument is part of.
    """
    instrument = get_object_or_404(Instrument, id=instrument_id)

    if not request.user.has_perm("enhydris.delete_instrument", instrument):
        return HttpResponseForbidden("Forbidden", content_type="text/plain")

    # Proceed with the deletion if it's a POST request
    if request.method == "POST":
        instrument.delete()
        return render(
            request, "success.html", {"msg": "Instrument deleted successfully"}
        )

    # Ask for confirmation if it's a GET request
    if request.method == "GET":
        return render(
            request,
            "delete_confirm.html",
            {"object_description": _("instrument {}").format(instrument.id)},
        )

    return HttpResponseBadRequest("Bad request", content_type="text/plain")


"""
Generic model creation
"""

ALLOWED_TO_EDIT = (
    "waterbasin",
    "waterdivision",
    "person",
    "organization",
    "stationtype",
    "variable",
    "timezone",
    "politicaldivision",
    "instrumenttype",
    "unitofmeasurement",
    "filetype",
    "eventtype",
    "gentityaltcodetype",
    "timestep",
    "gentityaltcode",
    "gentityfile",
    "gentityevent",
    "gentitygenericdatatype",
)


class ModelAddView(CreateView):

    template_name = "model_add.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        # Verify url parms correctness
        popup = self.request.GET.get("_popup", False)
        if (
            not popup
            and self.request.method == "GET"
            and "_complete" not in self.request.GET
        ):
            raise Http404

        # Determine self.model and self.fields
        try:
            self.model = ContentType.objects.get(
                model=kwargs["model_name"], app_label="enhydris"
            ).model_class()
        except (ContentType.DoesNotExist, ContentType.MultipleObjectsReturned):
            raise Http404
        self.fields = [f.name for f in self.model._meta.fields if f.editable]

        # Check permissions
        if not kwargs[
            "model_name"
        ] in ALLOWED_TO_EDIT or not self.request.user.has_perm(
            "enhydris.add_" + kwargs["model_name"]
        ):
            return HttpResponseForbidden("Forbidden", content_type="text/plain")

        return super(ModelAddView, self).dispatch(*args, **kwargs)

    def get_form_class(self):
        return (
            TimeStepForm
            if self.model.__name__ == "TimeStep"
            else super(ModelAddView, self).get_form_class()
        )

    def get_extra_context(self):
        context = super(ModelAddView, self).get_extra_context()
        context["form_prefix"] = self.model.__name__
        return context
