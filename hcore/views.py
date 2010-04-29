import calendar
import json
import math
import mimetypes
import os
import django.db
import pthelma.timeseries
from string import lower, split
from django.http import (HttpResponse, HttpResponseRedirect,
                            HttpResponseForbidden, Http404)
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views.generic import list_detail
from django.views.generic.create_update import create_object
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db.models import Q
from django.core.servers.basehttp import FileWrapper
from django.core.urlresolvers import reverse
from django.utils import simplejson
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _
from enhydris.hcore.models import *
from enhydris.hcore.decorators import *
from enhydris.hcore.forms import *



####################################################
# VIEWS

def index(request):
    return render_to_response('index.html', {},
        context_instance=RequestContext(request))


def protect_gentityfile(request):
    """
    This view is used to disallow users to be able to browse through the
    uploaded gentity files which is the default behaviour of django.
    """
    response = render_to_response('404.html',
                  RequestContext(request))
    response.status_code = 404
    return response

def station_detail(request, *args, **kwargs):
    stat = get_object_or_404(Station, pk=kwargs["object_id"])
    owner = stat.owner
    kwargs["extra_context"] = {"owner":owner,
        "enabled_user_content":settings.USERS_CAN_ADD_CONTENT}
    kwargs["request"] = request
    return list_detail.object_detail(*args, **kwargs)

#FIXME: Now you must keep the "political_division" FIRST in order
@filter_by(('political_division','owner', 'type', 'water_basin',
            'water_division',))
@sort_by
def station_list(request, queryset, *args, **kwargs):

    if request.GET.has_key("ts_only") and request.GET["ts_only"]=="True":
        from django.db.models import Count
        tmpset = queryset.annotate(tsnum=Count('timeseries'))
        queryset = tmpset.exclude(tsnum=0)

    if request.GET.has_key("check") and request.GET["check"]=="search":
        # The case we got a simple search request
        kwargs["extra_context"] = {"search":True}
        query_string = request.GET.get('q', "")
        search_terms = query_string.split()
        results = queryset

        if search_terms:
            query = Q()
            for term in search_terms:
                query &= (Q(name__icontains=term) | Q(name_alt__icontains=term) |
                          Q(short_name__icontains=term )|
                          Q(short_name_alt__icontains=term) |
                          Q(remarks__icontains=term) |
                          Q(remarks_alt__icontains=term)|
                          Q(water_basin__name__icontains=term) |
                          Q(water_basin__name_alt__icontains=term) |
                          Q(water_division__name__icontains=term) |
                          Q(water_division__name_alt__icontains=term) |
                          Q(political_division__name__icontains=term) |
                          Q(political_division__name_alt__icontains=term) |
                          Q(type__descr__icontains=term) |
                          Q(type__descr_alt__icontains=term) |
                          Q(owner__organization__name__icontains=term) |
                          Q(owner__person__first_name__icontains=term) |
                          Q(owner__person__last_name__icontains=term))
            results = results.filter(query).distinct()
            queryset = results
        else:
            results = []
        kwargs["extra_context"].update({'query': query_string,
                                        'terms': search_terms, })


    if hasattr(settings, 'USERS_CAN_ADD_CONTENT'):
        if settings.USERS_CAN_ADD_CONTENT:
            kwargs["extra_context"].update({'enabled_user_content':
                                    settings.USERS_CAN_ADD_CONTENT})

    return list_detail.object_list(request,queryset=queryset, *args, **kwargs )


# This list represents all the columns of the map table and is used when the
# user wants to sort the table. The fields represent model fields and are
# written the same way in this list.
SORTING_DICT= ('id', 'id', 'name', 'water_basin', 'water_division',
                            'political_division', 'owner', 'type')

def station_info(request, *args, **kwargs):
    """
    This function takes care of serving station data via AJAX for the map
    table.
    """
    from django.utils import simplejson
    from django.core import serializers
#    if settings.DEBUG:
#        print 'iDisplayStart: %s' % request.POST.get('iDisplayStart','')
#        print 'iDisplayLength: %s' % request.POST.get('iDisplayLength','')
#        print 'sSearch: %s' % request.POST.get('sSearch','')
#        print 'bEscapeRegex: %s' % request.POST.get('bEscapeRegex','')
#        print 'iColumns: %s' % request.POST.get('iColumns','')
#        print 'iSortingCols: %s' % request.POST.get('iSortingCols','')
#        print 'iSortCol_0: %s' % request.POST.get('iSortCol_0','')
#        print 'sSortDir_0: %s' % request.POST.get('sSortDir_0','')
#        print 'iSortCol_1: %s' % request.POST.get('iSortCol_1','')
#        print 'sSortDir_1: %s' % request.POST.get('sSortDir_1','')
#        print 'sEcho: %s' % request.POST.get('sEcho','')
#


    sids = ""
    if request.POST.has_key('sids'):
        sids = request.POST['sids']

    if request.POST and request.POST.has_key('station_list'):
        ids = split(request.POST['station_list'],",")
        stations = Station.objects.filter(id__in=ids)
    else:
        stations = Station.objects.all()



    # for search
    # for sorting

    scols = request.POST.get('iSortingCols', '0')
    for i in range(0,int(scols)):

        if request.POST.has_key('iSortCol_'+str(i)):
            col = int(request.POST.get('iSortCol_'+str(i)))
            if request.POST.has_key('sSortDir_'+str(i)) and \
                request.POST['sSortDir_'+str(i)] == 'asc':
                stations=stations.order_by(SORTING_DICT[col])
            else:
                stations=stations.order_by(SORTING_DICT[col]).reverse()

    # for items displayed
    dlength = int(request.POST.get('iDisplayLength','10'))
    dstart = int(request.POST.get('iDisplayStart','0'))


    json = simplejson.dumps({
        'sEcho': request.POST.get('sEcho','1'),
        'iTotalRecords': stations.count(),
        'iTotalDisplayRecords': stations.count(),
        'aaData': [
            [render_to_string("select_box.html", {'station':station,
                                    'sids':sids}),
            '<a href="/stations/d/'+str(station.id)+'">'+str(station.id)+'</a>',
            unicode(station),
            unicode(station.water_division),
            unicode(station.water_basin),
            unicode(station.political_division),
            unicode(station.owner),
            unicode(station.type)] for station in stations[dstart:dstart+dlength]]})
    return HttpResponse(json, mimetype='application/json')


def timeseries_data(request, *args, **kwargs):
    if request.method == "GET" and request.GET.has_key('object_id'):
        response = HttpResponse(content_type='text/plain;charset=utf8')
        response.status_code = 200
        object_id = request.GET['object_id']
        ts = pthelma.timeseries.Timeseries(int(object_id))
        ts.read_from_db(django.db.connection)
        chart_data = []
        pos = 0
        ts_list = ts.items()
        length =  len(ts_list)
        step = int(length/250)
        while pos < length:
            try:
                k,v = ts_list[pos]
            except IndexError:
                break
            pos += step
            if math.isnan(v):
                v=0
            chart_data.append([calendar.timegm(k.timetuple())*1000, v])

        if chart_data:
            response.content = json.dumps(chart_data)
        else:
            response.content = json.dumps("")
        return response
    else:
        response = render_to_response('404.html',
                      RequestContext(request))
        response.status_code = 404
        return response

def timeseries_detail(request, queryset, object_id, *args, **kwargs):
    """Return the details for a specific timeseries object."""

    enabled_user_content = False
    if hasattr(settings, 'USERS_CAN_ADD_CONTENT'):
        if settings.USERS_CAN_ADD_CONTENT:
            enabled_user_content = True

    anonymous_can_download_data = False
    if hasattr(settings, 'TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS') and\
            settings.TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS:
        anonymous_can_download_data = True
    tseries = get_object_or_404(Timeseries, id=object_id)
    related_station = tseries.related_station
    kwargs["extra_context"] = {'related_station': related_station,
                              'enabled_user_content':enabled_user_content,
                              'anonymous_can_download_data':
                                    anonymous_can_download_data}

    return list_detail.object_detail(request, queryset, object_id, *args, **kwargs)


def instrument_detail(request, queryset, object_id, *args, **kwargs):
    """Return the details for a specific timeseries object."""

    enabled_user_content = False
    if hasattr(settings, 'USERS_CAN_ADD_CONTENT'):
        if settings.USERS_CAN_ADD_CONTENT:
            enabled_user_content = True

    instrument = get_object_or_404(Instrument, id=object_id)
    related_station = instrument.station
    kwargs["extra_context"] = {'related_station': related_station,
                               'enabled_user_content':enabled_user_content}
    return list_detail.object_detail(request, queryset, object_id, *args, **kwargs)


@filter_by(('political_division','owner', 'type', 'water_basin',
            'water_division',))
@sort_by
def map_view(request, stations='',  *args, **kwargs):

    if request.GET.has_key("ts_only") and request.GET["ts_only"]=="True":
        from django.db.models import Count
        tmpset = stations.annotate(tsnum=Count('timeseries'))
        stations = tmpset.exclude(tsnum=0)

    if request.GET.has_key("check") and request.GET["check"]=="search":
        # The case we got a simple search request
        kwargs["extra_context"] = {"search":True}
        query_string = request.GET.get('q', "")
        search_terms = query_string.split()
        results = stations

        if search_terms:
            query = Q()
            for term in search_terms:
                query &= (Q(name__icontains=term) | Q(name_alt__icontains=term) |
                          Q(short_name__icontains=term )|
                          Q(short_name_alt__icontains=term) |
                          Q(remarks__icontains=term) |
                          Q(remarks_alt__icontains=term)|
                          Q(water_basin__name__icontains=term) |
                          Q(water_basin__name_alt__icontains=term) |
                          Q(water_division__name__icontains=term) |
                          Q(water_division__name_alt__icontains=term) |
                          Q(political_division__name__icontains=term) |
                          Q(political_division__name_alt__icontains=term) |
                          Q(type__descr__icontains=term) |
                          Q(type__descr_alt__icontains=term) |
                          Q(owner__organization__name__icontains=term) |
                          Q(owner__person__first_name__icontains=term) |
                          Q(owner__person__last_name__icontains=term))
            results = results.filter(query).distinct()
            stations = results
        else:
            results = []
        kwargs["extra_context"].update({'query': query_string,
                                        'terms': search_terms, })
    try:
        gis = settings.GIS_SERVER
    except AttributeError:
        gis = None
    kwargs["extra_context"].update({'gis_server':gis},)

    kwargs["extra_context"].update({'station_list': [ s.id for s in stations]},)


    return render_to_response('hcore/station_map.html', kwargs["extra_context"],
             context_instance=RequestContext(request))

def get_subdivision(request, division_id):
    """Ajax call to refresh divisions in filter table"""
    response = HttpResponse(content_type='text/plain;charset=utf8',
                            mimetype='application/json')
    div = PoliticalDivision.objects.get(pk=division_id)
    parent_divs = PoliticalDivision.objects.filter(Q(name=div.name)&
                                                 Q(name_alt=div.name_alt)&
                                                 Q(short_name=div.short_name)&
                                           Q(short_name_alt=div.short_name_alt))
    divisions = PoliticalDivision.objects.filter(parent__in=[p.id for p in parent_divs])
    response.write("[")
    for num,div in enumerate(divisions):
        response.write(simplejson.dumps({"name": div.name,"id": div.pk}))
        if num < divisions.count()-1:
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

    if hasattr(settings, "STORE_TSDATA_LOCALLY") and\
      settings.STORE_TSDATA_LOCALLY:
        gfile = get_object_or_404(GentityFile, pk=int(gf_id))
        try:
            filename = gfile.content.file.name
            wrapper  = FileWrapper(open(filename))
        except:
            raise Http404
        download_name = gfile.content.name.split('/')[-1]
        content_type = mimetypes.guess_type(filename)[0]
        response = HttpResponse(content_type=content_type)
        response['Content-Length'] = os.path.getsize(filename)
        response['Content-Disposition'] = "attachment; filename=%s"%download_name

        for chunk in wrapper:
            response.write(chunk)
    else:
        """
        Fetch GentityFile content from remote instance.
        """
        import urllib2, re, base64

        gfile = get_object_or_404(GentityFile, pk=int(gf_id))

        # Read the creds from the settings file
        REMOTE_INSTANCE_CREDENTIALS = getattr(settings,
                'REMOTE_INSTANCE_CREDENTIALS', {})

        # Get the original GentityFile id and the source database
        if gfile.original_id and gfile.original_db:
            gf_id = gfile.original_id
            db_host = gfile.original_db.hostname
        else:
            request.notifications.error("No data was found for "
                    " the requested Gentity file.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', None) or '/')

        # Next we check the setting files for a uname/pass for this host
        uname, pwd = REMOTE_INSTANCE_CREDENTIALS.get(db_host, (None,None))

        # We craft the url
        url = 'http://'+db_host + '/api/gfdata/' + str(gf_id)
        req = urllib2.Request(url)
        try:
            handle = urllib2.urlopen(req,timeout=10)
        except IOError, e:
            # here we *want* to fail
            pass
        else:
            # If we don't fail then the page isn't protected
            # which means something is not right. Raise hell
            # mail admins + return user notification.
            request.notifications.error(GF_ERROR)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', None) or '/')

        if not hasattr(e, 'code') or e.code != 401:
            # we got an error - but not a 401 error
            request.notifications.error(GF_ERROR)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', None) or '/')

        authline = e.headers['www-authenticate']
        # this gets the www-authenticate line from the headers
        # which has the authentication scheme and realm in it

        authobj = re.compile(
            r'''(?:\s*www-authenticate\s*:)?\s*(\w*)\s+realm=['"]([^'"]+)['"]''',
            re.IGNORECASE)
        # this regular expression is used to extract scheme and realm
        matchobj = authobj.match(authline)

        if not matchobj:
            # if the authline isn't matched by the regular expression
            # then something is wrong
            request.notifications.error(GF_ERROR)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', None) or '/')

        scheme = matchobj.group(1)
        realm = matchobj.group(2)
        # here we've extracted the scheme
        # and the realm from the header
        if scheme.lower() != 'basic':
            # we don't support other auth
            # mail admins + inform user of error
            request.notifications.error(GF_ERROR)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', None) or '/')

        # now the good part.
        base64string = base64.encodestring(
                '%s:%s' % (uname, pwd))[:-1]
        authheader =  "Basic %s" % base64string
        req.add_header("Authorization", authheader)

        try:
            handle = urllib2.urlopen(req)
        except IOError, e:
            # here we shouldn't fail if the username/password is right
            request.notifications.error(GF_ERROR)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', None) or '/')


        filedata = handle.read()

        download_name = gfile.content.name.split('/')[-1]
        content_type = gfile.file_type.mime_type
        response = HttpResponse(mimetype=content_type)
        response['Content-Length'] = len(filedata)
        response['Content-Disposition'] = "attachment; filename=%s"%download_name
        response.write(filedata)


    return response

TS_ERROR = ("There seems to be some problem with our internal infrastucture. The"
" admins have been notified of this and will try to resolve the matter as soon as"
" possible.  Please try again later.")

@timeseries_permission
def download_timeseries(request, object_id):
    """
    This function handles timeseries downloading either from the local db or
    from a remote instance.
    """

    timeseries = get_object_or_404(Timeseries, pk=int(object_id))

    # Check whether this instance has local store enabled or else we need to
    # fetch ts data from remote instance
    if hasattr(settings, 'STORE_TSDATA_LOCALLY') and\
        settings.STORE_TSDATA_LOCALLY:

        t = timeseries # nickname, because we use it much in next statement
        ts = pthelma.timeseries.Timeseries(
            id = int(object_id),
            time_step = pthelma.timeseries.TimeStep(
                length_minutes = t.time_step.length_minutes if t.time_step
                                            else 0,
                length_months = t.time_step.length_months if t.time_step
                                            else 0,
                nominal_offset =
                    (t.nominal_offset_minutes, t.nominal_offset_months)
                    if t.nominal_offset_minutes and t.nominal_offset_months
                    else None,
                actual_offset =
                    (t.actual_offset_minutes, t.actual_offset_months)
                    if t.actual_offset_minutes and t.actual_offset_months
                    else (0,0)
            ),
            unit = t.unit_of_measurement.symbol,
            title = t.name,
            timezone = '%s (UTC+%02d%02d)' % (t.time_zone.code,
                t.time_zone.utc_offset / 60, t.time_zone.utc_offset % 60),
            variable = t.variable.descr,
            precision = t.precision,
            comment = '%s\n\n%s' % (t.gentity.name, t.remarks)
            )
        ts.read_from_db(django.db.connection)
        response = HttpResponse(mimetype=
                                'text/vnd.openmeteo.timeseries; charset=utf-8')
        response['Content-Disposition'] = "attachment; filename=%s.hts"%(object_id,)
        ts.write_file(response)
        return response
    else:
        """
        Here we use the piston api to fetch a specific timeseries data from the
        original database from which it was synced. Since this requires http
        authentication, we use the username/password stored in the settings file to
        connect.

        NOTE: The user used for the sync should be a superuser in the remote
        instance.
        """
        import urllib2, re, base64

        # Read the creds from the settings file
        REMOTE_INSTANCE_CREDENTIALS = getattr(settings,
                'REMOTE_INSTANCE_CREDENTIALS', {})

        # Get the original timeseries id and the source database
        if timeseries.original_id and timeseries.original_db:
            ts_id = timeseries.original_id
            db_host = timeseries.original_db.hostname
        else:
            request.notifications.error("No data was found for "
                    " the requested timeseries.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', None)
                                or reverse('timeseries_detail',args=[timeseries.id]))

        # Next we check the setting files for a uname/pass for this host
        uname, pwd = REMOTE_INSTANCE_CREDENTIALS.get(db_host, (None,None))

        # We craft the url
        url = 'http://'+db_host + '/api/tsdata/' + str(ts_id)
        req = urllib2.Request(url)
        try:
            handle = urllib2.urlopen(req,timeout=10)
        except IOError, e:
            # here we *want* to fail
            pass
        else:
            # If we don't fail then the page isn't protected
            # which means something is not right. Raise hell
            # mail admins + return user notification.
            request.notifications.error(TS_ERROR)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', None)
                                or reverse('timeseries_detail',args=[timeseries.id]))

        if not hasattr(e, 'code') or e.code != 401:
            # we got an error - but not a 401 error
            request.notifications.error(TS_ERROR)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', None)
                                or reverse('timeseries_detail',args=[timeseries.id]))

        authline = e.headers['www-authenticate']
        # this gets the www-authenticate line from the headers
        # which has the authentication scheme and realm in it

        authobj = re.compile(
            r'''(?:\s*www-authenticate\s*:)?\s*(\w*)\s+realm=['"]([^'"]+)['"]''',
            re.IGNORECASE)
        # this regular expression is used to extract scheme and realm
        matchobj = authobj.match(authline)

        if not matchobj:
            # if the authline isn't matched by the regular expression
            # then something is wrong
            request.notifications.error(TS_ERROR)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', None)
                                or reverse('timeseries_detail',args=[timeseries.id]))

        scheme = matchobj.group(1)
        realm = matchobj.group(2)
        # here we've extracted the scheme
        # and the realm from the header
        if scheme.lower() != 'basic':
            # we don't support other auth
            # mail admins + inform user of error
            request.notifications.error(TS_ERROR)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', None)
                                or reverse('timeseries_detail',args=[timeseries.id]))

        # now the good part.
        base64string = base64.encodestring(
                '%s:%s' % (uname, pwd))[:-1]
        authheader =  "Basic %s" % base64string
        req.add_header("Authorization", authheader)

        try:
            handle = urllib2.urlopen(req)
        except IOError, e:
            # here we shouldn't fail if the username/password is right
            request.notifications.error(TS_ERROR)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', None)
                                or reverse('timeseries_detail',args=[timeseries.id]))

        tsdata = handle.read()

        response = HttpResponse(mimetype='text/vnd.openmeteo.timeseries;charset=iso-8859-7')
        response['Content-Disposition']="attachment;filename=%s.hts"%(object_id,)

        response.write(tsdata)
        return response

def terms(request):
    return render_to_response('terms.html', RequestContext(request,{}) )

def help(request):
    return render_to_response('help.html', RequestContext(request,{}) )

"""
Model management views.
"""

def _station_edit_or_create(request,station_id=None):
    """
    This function updates existing stations and creates new ones.
    """
    from django.forms.models import inlineformset_factory
    user = request.user
    formsets = {}
    if station_id:
        # User is editing a station
        station = get_object_or_404(Station, id=station_id)
        if not user.has_row_perm(station, 'edit')\
            and not user.has_perm('hcore.change_station'):
            response = render_to_response('403.html',
                    RequestContext(request))
            response.status_code = 403
            return response
    else:
        # User is creating a new station
        station = None
        if not user.has_perm('hcore.add_station'):
            p = render_to_response('403.html',
                   RequestContext(request))
            resp.status_code = 403
            return resp

    OverseerFormset = inlineformset_factory(Station, Overseer,
                                            extra=1)
    InstrumentFormset = inlineformset_factory(Station, Instrument,
                                            extra=1)
    TimeseriesFormset = inlineformset_factory(Station, Timeseries,
                                            extra=1)

    if request.method == 'POST':
        if station:
            form = StationForm(request.POST,instance=station)
            formsets["Overseer"]  = OverseerFormset(request.POST,
                                    instance=station, prefix='Overseer')
            formsets["Instrument"]  = InstrumentFormset(request.POST,
                                    instance=station, prefix='Instrument')
            formsets["Timeseries"]  = TimeseriesFormset(request.POST,
                                    instance=station, prefix='Timeseries')
        else:
            form = StationForm(request.POST)
            formsets["Overseer"] = OverseerFormset(request.POST,
                                                      prefix='Overseer')
            formsets["Instrument"]  = InstrumentFormset(request.POST,
                                                      prefix='Instrument')
            formsets["Timeseries"]  = TimeseriesFormset(request.POST,
                                                      prefix='Timeseries')

        forms_validated = 0
        for type in formsets:
            if formsets[type].is_valid():
                forms_validated+=1
        if form.is_valid() and forms_validated == len(formsets):
            if station:
                om = station.maintainers.all()
                # To bypass djangos lazy fetching
                old_maintainers = list(om)
            else:
                old_maintainers = None
            station = form.save()
            if hasattr(settings, 'USERS_CAN_ADD_CONTENT')\
                and settings.USERS_CAN_ADD_CONTENT:
                    # Make creating user the station creator
                    if not station_id:
                        station.creator = request.user
                        # Give perms to the creator
                        user.add_row_perm(station, 'edit')
                        user.add_row_perm(station, 'delete')
                    # Handle maintainers
                    if old_maintainers:
                        for m_old in old_maintainers:
                            m_old.del_row_perm(station,'edit')
                    for m_new in station.maintainers.all():
                        m_new.add_row_perm(station,'edit')
            station.save()
            for type in formsets:
                formsets[type].save()
            if not station_id:
                station_id = str(station.id)
            return HttpResponseRedirect('/stations/d/'+station_id)
    else:
        if station:
            form = StationForm(instance=station)
            formsets["Overseer"]  = OverseerFormset(instance=station,
                                                         prefix='Overseer')
            formsets["Instrument"]  = InstrumentFormset(instance=station,
                                                         prefix='Instrument')
            formsets["Timeseries"]  = TimeseriesFormset(instance=station,
                                                         prefix='Timeseries')
        else:
            form = StationForm()
            formsets["Overseer"]  = OverseerFormset(prefix='Overseer')
            formsets["Instrument"]  = InstrumentFormset(prefix='Instrument')
            formsets["Timeseries"]  = TimeseriesFormset(prefix='Timeseries')
    return render_to_response('hcore/station_edit.html', {'form': form,
                            'formsets':formsets, },
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
def station_delete(request,station_id):
    """
    Delete existing station.

    Permissions for deleting stations are handled by our custom permissions app
    and django.contrib.auth since a user may be allowed to delete a specific
    station but not all of them (specified with row level permissions) or in
    case he is an admin,manager,etc he must be able to delete all of them
    (handled by django.contrib.auth)
    """
    station = Station.objects.get(id=station_id)
    if ( request.user.has_row_perm(station,'delete') or
         request.user.has_perm('hcore.delete_station')):
        station.delete();
        return render_to_response('success.html',
            {'msg': 'Station deleted successfully',},
            context_instance=RequestContext(request))
    response = render_to_response('403.html',
                   RequestContext(request))
    response.status_code = 403
    return response


"""
Timeseries views
"""

def _timeseries_edit_or_create(request,tseries_id=None,station_id=None):
    if tseries_id:
        # Edit
        tseries = get_object_or_404(Timeseries, id=tseries_id)
    else:
        # Add
        tseries = None

    if tseries_id and not station_id:
        # Editing
        try:
            station = tseries.related_station
        except:
            # Timeseries doesn't have a relative station.
            # This shouldn't happen. Admin should fix such cases
            response = render_to_response('404.html',
                       RequestContext(request))
            response.status_code = 404
            return response
        else:
            # Check perms
            if not request.user.has_row_perm(station,'edit'):
                response = render_to_response('403.html',
                               RequestContext(request))
                response.status_code = 403
                return response

    if station_id and not tseries_id:
        # Adding new
        station = get_object_or_404(Station, id=station_id)
        if not request.user.has_row_perm(station,'edit'):
            response = render_to_response('403.html',
                           RequestContext(request))
            response.status_code = 403
            return response

    user = request.user
    # Done with checks
    if request.method == 'POST':
        if tseries:
            form = TimeseriesDataForm(request.POST,request.FILES,instance=tseries,user=user)
        else:
            form = TimeseriesForm(request.POST,request.FILES,user=user)
        if form.is_valid():
            tseries = form.save()
            # do stuff
            tseries.save()
            if not tseries_id:
                tseries_id=str(tseries.id)
            return HttpResponseRedirect('/timeseries/d/'+tseries_id)
    else:
        if tseries:
            form = TimeseriesDataForm(instance=tseries,user=user)
        else:
            form = TimeseriesForm(user=user)

    return render_to_response('hcore/timeseries_edit.html', {'form': form},
                    context_instance=RequestContext(request))

@permission_required('hcore.add_timeseries')
def timeseries_add(request):
    """
    Create new timeseries. Timeseries can only be added as part of an existing
    station.
    """
    return _timeseries_edit_or_create(request)

@login_required
def timeseries_edit(request,timeseries_id):
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
        if request.user.has_row_perm(related_station, 'edit'):
            ts = pthelma.timeseries.Timeseries(int(timeseries_id))
            ts.delete_from_db(django.db.connection)
            tseries.delete()
            return render_to_response('success.html',
                    {'msg': 'Timeseries deleted successfully',},
                    context_instance=RequestContext(request))
    response = render_to_response('403.html',
                   RequestContext(request))
    response.status_code = 403
    return response


"""
GentityFile/Event Views
"""

def _gentityfile_edit_or_create(request,gfile_id=None,station_id=None):
    if gfile_id:
        # Edit
        gfile = get_object_or_404(GentityFile, id=gfile_id)
    else:
        # Add
        gfile = None


    if gfile_id and not station_id:
        # Editing
        try:
            station = gfile.gentity
        except:
            # GentityFile doesn't have a relative station.
            # This shouldn't happen. Admin should fix such cases
            response = render_to_response('404.html',
                       RequestContext(request))
            response.status_code = 404
            return response
        else:
            # Check perms
            if not request.user.has_row_perm(station,'edit'):
                response = render_to_response('403.html',
                               RequestContext(request))
                response.status_code = 403
                return response

    if station_id and not gfile_id:
        # Adding new
        station = get_object_or_404(Station, id=station_id)
        if not request.user.has_row_perm(station,'edit'):
            response = render_to_response('403.html',
                           RequestContext(request))
            response.status_code = 403
            return response

    user = request.user
    # Done with checks
    if request.method == 'POST':
        if gfile:
            form = GentityFileForm(request.POST,request.FILES,instance=gfile,user=user)
        else:
            form = GentityFileForm(request.POST,request.FILES,user=user)
        if form.is_valid():
            gfile = form.save()
            # do stuff
            gfile.save()
            if not gfile_id:
                gfile_id=str(gfile.id)
            return HttpResponseRedirect('/stations/d/'+str(gfile.gentity.id))
    else:
        if gfile:
            form = GentityFileForm(instance=gfile,user=user)
        else:
            form = GentityFileForm(user=user)

    return render_to_response('hcore/gentityfile_edit.html', {'form': form},
                    context_instance=RequestContext(request))

@permission_required('hcore.add_gentityfile')
def gentityfile_add(request):
    """
    Create new gentityfile. GentityFile can only be added as part of an existing
    station.
    """
    return _gentityfile_edit_or_create(request)

@login_required
def gentityfile_edit(request,gentityfile_id):
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
        if request.user.has_row_perm(related_station, 'edit'):
            gfile.delete()
            return render_to_response('success.html',
                    {'msg': 'GentityFile deleted successfully',},
                    context_instance=RequestContext(request))
    response = render_to_response('403.html',
                   RequestContext(request))
    response.status_code = 403
    return response


def _gentityevent_edit_or_create(request,gevent_id=None,station_id=None):
    if gevent_id:
        # Edit
        gevent = get_object_or_404(GentityEvent, id=gevent_id)
    else:
        # Add
        gevent = None

    if gevent_id and not station_id:
        # Editing
        try:
            station = gevent.gentity
        except:
            # GentityEvent doesn't have a relative station.
            # This shouldn't happen. Admin should fix such cases
            response = render_to_response('404.html',
                       RequestContext(request))
            response.status_code = 404
            return response
        else:
            # Check perms
            if not request.user.has_row_perm(station,'edit'):
                response = render_to_response('403.html',
                               RequestContext(request))
                response.status_code = 403
                return response

    if station_id and not gevent_id:
        # Adding new
        station = get_object_or_404(Station, id=station_id)
        if not request.user.has_row_perm(station,'edit'):
            response = render_to_response('403.html',
                           RequestContext(request))
            response.status_code = 403
            return response

    user = request.user
    # Done with checks
    if request.method == 'POST':
        if gevent:
            form = GentityEventForm(request.POST,request.FILES,instance=gevent,user=user)
        else:
            form = GentityEventForm(request.POST,request.FILES,user=user)
        if form.is_valid():
            gevent = form.save()
            # do stuff
            gevent.save()
            if not gevent_id:
                gevent_id=str(gevent.id)
            return HttpResponseRedirect('/stations/d/'+str(gevent.gentity.id))
    else:
        if gevent:
            form = GentityEventForm(instance=gevent,user=user)
        else:
            form = GentityEventForm(user=user)

    return render_to_response('hcore/gentityevent_edit.html', {'form': form},
                    context_instance=RequestContext(request))

@permission_required('hcore.add_gentityevent')
def gentityevent_add(request):
    """
    Create new gentityevent. GentityEvent can only be added as part of an existing
    station.
    """
    return _gentityevent_edit_or_create(request)

@login_required
def gentityevent_edit(request,gentityevent_id):
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
        if request.user.has_row_perm(related_station, 'edit'):
            gevent.delete()
            return render_to_response('success.html',
                    {'msg': 'GentityEvent deleted successfully',},
                    context_instance=RequestContext(request))
    response = render_to_response('403.html',
                   RequestContext(request))
    response.status_code = 403
    return response


def _gentityaltcode_edit_or_create(request,galtcode_id=None,station_id=None):
    if galtcode_id:
        # Edit
        galtcode = get_object_or_404(GentityAltCode, id=galtcode_id)
    else:
        # Add
        galtcode = None

    if galtcode_id and not station_id:
        # Editing
        try:
            station = galtcode.gentity
        except:
            # GentityAltCode doesn't have a relative station.
            # This shouldn't happen. Admin should fix such cases
            response = render_to_response('404.html',
                       RequestContext(request))
            response.status_code = 404
            return response
        else:
            # Check perms
            if not request.user.has_row_perm(station,'edit'):
                response = render_to_response('403.html',
                               RequestContext(request))
                response.status_code = 403
                return response

    if station_id and not galtcode_id:
        # Adding new
        station = get_object_or_404(Station, id=station_id)
        if not request.user.has_row_perm(station,'edit'):
            response = render_to_response('403.html',
                           RequestContext(request))
            response.status_code = 403
            return response

    user = request.user
    # Done with checks
    if request.method == 'POST':
        if galtcode:
            form = GentityAltCodeForm(request.POST,request.FILES,instance=galtcode,user=user)
        else:
            form = GentityAltCodeForm(request.POST,request.FILES,user=user)
        if form.is_valid():
            galtcode = form.save()
            # do stuff
            galtcode.save()
            if not galtcode_id:
                galtcode_id=str(galtcode.id)
            return HttpResponseRedirect('/stations/d/'+str(galtcode.gentity.id))
    else:
        if galtcode:
            form = GentityAltCodeForm(instance=galtcode,user=user)
        else:
            form = GentityAltCodeForm(user=user)

    return render_to_response('hcore/gentityaltcode_edit.html', {'form': form},
                    context_instance=RequestContext(request))

@permission_required('hcore.add_gentityaltcode')
def gentityaltcode_add(request):
    """
    Create new gentityaltcode. GentityAltCode can only be added as part of an existing
    station.
    """
    return _gentityaltcode_edit_or_create(request)

@login_required
def gentityaltcode_edit(request,gentityaltcode_id):
    """
    Edit existing gentityaltcode. Permissions are checked against the relative
    station that the gentityaltcode is part of.
    """
    return _gentityaltcode_edit_or_create(request, galtcode_id=gentityaltcode_id)

@login_required
def gentityaltcode_delete(request, gentityaltcode_id):
    """
    Delete existing gentityaltcode. Permissions are checked against the relative
    station that the gentityaltcode is part of.
    """
    galtcode = get_object_or_404(GentityAltCode, id=gentityaltcode_id)
    related_station = galtcode.related_station
    if galtcode and related_station:
        if request.user.has_row_perm(related_station, 'edit'):
            galtcode.delete()
            return render_to_response('success.html',
                    {'msg': 'GentityAltCode deleted successfully',},
                    context_instance=RequestContext(request))
    response = render_to_response('403.html',
                   RequestContext(request))
    response.status_code = 403
    return response



"""
Instument views
"""

def _instrument_edit_or_create(request,instrument_id=None,station_id=None):
    if instrument_id:
        # Edit
        instrument = get_object_or_404(Instrument, id=instrument_id)
    else:
        # Add
        instrument = None

    if instrument_id and not station_id:
        # Editing
        try:
            station = instrument.station
        except:
            # Instrument doesn't have a relative station.
            # This shouldn't happen. Admin should fix such cases
            response = render_to_response('404.html',
                       RequestContext(request))
            response.status_code = 404
            return response
        else:
            # Check perms
            if not request.user.has_row_perm(station,'edit'):
                response = render_to_response('403.html',
                               RequestContext(request))
                response.status_code = 403
                return response

    if station_id and not instrument_id:
        # Adding new
        station = get_object_or_404(Station, id=station_id)
        if not request.user.has_row_perm(station,'edit'):
            response = render_to_response('403.html',
                           RequestContext(request))
            response.status_code = 403
            return response

    user = request.user
    # Done with checks
    if request.method == 'POST':
        if instrument:
            form = InstrumentForm(request.POST,instance=instrument,user=user)
        else:
            form = InstrumentForm(request.POST,user=user)
        if form.is_valid():
            instrument = form.save()
            # do stuff
            instrument.save()
            if not instrument_id:
                instrument_id=str(instrument.id)
            return HttpResponseRedirect('/instruments/d/'+instrument_id)
    else:
        if instrument:
            form = InstrumentForm(instance=instrument,user=user)
        else:
            form = InstrumentForm(user=user)

    return render_to_response('hcore/instrument_edit.html', {'form': form},
                    context_instance=RequestContext(request))

@permission_required('hcore.add_instrument')
def instrument_add(request):
    """
    Create new instrument. Timeseries can only be added as part of an existing
    station.
    """
    return _instrument_edit_or_create(request)

@login_required
def instrument_edit(request,instrument_id):
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
        if request.user.has_row_perm(related_station, 'edit'):
            instrument.delete()
            return render_to_response('success.html',
                    {'msg': 'Instrument deleted successfully',},
                    context_instance=RequestContext(request))
    response = render_to_response('403.html',
                   RequestContext(request))
    response.status_code = 403
    return response




"""
Generic model creation
"""

ALLOWED_TO_EDIT = ('waterbasin', 'waterdivision', 'person', 'organization',
                   'stationtype', 'lentity','gentity', 'variable', 'timezone',
                   'politicaldivision','instrumenttype', 'unitofmeasurement',
                   'filetype','eventtype','gentityaltcodetype','timestep')

@login_required
def model_add(request, model_name=''):
    popup = False
    if '_popup' in request.GET:
        if request.GET['_popup'] == '1':
            popup = True
    if not popup and request.method == 'GET'\
        and not '_complete' in request.GET:
        response = render_to_response('404.html',
                   RequestContext(request))
        response.status_code = 404
        return response
    try:
        model = ContentType.objects.get(model=model_name).model_class()
    except (ContentType.DoesNotExist, ContentType.MultipleObjectsReturned):
        response = render_to_response('404.html',
                   RequestContext(request))
        response.status_code = 404
        return response
    if not model_name in ALLOWED_TO_EDIT\
       or not request.user.has_perm('hcore.add_'+model_name):
            response = render_to_response('403.html',
                   RequestContext(request))
            response.status_code = 403
            return response
    if '_complete' in request.GET:
        if request.GET['_complete'] == '1':
            newObject = model.objects.order_by('-pk')[0]
            return HttpResponse('<script type="text/javascript"'
                 'src="/media/js/admin/RelatedObjectLookups.js"></script>'
                 '<script type="text/javascript">'
                 'opener.dismissAddAnotherPopup(window,"%s","%s");</script>'\
                 % (escape(newObject._get_pk_val()), escape(newObject)))
    return create_object(request, model,
                post_save_redirect="/add/"+lower(model.__name__)+"/?_complete=1",
                template_name='hcore/model_add.html',
                form_class= TimeStepForm if model.__name__=='TimeStep' else None,
                extra_context={'form_prefix': model.__name__,})

# Profile page
def profile_view(request, username):
    from profiles.views import profile_detail
    if request.user and request.user.username == username:
        extra_content = {'user_enabled_content': getattr(settings,
                                   'USERS_CAN_ADD_CONTENT', False)}
        return profile_detail(request, username, extra_context=extra_content)
    else:
        user = get_object_or_404(User, username=username)
        return render_to_response('profiles/profile_public.html',
            { 'profile': user.get_profile()} ,
            context_instance=RequestContext(request))
