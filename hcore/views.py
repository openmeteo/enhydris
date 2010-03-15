import calendar
import json
import math
import django.db
import pthelma.timeseries

from string import lower
from django.http import (HttpResponse, HttpResponseRedirect,
                            HttpResponseForbidden, Http404)
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.generic import list_detail
from django.views.generic.create_update import create_object
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db.models import Q
from django.utils import simplejson
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _
from enhydris.hcore.models import *
from enhydris.hcore.decorators import filter_by, sort_by, timeseries_permission
from enhydris.hcore.forms import StationForm, TimeseriesForm, InstrumentForm



####################################################
# VIEWS

def index(request):
    return render_to_response('index.html', {},
        context_instance=RequestContext(request))


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
        tmpset = Station.objects.annotate(tsnum=Count('timeseries'))
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


    kwargs["extra_context"].update({'station_list':stations},)


    return render_to_response('hcore/station_map.html', kwargs["extra_context"],
             context_instance=RequestContext(request))

def get_subdivision(request, division_id):
    """Ajax call to refresh divisions in filter table"""
    response = HttpResponse(content_type='text/plain;charset=utf8')
    divisions = PoliticalDivision.objects.filter(parent=division_id)
    response.write("[")
    for div in divisions:
        response.write(simplejson.dumps({"name": div.name,"id": div.pk})+',')
    response.write("]")
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
        """Return plain text data of a specific timeseries.

        NOTE: All this function is obsolete the time it's written. It's only
        intended as proof-of-concept to download timeseries and open them in
        Hydrognomon. Changes are required on Hydrognomon, in order to proper
        implement version 2 of the timeseries "File format" here and in Hydrognomon,
        and in order to do proper security checks. In addition, all flags are
        removed before downloading timeseries, otherwise the current version of
        Hydrognomon is in trouble.
        """

        # Determine time step and convert it to old format
        t = timeseries.time_step
        if t:
            minutes, months = (t.length_minutes, t.length_months)
        else:
            minutes, months = ( 5, 0)
        old_timestep = 0
        if   (minutes, months) == (   5,  0): old_timestep = 7
        elif (minutes, months) == (  10,  0): old_timestep = 1
        elif (minutes, months) == (  60,  0): old_timestep = 2
        elif (minutes, months) == (1440,  0): old_timestep = 3
        elif (minutes, months) == (   0,  1): old_timestep = 4
        elif (minutes, months) == (   0, 12): old_timestep = 5
        time_step_strict = (not timeseries.nominal_offset_minutes) and (
                                            not timeseries.nominal_offset_months)
        time_step_strict = time_step_strict and 'True' or 'False'

        # Create a proper title and comment
        title = timeseries.name
        if not title: title = 'id=%d' % (timeseries.id)
        title = title.encode('iso-8859-7')
        symbol = timeseries.unit_of_measurement.symbol.encode('iso-8859-7')
        comment = [timeseries.variable.descr.encode('iso-8859-7'),
                   timeseries.gentity.name.encode('iso-8859-7')]

        ts = pthelma.timeseries.Timeseries(int(object_id))
        ts.read_from_db(django.db.connection)
        for k in ts.keys(): ts[k] = (ts[k], "") # Remove flags
        response = HttpResponse(mimetype=
                                'text/vnd.openmeteo.timeseries; charset=iso-8859-7')
        response['Content-Disposition'] = "attachment; filename=%s.hts"%(object_id,)
        response.write("Delimiter=,\r\n")
        response.write('FlagDelimiter=" "\r\n')
        response.write("DecimalSeparator=.\r\n")
        response.write("DateFormat=yyyy-mm-dd HH:nn\r\n")
        response.write("TimeStep=%d\r\n" % (old_timestep,))
        response.write("TimeStepStrict=%s\r\n" % (time_step_strict,))
        response.write("MUnit=%s\r\n" % (symbol,))
        response.write('Flags=""\r\n')
        response.write("Variable=0\r\n")# % (timeseries.variable.descr,))
        response.write("VariableType=Unknown\r\n")
        response.write("Title=%s\r\n" % (title,))
        for c in comment: response.write("Comment=%s\r\n" % (c,))
        response.write("\r\n")
        ts.write(response)
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
            return HttpResponseRedirect(request.META['HTTP_REFERER'])

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
            return HttpResponseRedirect(request.META['HTTP_REFERER'])

        if not hasattr(e, 'code') or e.code != 401:
            # we got an error - but not a 401 error
            request.notifications.error(TS_ERROR)
            return HttpResponseRedirect(request.META['HTTP_REFERER'])

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
            return HttpResponseRedirect(request.META['HTTP_REFERER'])

        scheme = matchobj.group(1)
        realm = matchobj.group(2)
        # here we've extracted the scheme
        # and the realm from the header
        if scheme.lower() != 'basic':
            # we don't support other auth
            # mail admins + inform user of error
            request.notifications.error(TS_ERROR)
            return HttpResponseRedirect(request.META['HTTP_REFERER'])

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
            return HttpResponseRedirect(request.META['HTTP_REFERER'])

        tsdata = handle.read()

        response = HttpResponse(mimetype='text/vnd.openmeteo.timeseries;charset=iso-8859-7')
        response['Content-Disposition']="attachment;filename=%s.hts"%(object_id,)

        response.write(tsdata)
        return response

def terms(request):
    return render_to_response('terms.html', RequestContext(request,{}) )


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
                    if not station.creator:
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
            form = TimeseriesForm(request.POST,request.FILES,instance=tseries,user=user)
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
            form = TimeseriesForm(instance=tseries,user=user)
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
                   'stationtype', 'lentity', 'politicaldivision')

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
