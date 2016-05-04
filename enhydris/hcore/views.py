import calendar
import csv
from datetime import datetime, timedelta
import json
import linecache
import math
import mimetypes
import os
import tempfile
from tempfile import mkstemp
from zipfile import ZipFile, ZIP_DEFLATED

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.views import login as auth_login
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import Polygon
from django.core.servers.basehttp import FileWrapper
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Count, Q
from django.db.utils import InternalError
from django.http import (Http404, HttpResponse, HttpResponseForbidden,
                         HttpResponseRedirect)
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.utils.decorators import method_decorator
from django.utils.functional import lazy
from django.utils.translation import ugettext_lazy as _

import iso8601
from pthelma.timeseries import add_months_to_datetime

from enhydris.hcore.models import (
    GentityAltCode, GentityEvent, GentityFile, GentityGenericData, Instrument,
    Overseer, PoliticalDivision, Station, Timeseries, UserProfile)
from enhydris.hcore.decorators import (gentityfile_permission,
                                       timeseries_permission)
from enhydris.hcore.forms import (
    GentityAltCodeForm, GentityEventForm, GentityFileForm,
    GentityGenericDataForm, InstrumentForm, OverseerForm, StationForm,
    TimeseriesForm, TimeseriesDataForm, TimeStepForm)


class ProfileDetailView(DetailView):
    model = UserProfile
    template_name = 'profile_detail.html'
    slug_field = 'user__username'

    def get_object(self, queryset=None):
        if self.kwargs.get('slug', None):
            return super(ProfileDetailView, self).get_object(queryset)
        if not self.request.user.is_authenticated():
            return None
        if queryset is None:
            queryset = self.get_queryset()
        return queryset.get(user=self.request.user)


class ProfileEditView(UpdateView):
    model = UserProfile
    template_name = 'profile_edit.html'
    success_url = lazy(reverse, str)('current_user_profile')
    fields = ('user', 'fname', 'lname', 'address', 'organization',
              'email_is_public')

    def get_object(self, queryset=None):
        if not self.request.user.is_authenticated():
            return None
        if queryset is None:
            queryset = self.get_queryset()
        return queryset.get(user=self.request.user)


def login(request, *args, **kwargs):
    if request.user.is_authenticated():
        redir_url = request.GET.get('next', reverse('station_list'))
        messages.info(request, 'You are already logged on; '
                               'logout to log in again.')
        return HttpResponseRedirect(redir_url)
    else:
        return auth_login(request, *args, **kwargs)


class StationDetailView(DetailView):

    model = Station
    template_name = 'station_detail.html'

    def get_context_data(self, **kwargs):
        context = super(StationDetailView, self).get_context_data(**kwargs)
        anonymous_can_download_data = \
            settings.ENHYDRIS_TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS
        display_copyright = settings.ENHYDRIS_DISPLAY_COPYRIGHT_INFO
        context.update(
            {"owner": self.object.owner,
             "enabled_user_content": settings.ENHYDRIS_USERS_CAN_ADD_CONTENT,
             "anonymous_can_download_data": anonymous_can_download_data,
             "display_copyright": display_copyright,
             "wgs84_name": settings.ENHYDRIS_WGS84_NAME,
             })
        return context


class StationBriefView(DetailView):
    model = Station
    template_name = 'station_brief.html'


_station_list_csv_headers = [
    'id', 'Name', 'Alternative name', 'Short name',
    'Alt short name', 'Type', 'Owner', 'Start date', 'End date', 'Abscissa',
    'Ordinate', 'SRID', 'Approximate', 'Altitude', 'SRID', 'Water basin',
    'Water division', 'Political division', 'Automatic', 'Remarks',
    'Alternative remarks', 'Last modified']


def _station_csv(s):
    abscissa, ordinate = (s.point.transform(s.srid, clone=True)
                          if s.point else (None, None))
    return [unicode(x).encode('utf-8') for x in
            [s.id, s.name, s.name_alt, s.short_name, s.short_name_alt,
             '+'.join([t.descr for t in s.stype.all()]),
             s.owner, s.start_date, s.end_date,
             abscissa, ordinate, s.srid, s.approximate, s.altitude, s.asrid,
             s.water_basin.name if s.water_basin else "",
             s.water_division.name if s.water_division else "",
             s.political_division.name if s.political_division else "",
             s.is_automatic, s.remarks, s.remarks_alt, s.last_modified
             ]
            ]


_instrument_list_csv_headers = [
    'id', 'Station', 'Type', 'Name',
    'Alternative name', 'Manufacturer', 'Model', 'Start date', 'End date',
    'Remarks', 'Alternative remarks']


def _instrument_csv(i):
    return [unicode(x).encode('utf-8') for x in
            [i.id, i.station.id, i.type.descr if i.type else "", i.name,
             i.name_alt, i.manufacturer, i.model, i.start_date, i.end_date,
             i.remarks, i.remarks_alt
             ]
            ]


_timeseries_list_csv_headers = [
    'id', 'Station', 'Instrument', 'Variable',
    'Unit', 'Name', 'Alternative name', 'Precision', 'Time zone', 'Time step',
    'Nom. Offs. Min.', 'Nom. Offs. Mon.', 'Act. Offs. Min.',
    'Act. Offs.  Mon.', 'Remarks', 'Alternative Remarks']


def _timeseries_csv(t):
    return [unicode(x).encode('utf-8') for x in
            [t.id, t.gentity.id, t.instrument.id if t.instrument else "",
             t.variable.descr if t.variable else "",
             t.unit_of_measurement.symbol, t.name, t.name_alt, t.precision,
             t.time_zone.code, t.time_step.descr if t.time_step else "",
             t.timestamp_rounding_minutes, t.timestamp_rounding_months,
             t.timestamp_offset_minutes, t.timestamp_offset_months
             ]
            ]


def _prepare_csv(queryset):
    tempdir = tempfile.mkdtemp()
    zipfilename = os.path.join(tempdir, 'data.zip')
    zipfile = ZipFile(zipfilename, 'w', ZIP_DEFLATED)

    stationsfilename = os.path.join(tempdir, 'stations.csv')
    stationsfile = open(stationsfilename, 'w')
    try:
        stationsfile.write(b'\xef\xbb\xbf')  # BOM
        csvwriter = csv.writer(stationsfile)
        csvwriter.writerow(_station_list_csv_headers)
        for station in queryset:
            csvwriter.writerow(_station_csv(station))
    finally:
        stationsfile.close()
    zipfile.write(stationsfilename, 'stations.csv')

    instrumentsfilename = os.path.join(tempdir, 'instruments.csv')
    instrumentsfile = open(instrumentsfilename, 'w')
    try:
        instrumentsfile.write(b'\xef\xbb\xbf')  # BOM
        csvwriter = csv.writer(instrumentsfile)
        csvwriter.writerow(_instrument_list_csv_headers)
        for station in queryset:
            for instrument in station.instrument_set.all():
                csvwriter.writerow(_instrument_csv(instrument))
    finally:
        instrumentsfile.close()
    zipfile.write(instrumentsfilename, 'instruments.csv')

    timeseriesfilename = os.path.join(tempdir, 'timeseries.csv')
    timeseriesfile = open(timeseriesfilename, 'w')
    try:
        timeseriesfile.write(b'\xef\xbb\xbf')  # BOM
        csvwriter = csv.writer(timeseriesfile)
        csvwriter.writerow(_timeseries_list_csv_headers)
        for station in queryset:
            for timeseries in station.timeseries.order_by('instrument__id'):
                csvwriter.writerow(_timeseries_csv(timeseries))
    finally:
        timeseriesfile.close()
    zipfile.write(timeseriesfilename, 'timeseries.csv')

    import textwrap
    readmefilename = os.path.join(tempdir, 'README')
    readmefile = open(readmefilename, 'w')
    readmefile.write(textwrap.dedent("""\
        The functionality which provides you with CSV versions of the station,
        instrument and time series list is a quick way to enable HUMANS to
        examine these lists with tools such as spreadsheets. It is not
        intended to be used by any automation tools: headings, columns, file
        structure and everything is subject to change without notice.

        If you are a developer and need to write automation tools, do not rely
        on the CSV files. Instead, use the documented API
        (http://openmeteo.org/doc/api.html), or contact us (the Enhydris
        developers, not the web site maintainers) and insist that we support
        one of these open standards appropriate for such information
        interchange.
        """))
    readmefile.close()
    zipfile.write(readmefilename, 'README')

    zipfile.close()
    os.remove(stationsfilename)
    os.remove(instrumentsfilename)
    os.remove(timeseriesfilename)
    os.remove(readmefilename)

    return zipfilename


class StationListBaseView(ListView):
    template_name = ''
    model = Station

    def get_queryset(self, distinct=True, **kwargs):
        result = super(StationListBaseView, self).get_queryset(**kwargs)

        # Apply SITE_STATION_FILTER
        if len(settings.ENHYDRIS_SITE_STATION_FILTER) > 0:
            result = result.filter(**settings.ENHYDRIS_SITE_STATION_FILTER)

        # If kml, only stations with location
        if self.template_name.endswith('.kml'):
            result = result.filter(point__isnull=False)

        # Perform the search specified by the user
        query_string = self.request.GET.get('q', '')
        for search_term in query_string.split():
            result = self.refine_queryset(result, search_term)

        # Perform search specified by query parameters
        for param in self.request.GET:
            result = self.specific_filter(result,
                                          param,
                                          self.request.GET[param],
                                          ignore_invalid=True)

        # By default, only return distinct rows. We provide a way to
        # override this by calling with distinct=False, because distinct()
        # is incompatible with some things (namely extent()).
        if distinct:
            result = result.distinct()

        return result

    def refine_queryset(self, queryset, search_term):
        '''
        Return the queryset refined according to search_term.
        search_term can either be a word or a "name:value" string, such as
        political_division:greece.
        '''
        if not (':' in search_term):
            result = self.general_filter(queryset, search_term)
        else:
            name, dummy, value = search_term.partition(':')
            result = self.specific_filter(queryset, name, value)
        return result

    def general_filter(self, queryset, search_term):
        '''
        Return the queryset refined according to search_term.
        search_term is a simple word searched in various places.
        '''
        return queryset.filter(
            Q(name__icontains=search_term) |
            Q(name_alt__icontains=search_term) |
            Q(short_name__icontains=search_term) |
            Q(short_name_alt__icontains=search_term) |
            Q(remarks__icontains=search_term) |
            Q(remarks_alt__icontains=search_term) |
            Q(water_basin__name__icontains=search_term) |
            Q(water_basin__name_alt__icontains=search_term) |
            Q(water_division__name__icontains=search_term) |
            Q(water_division__name_alt__icontains=search_term) |
            Q(political_division__name__icontains=search_term) |
            Q(political_division__name_alt__icontains=search_term) |
            Q(owner__organization__name__icontains=search_term) |
            Q(owner__person__first_name__icontains=search_term) |
            Q(owner__person__last_name__icontains=search_term) |
            Q(timeseries__remarks__icontains=search_term) |
            Q(timeseries__remarks_alt__icontains=search_term))

    def specific_filter(self, queryset, name, value, ignore_invalid=False):
        '''
        Return the queryset refined according to the specified name
        and value; e.g. name can be "political_division" and value can be
        "greece". Value can also be an integer, in which case it refers to the
        id.
        '''
        method_name = 'filter_by_' + name
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
            Q(owner__organization__name__icontains=value) |
            Q(owner__organization__name_alt__icontains=value) |
            Q(owner__person__first_name__icontains=value) |
            Q(owner__person__first_name_alt__icontains=value) |
            Q(owner__person__last_name_alt__icontains=value) |
            Q(owner__person__last_name__icontains=value))

    def filter_by_type(self, queryset, value):
        return queryset.filter(
            Q(stype__descr__icontains=value) |
            Q(stype__descr_alt__icontains=value))

    def filter_by_water_division(self, queryset, value):
        return queryset.filter(
            Q(water_division__name__icontains=value) |
            Q(water_division__name_alt__icontains=value))

    def filter_by_water_basin(self, queryset, value):
        return queryset.filter(
            Q(water_basin__name__icontains=value) |
            Q(water_basin__name_alt__icontains=value))

    def filter_by_variable(self, queryset, value):
        return queryset.filter(
            Q(timeseries__variable__descr__icontains=value) |
            Q(timeseries__variable__descr_alt__icontains=value))

    def filter_by_bbox(self, queryset, value):
        try:
            minx, miny, maxx, maxy = [float(i) for i in value.split(',')]
        except ValueError:
            raise Http404  # FIXME: Return empty result plus error message
        geom = Polygon(((minx, miny), (minx, maxy),
                        (maxx, maxy), (maxx, miny),
                        (minx, miny)), srid=4326)
        return queryset.filter(point__contained=geom)

    def filter_by_gentityId(self, queryset, value):
        '''
        Normally the user won't perform the advanced search "gentity_id:1334"
        (and if he wants to do it we should find a simpler way than for him
        to type all that); so this filter is useful primarily for the kml view,
        when the client requests a specific station in order to show on the
        map.
        '''
        if not value:
            return queryset
        try:
            gentity_id = int(value)
        except ValueError:
            raise Http404  # FIXME: Return empty result plus error message
        return queryset.filter(pk=gentity_id)

    def filter_by_ts_only(self, queryset, value):
        return queryset.annotate(tsnum=Count('timeseries')).exclude(tsnum=0)

    def filter_by_ts_has_years(self, queryset, value):
        try:
            years = [int(y) for y in value.split(',')]
        except ValueError:
            raise Http404  # FIXME: Return empty result plus error message
        return queryset.extra(
            where=['hcore_station.gpoint_ptr_id IN '
                   '(SELECT t.gentity_id FROM hcore_timeseries t '
                   'WHERE ' + (' AND '.join(
                       ['{0} BETWEEN '
                        'EXTRACT(YEAR FROM t.start_date) AND '
                        'EXTRACT(YEAR FROM t.end_date)'
                        .format(year) for year in years])) +
                   ')'])

    def filter_by_political_division(self, queryset, value):
        return queryset.extra(where=['''
            hcore_station.gpoint_ptr_id IN (
              SELECT id FROM hcore_gentity WHERE political_division_id IN (
                WITH RECURSIVE mytable(garea_ptr_id) AS (
                    SELECT garea_ptr_id FROM hcore_politicaldivision
                    WHERE garea_ptr_id IN (
                        SELECT id FROM hcore_gentity
                        WHERE LOWER(name) LIKE LOWER('%%{}%%')
                        OR LOWER(name_alt) LIKE LOWER('%%{}%%'))
                  UNION ALL
                    SELECT pd.garea_ptr_id
                    FROM hcore_politicaldivision pd, mytable
                    WHERE pd.parent_id=mytable.garea_ptr_id
                )
                SELECT g.id FROM hcore_gentity g, mytable
                WHERE g.id=mytable.garea_ptr_id))
                                     '''.format(value, value)])
    filter_by_country = filter_by_political_division  # synonym

    def get_context_data(self, **kwargs):
        context = super(StationListBaseView, self).get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['enabled_user_content'] = \
            settings.ENHYDRIS_USERS_CAN_ADD_CONTENT
        return context


class StationListView(StationListBaseView):
    template_name = 'station_list.html'

    def get_sort_order(self):
        """Get sort_order as a list: from the request parameters, otherwise
        from request.session, otherwise it's the default, ['name']. Removes
        duplicate column occurences from the list.
        """
        sort_order = self.request.GET.getlist('sort')

        # Ensure sort order term to match with Station model field names
        sort_order = [x for x in sort_order
                      if x in Station._meta.get_all_field_names()]

        if not sort_order:
            sort_order = self.request.session.get('sort', ['name'])

        sort_order = sort_order[:]
        for i in range(len(sort_order) - 1, -1, -1):
            s = sort_order[i]
            if s[0] == '-':
                s = s[1:]
            if (s in sort_order[:i]) or ('-' + s in sort_order[:i]):
                del sort_order[i]
        self.sort_order = sort_order

    def get(self, request, *args, **kwargs):
        # The CSV is an undocumented feature we quickly and dirtily created
        # for some people (Hydroexigiantiki) who needed it.
        if request.GET.get("format", "").lower() == "csv":
            zipfilename = _prepare_csv(self.get_queryset())
            response = HttpResponse(file(zipfilename, 'rb').read(),
                                    content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename=data.zip'
            response['Content-Length'] = str(os.path.getsize(zipfilename))
            return response
        else:
            return super(StationListView, self).get(
                request, *args, **kwargs)

    def get_queryset(self, **kwargs):
        result = super(StationListView, self).get_queryset(**kwargs)

        # Sort results
        self.get_sort_order()
        self.request.session['sort'] = self.sort_order
        result = result.order_by(*self.sort_order)

        return result

    def get_context_data(self, **kwargs):
        context = super(StationListView, self).get_context_data(**kwargs)
        context['sort'] = self.sort_order
        return context


class BoundingBoxView(StationListBaseView):

    def get(self, request, *args, **kwargs):
        # Determine queryset's extent
        queryset = self.get_queryset(distinct=False)
        try:
            extent = list(queryset.extent())
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

        return HttpResponse(','.join([str(e) for e in extent]),
                            content_type='text/plain')


def bufcount(filename):
    lines = 0
    with open(filename) as f:
        buf_size = 1024 * 1024
        read_f = f.read  # loop optimization
        buf = read_f(buf_size)
        while buf:
            lines += buf.count('\n')
            buf = read_f(buf_size)
    return lines


def timeseries_data(request, *args, **kwargs):

    def date_at_pos(pos, tz):
        s = linecache.getline(afilename, pos)
        return iso8601.parse_date(s.split(',')[0], default_timezone=tz)

    def timedeltadivide(a, b):
        """Divide timedelta a by timedelta b."""
        a = a.days * 86400 + a.seconds
        b = b.days * 86400 + b.seconds
        return float(a) / float(b)

    # Return the nearest record number to the specified date
    # The second argument is 0 for exact match, -1 if no
    # exact match and the date is after the record found,
    # 1 if no exact match and the date is before the record.
    def find_line_at_date(adatetime, totlines, tz):
        if totlines < 2:
            return totlines
        i1, i2 = 1, totlines
        d1 = date_at_pos(i1, tz)
        d2 = date_at_pos(i2, tz)
        if adatetime <= d1:
            return (i1, 0 if d1 == adatetime else 1)
        if adatetime >= d2:
            return (i2, 0 if d2 == adatetime else -1)
        while(True):
            i = i1 + int(round(float(i2 - i1) *
                               timedeltadivide(adatetime - d1, d2 - d1)))
            d = date_at_pos(i, tz)
            if d == adatetime:
                return (i, 0)
            if (i == i1) or (i == i2):
                return (i, -1 if i == i1 else 1)
            if d < adatetime:
                d1, i1 = d, i
            if d > adatetime:
                d2, i2 = d, i

    def add_to_stats(date, value):
        if not gstats['max']:
            gstats['max'] = value
            gstats['min'] = value
            gstats['sum'] = 0
            gstats['vsum'] = [0.0, 0.0]
            gstats['count'] = 0
            gstats['vectors'] = [0] * 8
        if value >= gstats['max']:
            gstats['max'] = value
            gstats['max_tstmp'] = date
        if value <= gstats['min']:
            gstats['min'] = value
            gstats['min_tstmp'] = date
        if is_vector:
            value2 = value
            if value2 >= 360:
                value2 -= 360
            if value2 < 0:
                value2 += 360
            if value2 < 0 or value2 > 360:
                return
            # reversed order of x, y since atan2 definition is
            # math.atan2(y, x)
            gstats['vsum'][1] += math.cos(value2 * math.pi / 180)
            gstats['vsum'][0] += math.sin(value2 * math.pi / 180)
            value2 = value2 + 22.5 if value2 < 337.5 else value2 - 337.5
            gstats['vectors'][int(value2 / 45)] += 1
        gstats['sum'] += value
        gstats['last'] = value
        gstats['last_tstmp'] = date
        gstats['count'] += 1

    def inc_datetime(adate, unit, steps):
        if unit == 'day':
            return adate + steps * timedelta(days=1)
        elif unit == 'week':
            return adate + steps * timedelta(weeks=1)
        elif unit == 'month':
            return add_months_to_datetime(adate, steps)
        elif unit == 'year':
            return add_months_to_datetime(adate, 12 * steps)
        elif unit == 'moment':
            return adate
        elif unit == 'hour':
            return adate + steps * timedelta(minutes=60)
        elif unit == 'twohour':
            return adate + steps * timedelta(minutes=120)
        else:
            raise Http404

    if (request.method != "GET") or ('object_id' not in request.GET):
        raise Http404

    response = HttpResponse(content_type='application/json')
    response.status_code = 200
    try:
        object_id = int(request.GET['object_id'])
    except ValueError:
        raise Http404
    timeseries = Timeseries.objects.get(pk=object_id)
    afilename = timeseries.datafile.path
    tz = timeseries.time_zone.as_tzinfo
    chart_data = []
    if 'start_pos' in request.GET and 'end_pos' in request.GET:
        start_pos = int(request.GET['start_pos'])
        end_pos = int(request.GET['end_pos'])
    else:
        end_pos = bufcount(afilename)
        tot_lines = end_pos
        if 'last' in request.GET:
            if request.GET.get('date', False):
                datetimestr = request.GET['date']
                datetimefmt = '%Y-%m-%d'
                if request.GET.get('time', False):
                    datetimestr = datetimestr + ' ' + request.GET['time']
                    datetimefmt = datetimefmt + ' %H:%M'
                try:
                    first_date = datetime.strptime(datetimestr, datetimefmt)
                    last_date = inc_datetime(first_date, request.GET['last'],
                                             1)
                    (end_pos, is_exact) = find_line_at_date(
                        last_date, tot_lines, tz)
                    if request.GET.get('exact_datetime', False) and (
                            is_exact != 0):
                        raise Http404
                except ValueError:
                    raise Http404
            else:
                last_date = date_at_pos(end_pos, tz)
                first_date = inc_datetime(last_date, request.GET['last'], -1)
                # This is an almost bad workarround to exclude the first
                # record from sums, i.e. when we need the 144 10 minute
                # values from a day.
                if 'start_offset' in request.GET:
                    offset = float(request.GET['start_offset'])
                    first_date += timedelta(minutes=offset)
            start_pos = find_line_at_date(first_date, tot_lines, tz)[0]
        else:
            start_pos = 1

    length = end_pos - start_pos + 1
    step = int(length / settings.ENHYDRIS_TS_GRAPH_BIG_STEP_DENOMINATOR) or 1
    fine_step = int(step / settings.ENHYDRIS_TS_GRAPH_FINE_STEP_DENOMINATOR
                    ) or 1
    if not step % fine_step == 0:
        step = fine_step * settings.ENHYDRIS_TS_GRAPH_FINE_STEP_DENOMINATOR
    pos = start_pos
    amax = ''
    prev_pos = -1
    tick_pos = -1
    is_vector = request.GET.get('vector', False)
    gstats = {'max': None, 'min': None, 'count': 0,
              'max_tstmp': None, 'min_tstmp': None,
              'sum': None, 'avg': None,
              'vsum': None, 'vavg': None,
              'last': None, 'last_tstmp': None,
              'vectors': None}
    afloat = 0.01
    try:
        linecache.checkcache(afilename)
        while pos < start_pos + length:
            s = linecache.getline(afilename, pos)
            if s.isspace():
                pos += fine_step
                continue
            t = s.split(',')
            # Use the following exception handling to catch incoplete
            # reads from cache. Tries only one time, next time if
            # the error on the same line persists, it raises.
            try:
                k = iso8601.parse_date(t[0], default_timezone=tz)
                v = t[1]
            except:
                if pos > prev_pos:
                    prev_pos = pos
                    linecache.checkcache(afilename)
                    continue
                else:
                    raise
            if v != '':
                afloat = float(v)
                add_to_stats(k, afloat)
                if amax == '':
                    amax = afloat
                else:
                    amax = afloat if afloat > amax else amax
            if (pos - start_pos) % step == 0:
                tick_pos = pos
                if amax == '':
                    amax = 'null'
                chart_data.append([calendar.timegm(k.timetuple()) * 1000,
                                  str(amax), pos])
                amax = ''
            # Sometimes linecache tries to read a file being written (from
            # timeseries.write_file). So every 5000 lines refresh the
            # cache.
            if (pos - start_pos) % 5000 == 0:
                linecache.checkcache(afilename)
            pos += fine_step
        if length > 0 and tick_pos < end_pos:
            if amax == '':
                amax = 'null'
            chart_data[-1] = [calendar.timegm(k.timetuple()) * 1000,
                              str(amax), end_pos]
    finally:
        linecache.clearcache()
    if chart_data:
        if gstats['count'] > 0:
            gstats['avg'] = gstats['sum'] / gstats['count']
            if is_vector:
                gstats['vavg'] = math.atan2(*gstats['vsum']
                                            ) * 180 / math.pi
                if gstats['vavg'] < 0:
                    gstats['vavg'] += 360
            for item in ('max_tstmp', 'min_tstmp', 'last_tstmp'):
                gstats[item] = calendar.timegm(gstats[item].timetuple()) * 1000
        response.content = json.dumps({'data': chart_data,
                                       'stats': gstats})
    else:
        response.content = json.dumps("")
    callback = request.GET.get("jsoncallback", None)
    if callback:
        response.content = '%s(%s)' % (callback, response.content,)
    return response


class TimeseriesDetailView(DetailView):

    model = Timeseries
    template_name = 'timeseries_detail.html'

    def get_context_data(self, **kwargs):
        context = super(TimeseriesDetailView, self).get_context_data(**kwargs)
        context['related_station'] = self.object.related_station
        context['enabled_user_content'] = \
            settings.ENHYDRIS_USERS_CAN_ADD_CONTENT
        context['display_copyright'] = settings.ENHYDRIS_DISPLAY_COPYRIGHT_INFO
        context['anonymous_can_download_data'] = \
            settings.ENHYDRIS_TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS
        return context


class InstrumentDetailView(DetailView):

    model = Instrument
    template_name = 'instrument_detail.html'

    def get_context_data(self, **kwargs):
        context = super(InstrumentDetailView, self).get_context_data(**kwargs)
        context['related_station'] = self.object.station
        context['enabled_user_content'] = \
            settings.ENHYDRIS_USERS_CAN_ADD_CONTENT
        context['timeseries'] = Timeseries.objects.filter(
            instrument__id=self.object.id)
        return context


def map_view(request, *args, **kwargs):
    return render_to_response('map_page.html',
                              context_instance=RequestContext(request))


def get_subdivision(request, division_id):
    """Ajax call to refresh divisions in filter table"""
    response = HttpResponse(content_type='application/json;charset=utf8')
    try:
        div = PoliticalDivision.objects.get(pk=division_id)
    except:
        response.write("[]")
        return response
    parent_divs = PoliticalDivision.objects.filter(
        Q(name=div.name) & Q(name_alt=div.name_alt) &
        Q(short_name=div.short_name) & Q(short_name_alt=div.short_name_alt))
    divisions = PoliticalDivision.objects.filter(
        parent__in=[p.id for p in parent_divs])
    response.write("[")
    added = []
    for num, div in enumerate(divisions):
        if div.name not in added:
            response.write(json.dumps({"name": div.name, "id": div.pk}))
            added.append(div.name)
            if num < divisions.count() - 1:
                response.write(',')
    response.write("]")
    return response


GF_ERROR = ("The file you requested is temporary unavailable. Please try again"
            " later.")


@gentityfile_permission
def download_gentityfile(request, gf_id):
    """
    This function handles requests for gentityfile downloads and serves the
    content to the user.
    """

    gfile = get_object_or_404(GentityFile, pk=int(gf_id))
    try:
        filename = gfile.content.file.name
        wrapper = FileWrapper(open(filename))
    except IOError:
        raise Http404
    download_name = gfile.content.name.split('/')[-1]
    content_type = mimetypes.guess_type(filename)[0]
    response = HttpResponse(content_type=content_type)
    response['Content-Length'] = os.path.getsize(filename)
    response['Content-Disposition'] = \
        "attachment; filename=%s" % download_name

    for chunk in wrapper:
        response.write(chunk)

    return response


@gentityfile_permission
def download_gentitygenericdata(request, gg_id):
    """
    This function handles requests for gentitygenericdata downloads and serves
    the content to the user.
    """
    ggenericdata = get_object_or_404(GentityGenericData, pk=int(gg_id))
    try:
        s = ggenericdata.content
        if s.find('\r') < 0:
            s = s.replace('\n', '\r\n')
        (afile_handle, afilename) = mkstemp()
        os.write(afile_handle, s)
        afile = open(afilename, 'r')
        wrapper = FileWrapper(afile)
    except:
        raise Http404
    download_name = 'GenericData-id_%s.%s' % (
        gg_id, ggenericdata.data_type.file_extension)
    content_type = 'text/plain'
    response = HttpResponse(content_type=content_type)
    response['Content-Length'] = os.fstat(afile_handle).st_size
    response['Content-Disposition'] = \
        "attachment; filename=%s" % download_name
    for chunk in wrapper:
        response.write(chunk)
    return response


TS_ERROR = ("There seems to be some problem with our internal infrastuctrure. "
            "The admins have been notified of this and will try to resolve "
            "the matter as soon as possible.  Please try again later.")


@timeseries_permission
def download_timeseries(request, object_id, start_date=None, end_date=None):
    timeseries = get_object_or_404(Timeseries, pk=int(object_id))
    tz = timeseries.time_zone.as_tzinfo
    start_date = (iso8601.parse_date(start_date, default_timezone=tz)
                  if start_date else None)
    end_date = (iso8601.parse_date(end_date, default_timezone=tz)
                if end_date else None)
    ts = timeseries.get_all_data()
    if start_date:
        ts.delete_items(None, start_date - timedelta(minutes=1))
    if end_date:
        ts.delete_items(end_date + timedelta(minutes=1), None)
    response = HttpResponse(
        content_type='text/vnd.openmeteo.timeseries; charset=utf-8')
    response['Content-Disposition'] = \
        "attachment; filename=%s.hts" % (object_id,)
    try:
        file_version = int(request.GET.get('version', '2'))
    except ValueError:
        raise Http404
    if file_version not in (2, 3):
        raise Http404
    ts.write_file(response, version=file_version)
    return response


@timeseries_permission
def timeseries_bottom(request, object_id):
    try:
        atimeseries = Timeseries.objects.get(pk=int(object_id))
    except Timeseries.DoesNotExist:
        raise Http404
    response = HttpResponse(content_type='text/plain; charset=utf-8')
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
        if not (user.has_row_perm(station, 'edit')
                and user.has_perm('hcore.change_station')):
            return HttpResponseForbidden('Forbidden',
                                         content_type='text/plain')
    else:
        # User is creating a new station
        station = None
        if not user.has_perm('hcore.add_station'):
            return HttpResponseForbidden('Forbidden',
                                         content_type='text/plain')

    if request.method == 'POST':
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
                                # Give perms to the creator
                                user.add_row_perm(station, 'edit')
                                user.add_row_perm(station, 'delete')
                    station.save()
                    # Save maintainers, many2many, then save again to
                    # set correctly row permissions
                    form.save_m2m()
                    station.save()
                    if not station_id:
                        station_id = str(station.id)
                    return HttpResponseRedirect(
                        reverse('station_detail', kwargs={'pk': station_id}))
            except InternalError as e:
                if 'Cannot find SRID' not in str(e):
                    raise
                form.add_error('srid', _("Invalid SRID"))

    else:
        if station:
            form = StationForm(instance=station,
                               initial={'abscissa': station.original_abscissa,
                                        'ordinate': station.original_ordinate})
        else:
            form = StationForm()

    return render_to_response('station_edit.html',
                              {'form': form},
                              context_instance=RequestContext(request))


@login_required
def station_edit(request, station_id):
    """
    Edit station details.

    Permissions for editing stations are handled by row level permissions
    """
    return _station_edit_or_create(request, station_id)


@permission_required('hcore.add_station')
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
    station = Station.objects.get(id=station_id)
    if request.user.has_row_perm(station, 'delete') and \
            request.user.has_perm('hcore.delete_station'):
        station.delete()
        ref = request.META.get('HTTP_REFERER', None)
        if ref and not ref.endswith(reverse('station_detail',
                                            args=[station_id])):
            return HttpResponseRedirect(ref)
        return render_to_response(
            'success.html',
            {'msg': 'Station deleted successfully', },
            context_instance=RequestContext(request))
    return HttpResponseForbidden('Forbidden', content_type='text/plain')


"""
Timeseries views
"""


def _timeseries_edit_or_create(request, tseries_id=None):
    station_id = request.GET.get('station_id', None)
    station = None
    instrument_id = request.GET.get('instrument_id', None)
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
        if not request.user.has_row_perm(station, 'edit'):
            return HttpResponseForbidden('Forbidden',
                                         content_type='text/plain')
    if station and not tseries:
        tseries = Timeseries(gentity=station, instrument=instrument)

    user = request.user
    # Done with checks
    if request.method == 'POST':
        if tseries and tseries.id:
            form = TimeseriesDataForm(request.POST, request.FILES,
                                      instance=tseries, user=user,
                                      gentity_id=station_id,
                                      instrument_id=instrument_id)
        else:
            form = TimeseriesForm(request.POST, request.FILES, user=user,
                                  gentity_id=station_id,
                                  instrument_id=instrument_id)
        if form.is_valid():
            tseries = form.save()
            # do stuff
            tseries.save()
            if not tseries_id:
                tseries_id = str(tseries.id)
            return HttpResponseRedirect(reverse('timeseries_detail',
                                        kwargs={'pk': tseries_id}))
    else:
        if tseries and tseries.id:
            form = TimeseriesDataForm(instance=tseries, user=user,
                                      gentity_id=station_id,
                                      instrument_id=instrument_id)
        else:
            form = TimeseriesForm(instance=tseries, user=user,
                                  gentity_id=station_id,
                                  instrument_id=instrument_id)

    return render_to_response('timeseries_edit.html', {'form': form},
                              context_instance=RequestContext(request))


@permission_required('hcore.add_timeseries')
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


@login_required
def timeseries_delete(request, timeseries_id):
    """
    Delete existing timeseries. Permissions are checked against the relative
    station that the timeseries is part of.
    """
    tseries = get_object_or_404(Timeseries, id=timeseries_id)
    related_station = tseries.related_station
    if tseries and related_station:
        if request.user.has_row_perm(related_station, 'edit') and \
                request.user.has_perm('hcore.delete_timeseries'):
            tseries.delete()
            ref = request.META.get('HTTP_REFERER', None)
            if ref and not ref.endswith(reverse('timeseries_detail',
                                                args=[timeseries_id])):
                return HttpResponseRedirect(ref)
            return render_to_response(
                'success.html',
                {'msg': 'Timeseries deleted successfully', },
                context_instance=RequestContext(request))
    return HttpResponseForbidden('Forbidden',
                                 content_type='text/plain')


"""
GentityFile/GenericData/Event Views
"""


def _gentityfile_edit_or_create(request, gfile_id=None):
    station_id = request.GET.get('station_id', None)
    if gfile_id:
        # Edit
        gfile = get_object_or_404(GentityFile, id=gfile_id)
    else:
        # Add
        gfile = None

    if gfile_id:
        station = gfile.related_station
        station_id = station.id
        if not request.user.has_row_perm(station, 'edit'):
            return HttpResponseForbidden('Forbidden',
                                         content_type='text/plain')

    if station_id and not gfile_id:
        # Adding new
        station = get_object_or_404(Station, id=station_id)
        if not request.user.has_row_perm(station, 'edit'):
            return HttpResponseForbidden('Forbidden',
                                         content_type='text/plain')

    user = request.user
    # Done with checks
    if request.method == 'POST':
        if gfile:
            form = GentityFileForm(request.POST, request.FILES,
                                   instance=gfile, user=user)
        else:
            form = GentityFileForm(request.POST, request.FILES, user=user)
        if form.is_valid():
            gfile = form.save()
            # do stuff
            gfile.save()
            if not gfile_id:
                gfile_id = str(gfile.id)
            return HttpResponseRedirect(reverse('station_detail',
                                        kwargs={'pk': str(gfile.gentity.id)}))
    else:
        if gfile:
            form = GentityFileForm(instance=gfile, user=user,
                                   gentity_id=station_id)
        else:
            form = GentityFileForm(user=user, gentity_id=station_id)

    return render_to_response('gentityfile_edit.html', {'form': form},
                              context_instance=RequestContext(request))


@permission_required('hcore.add_gentityfile')
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
    if gfile and related_station:
        if request.user.has_row_perm(related_station, 'edit') and \
                request.user.has_perm('hcore.delete_gentityfile'):
            gfile.delete()
            ref = request.META.get('HTTP_REFERER', None)
            if ref:
                return HttpResponseRedirect(ref)
            return render_to_response(
                'success.html',
                {'msg': 'GentityFile deleted successfully', },
                context_instance=RequestContext(request))
    return HttpResponseForbidden('Forbidden',
                                 content_type='text/plain')


"""
GentityGenericData View
"""


def _gentitygenericdata_edit_or_create(request, ggenericdata_id=None):
    station_id = request.GET.get('station_id', None)
    if ggenericdata_id:
        # Edit
        ggenericdata = get_object_or_404(GentityGenericData,
                                         id=ggenericdata_id)
    else:
        # Add
        ggenericdata = None

    if ggenericdata_id:
        station = ggenericdata.related_station
        station_id = station.id
        if not request.user.has_row_perm(station, 'edit'):
            return HttpResponseForbidden('Forbidden',
                                         content_type='text/plain')

    if station_id and not ggenericdata_id:
        # Adding new
        station = get_object_or_404(Station, id=station_id)
        if not request.user.has_row_perm(station, 'edit'):
            return HttpResponseForbidden('Forbidden',
                                         content_type='text/plain')

    user = request.user
    # Done with checks
    if request.method == 'POST':
        if ggenericdata:
            form = GentityGenericDataForm(request.POST, request.FILES,
                                          instance=ggenericdata, user=user)
        else:
            form = GentityGenericDataForm(request.POST, request.FILES,
                                          user=user)
        if form.is_valid():
            ggenericdata = form.save()
            # do stuff
            ggenericdata.save()
            if not ggenericdata_id:
                ggenericdata_id = str(ggenericdata.id)
            return HttpResponseRedirect(reverse(
                'station_detail', kwargs={'object_id':
                                          str(ggenericdata.gentity.id)}))
    else:
        if ggenericdata:
            form = GentityGenericDataForm(instance=ggenericdata, user=user,
                                          gentity_id=station_id)
        else:
            form = GentityGenericDataForm(user=user, gentity_id=station_id)

    return render_to_response('gentitygenericdata_edit.html', {'form': form},
                              context_instance=RequestContext(request))


@permission_required('hcore.add_gentityfile')
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
    return _gentitygenericdata_edit_or_create(request,
                                              ggenericdata_id=ggenericdata_id)


@login_required
def gentitygenericdata_delete(request, ggenericdata_id):
    """
    Delete existing gentitygenericdata. Permissions are checked against the
    relative station that the gentitygenericdata is part of.
    """
    ggenericdata = get_object_or_404(GentityGenericData, id=ggenericdata_id)
    related_station = ggenericdata.related_station
    if ggenericdata and related_station:
        if request.user.has_row_perm(related_station, 'edit') and \
                request.user.has_perm('hcore.delete_gentityfile'):
            ggenericdata.delete()
            ref = request.META.get('HTTP_REFERER', None)
            if ref:
                return HttpResponseRedirect(ref)
            return render_to_response(
                'success.html',
                {'msg': 'GentityGenericData deleted successfully', },
                context_instance=RequestContext(request))
    return HttpResponseForbidden('Forbidden', content_type='text/plain')


"""
GentityEvent View
"""


def _gentityevent_edit_or_create(request, gevent_id=None):
    station_id = request.GET.get('station_id', None)
    if gevent_id:
        # Edit
        gevent = get_object_or_404(GentityEvent, id=gevent_id)
    else:
        # Add
        gevent = None

    if gevent_id:
        station = gevent.related_station
        station_id = station.id
        if not request.user.has_row_perm(station, 'edit'):
            return HttpResponseForbidden('Forbidden',
                                         content_type='text/plain')

    if station_id and not gevent_id:
        # Adding new
        station = get_object_or_404(Station, id=station_id)
        if not request.user.has_row_perm(station, 'edit'):
            return HttpResponseForbidden('Forbidden',
                                         content_type='text/plain')
        gevent = GentityEvent(gentity=station)

    user = request.user
    # Done with checks
    if request.method == 'POST':
        if gevent:
            form = GentityEventForm(request.POST, request.FILES,
                                    instance=gevent, user=user)
        else:
            form = GentityEventForm(request.POST, request.FILES, user=user)
        if form.is_valid():
            gevent = form.save()
            # do stuff
            gevent.save()
            if not gevent_id:
                gevent_id = str(gevent.id)

            return HttpResponseRedirect(reverse(
                'station_detail',
                kwargs={'pk': str(gevent.gentity.id)}))
    else:
        if gevent:
            form = GentityEventForm(instance=gevent, user=user,
                                    gentity_id=station_id)
        else:
            form = GentityEventForm(user=user, gentity_id=station_id)

    return render_to_response('gentityevent_edit.html', {'form': form},
                              context_instance=RequestContext(request))


@permission_required('hcore.add_gentityevent')
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
    if gevent and related_station:
        if request.user.has_row_perm(related_station, 'edit') and \
                request.user.has_perm('hcore.delete_gentityevent'):
            gevent.delete()
            ref = request.META.get('HTTP_REFERER', None)
            if ref:
                return HttpResponseRedirect(ref)
            return render_to_response(
                'success.html', {'msg': 'GentityEvent deleted successfully', },
                context_instance=RequestContext(request))
    return HttpResponseForbidden('Forbidden', content_type='text/plain')


def _gentityaltcode_edit_or_create(request, galtcode_id=None):
    station_id = request.GET.get('station_id', None)
    if galtcode_id:
        # Edit
        galtcode = get_object_or_404(GentityAltCode, id=galtcode_id)
    else:
        # Add
        galtcode = None

    if galtcode_id:
        station = galtcode.related_station
        station_id = station.id
        if not request.user.has_row_perm(station, 'edit'):
            return HttpResponseForbidden('Forbidden',
                                         content_type='text/plain')

    if station_id and not galtcode_id:
        # Adding new
        station = get_object_or_404(Station, id=station_id)
        if not request.user.has_row_perm(station, 'edit'):
            return HttpResponseForbidden('Forbidden',
                                         content_type='text/plain')

    user = request.user
    # Done with checks
    if request.method == 'POST':
        if galtcode:
            form = GentityAltCodeForm(request.POST, request.FILES,
                                      instance=galtcode, user=user)
        else:
            form = GentityAltCodeForm(request.POST, request.FILES, user=user)
        if form.is_valid():
            galtcode = form.save()
            # do stuff
            galtcode.save()
            if not galtcode_id:
                galtcode_id = str(galtcode.id)
            return HttpResponseRedirect(
                reverse('station_detail',
                        kwargs={'object_id': str(galtcode.gentity.id)}))
    else:
        if galtcode:
            form = GentityAltCodeForm(instance=galtcode, user=user,
                                      gentity_id=station_id)
        else:
            form = GentityAltCodeForm(user=user, gentity_id=station_id)

    return render_to_response('gentityaltcode_edit.html',
                              {'form': form},
                              context_instance=RequestContext(request))


@permission_required('hcore.add_gentityaltcode')
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
    return _gentityaltcode_edit_or_create(request,
                                          galtcode_id=gentityaltcode_id)


@login_required
def gentityaltcode_delete(request, gentityaltcode_id):
    """
    Delete existing gentityaltcode. Permissions are checked against the
    relative station that the gentityaltcode is part of.
    """
    galtcode = get_object_or_404(GentityAltCode, id=gentityaltcode_id)
    related_station = galtcode.related_station
    if galtcode and related_station:
        if request.user.has_row_perm(related_station, 'edit') and \
                request.user.has_perm('hcore.delete_gentityaltcode'):
            galtcode.delete()
            ref = request.META.get('HTTP_REFERER', None)
            if ref:
                return HttpResponseRedirect(ref)
            return render_to_response(
                'success.html',
                {'msg': 'GentityAltCode deleted successfully', },
                context_instance=RequestContext(request))
    return HttpResponseForbidden('Forbidden',
                                 content_type='text/plain')

"""
Overseer Views
"""


def _overseer_edit_or_create(request, overseer_id=None, station_id=None):
    station_id = request.GET.get('station_id', None)
    if overseer_id:
        # Edit
        overseer = get_object_or_404(Overseer, id=overseer_id)
    else:
        # Add
        overseer = None

    if overseer_id:
        station = overseer.station
        station_id = station.id
        if not request.user.has_row_perm(station, 'edit'):
            return HttpResponseForbidden('Forbidden',
                                         content_type='text/plain')

    if station_id and not overseer_id:
        # Adding new
        station = get_object_or_404(Station, id=station_id)
        if not request.user.has_row_perm(station, 'edit'):
            return HttpResponseForbidden('Forbidden',
                                         content_type='text/plain')
        overseer = Overseer(station=station)

    user = request.user
    # Done with checks
    if request.method == 'POST':
        if overseer:
            form = OverseerForm(request.POST, request.FILES, instance=overseer,
                                user=user)
        else:
            form = OverseerForm(request.POST, request.FILES, user=user)
        if form.is_valid():
            overseer = form.save()
            # do stuff
            overseer.save()
            if not overseer_id:
                overseer_id = str(overseer.id)
            return HttpResponseRedirect(
                reverse('station_detail',
                        kwargs={'object_id': str(overseer.station.id)}))
    else:
        if overseer:
            form = OverseerForm(instance=overseer, user=user,
                                gentity_id=station_id)
        else:
            form = OverseerForm(user=user, gentity_id=station_id)

    return render_to_response('overseer_edit.html', {'form': form},
                              context_instance=RequestContext(request))


@permission_required('hcore.add_overseer')
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
    if overseer and related_station:
        if request.user.has_row_perm(related_station, 'edit') and \
                request.user.has_perm('hcore.delete_overseer'):
            overseer.delete()
            ref = request.META.get('HTTP_REFERER', None)
            if ref:
                return HttpResponseRedirect(ref)
            return render_to_response(
                'success.html',
                {'msg': 'Overseer deleted successfully', },
                context_instance=RequestContext(request))
    return HttpResponseForbidden('Forbidden', content_type='text/plain')


"""
Instument views
"""


def _instrument_edit_or_create(request, instrument_id=None):
    station_id = request.GET.get('station_id', None)
    if instrument_id:
        # Edit
        instrument = get_object_or_404(Instrument, id=instrument_id)
    else:
        # Add
        instrument = None

    if instrument_id:
        station = instrument.station
        station_id = station.id
        if not request.user.has_row_perm(station, 'edit'):
            return HttpResponseForbidden('Forbidden',
                                         content_type='text/plain')

    if station_id and not instrument_id:
        station = get_object_or_404(Station, id=station_id)
        if not request.user.has_row_perm(station, 'edit'):
            return HttpResponseForbidden('Forbidden',
                                         content_type='text/plain')
        instrument = Instrument(station=station)

    user = request.user
    # Done with checks
    if request.method == 'POST':
        if instrument:
            form = InstrumentForm(request.POST,
                                  instance=instrument, user=user)
        else:
            form = InstrumentForm(request.POST, user=user)
        if form.is_valid():
            instrument = form.save()
            # do stuff
            instrument.save()
            if not instrument_id:
                instrument_id = str(instrument.id)
            return HttpResponseRedirect(
                reverse('instrument_detail', kwargs={'pk': instrument_id}))
    else:
        if instrument:
            form = InstrumentForm(instance=instrument, user=user,
                                  gentity_id=station_id)
        else:
            form = InstrumentForm(user=user, gentity_id=station_id)

    return render_to_response(
        'instrument_edit.html', {'form': form},
        context_instance=RequestContext(request))


@permission_required('hcore.add_instrument')
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


@login_required
def instrument_delete(request, instrument_id):
    """
    Delete existing instrument. Permissions are checked against the relative
    station that the instrument is part of.
    """
    instrument = get_object_or_404(Instrument, id=instrument_id)
    related_station = instrument.station
    if instrument and related_station:
        if request.user.has_row_perm(related_station, 'edit') and \
                request.user.has_perm('hcore.delete_instrument'):
            instrument.delete()
            ref = request.META.get('HTTP_REFERER', None)
            if ref and not ref.endswith(reverse('instrument_detail',
                                                args=[instrument_id])):
                return HttpResponseRedirect(ref)
            return render_to_response(
                'success.html',
                {'msg': 'Instrument deleted successfully', },
                context_instance=RequestContext(request))
    return HttpResponseForbidden('Forbidden', content_type='text/plain')


"""
Generic model creation
"""

ALLOWED_TO_EDIT = ('waterbasin', 'waterdivision', 'person', 'organization',
                   'stationtype', 'variable', 'timezone',
                   'politicaldivision', 'instrumenttype', 'unitofmeasurement',
                   'filetype', 'eventtype', 'gentityaltcodetype', 'timestep',
                   'gentityaltcode', 'gentityfile', 'gentityevent',
                   'gentitygenericdatatype')


class ModelAddView(CreateView):

    template_name = 'model_add.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        # Verify url parms correctness
        popup = self.request.GET.get('_popup', False)
        if not popup and self.request.method == 'GET' \
                and '_complete' not in self.request.GET:
            raise Http404

        # Determine self.model and self.fields
        try:
            self.model = ContentType.objects.get(
                model=kwargs['model_name'], app_label='hcore'
            ).model_class()
        except (ContentType.DoesNotExist,
                ContentType.MultipleObjectsReturned):
            raise Http404
        self.fields = [f.name for f in self.model._meta.fields if f.editable]

        # Check permissions
        if not kwargs['model_name'] in ALLOWED_TO_EDIT or not \
                self.request.user.has_perm('hcore.add_' +
                                           kwargs['model_name']):
            return HttpResponseForbidden('Forbidden',
                                         content_type='text/plain')

        return super(ModelAddView, self).dispatch(*args, **kwargs)

    def get_form_class(self):
        return TimeStepForm if self.model.__name__ == 'TimeStep' \
            else super(ModelAddView, self).get_form_class()

    def get_extra_context(self):
        context = super(ModelAddView, self).get_extra_context()
        context['form_prefix'] = self.model.__name__
        return context
