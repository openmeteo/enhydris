from StringIO import StringIO
from pyproj import Proj, transform
import os.path

from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.conf import settings

from pthelma.timeseries import Timeseries
from enhydris.hrain import models

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm


def index(request):
    from django.db.models import Max
    eventgroups = []
    year = 0
    small, big = settings.HRAIN_EVENT_CLOUD_FONTSIZE_RANGE
    increment = float(settings.HRAIN_EVENT_CLOUD_FONTSIZE_INCREMENT)
    max_precipitation = models.Event.objects.aggregate(
        Max('average_precipitation_depth'))['average_precipitation_depth__max']
    for e in models.Event.objects.order_by('-id').all():
        if e.start_date.year != year:
            year = e.start_date.year
            eventgroups.append({ 'year': year, 'events': [] })
        e.fontsize = small + int(e.average_precipitation_depth/
                max_precipitation*(big-small)/increment+0.5)*increment
        eventgroups[-1]['events'].append(e)
    return render_to_response('rain-index.html',
                                    { 'eventgroups': eventgroups },
                                    context_instance=RequestContext(request))


def _datetime_to_ordinal(dt):
    return dt.toordinal() + dt.hour/24.0 + dt.minute/1440.0


def _create_contour_map(ev):
    """Check whether a contour for a specified event exists, and if it doesn't,
    create it."""
    from scipy.interpolate import Rbf
    import numpy as np

    # Return immediately if file is already there
    filename = os.path.join(settings.HRAIN_STATIC_CACHE_PATH,
                                            'hrain-e%04d.png' % (ev.id,))
    if os.path.exists(filename): return

    # Calculate array a = [(x1, y1, z1), ...], where each triplet is the
    # co-ordinates of the point and the total rainfall.
    a = []
    for tsev in ev.timeseriesevent_set.all():
        gp = tsev.timeseries.gentity.gpoint
        p1 = Proj(init='epsg:%d' % (gp.srid,))
        p2 = Proj(init='epsg:%d' % (settings.HRAIN_CONTOUR_SRID,))
        (x, y) = transform(p1, p2, gp.abscissa, gp.ordinate)
        a.append((x, y, tsev.total_precipitation, gp.name))

    # Get the grid parameters
    GRANULARITY=100
    (x0, y0, x1, y1) = [float(x) for x in settings.HRAIN_CONTOUR_CHART_BOUNDS]
    dx, dy = (x1-x0)/GRANULARITY, (y1-y0)/GRANULARITY
    width, height = x1-x0, y1-y0

    # If we just interpolate, then the contours can be bad. What we actually
    # need to do is to tell the interpolator that far away the rainfall becomes
    # zero. So we actually work on a grid that is larger (three times larger),
    # we define rainfall at the edges as zero, we interpolate in there and
    # calculate the contours, and we crop it so that only its middle part is
    # shown. We call this grid the "greater" grid, so we suffix variables with
    # "gr" when they refer to it.
    xgr0, ygr0, xgr1, ygr1 = (x0-width, y0-height, x1+width, y1+height)
    a.append((xgr0, ygr0, 0.0, 'virtual'))
    a.append((xgr1, ygr0, 0.0, 'virtual'))
    a.append((xgr0, ygr1, 0.0, 'virtual'))
    a.append((xgr1, ygr1, 0.0, 'virtual'))
    a.append((xgr0+width/2, ygr0, 0.0, 'virtual'))
    a.append((xgr0+width/2, ygr1, 0.0, 'virtual'))
    a.append((xgr0, ygr0+height/2, 0.0, 'virtual'))
    a.append((xgr1, ygr0+height/2, 0.0, 'virtual'))

    # Now interpolate
    x = [i[0] for i in a]
    y = [i[1] for i in a]
    z = [i[2] for i in a]
    rbfi = Rbf(x, y, z, function='linear')
    xx = np.arange(xgr0, xgr1+dx, dx)
    yy = np.arange(ygr0, ygr1+dy, dy)
    zz = np.empty([3*GRANULARITY+1, 3*GRANULARITY+1])
    for i in xrange(0, 3*GRANULARITY):
        for j in xrange(0, 3*GRANULARITY):
            zz[j][i] = rbfi(xx[i], yy[j])
    # Crop
    zz = zz[GRANULARITY:2*GRANULARITY+1, GRANULARITY:2*GRANULARITY+1]

    # Create the chart
    chart_large_dimension = 500 # pixels
    chart_small_dimension = chart_large_dimension*min(y1-y0, x1-x0)/max(
                                                                y1-y0, x1-x0)
    if x1-x0>y1-y0:
        x_dim, y_dim = chart_large_dimension, chart_small_dimension
    else:
        x_dim, y_dim = chart_small_dimension, chart_large_dimension
    fig = plt.figure(figsize=(x_dim/96.0, y_dim/96.0), dpi=96)
    for x, y, z, name in a:
        if name=='virtual': continue
        plt.plot(x, y, marker='x', linestyle='None', color='black')
        plt.text(x, y, name, color='black')
    plt.axis('off')
    im = plt.imshow(zz, interpolation='bilinear', origin='lower',
        cmap=cm.winter_r, extent=(x0, x1, y0, y1))
    cs = plt.contour(zz, extent=(x0, x1, y0, y1), colors="red")
    plt.clabel(cs, inline=1, fontsize=10, fmt="%1.0f")

    fig.savefig(filename)


def _create_chart(tsev):
    """Check whether a chart for specified event and timeseries exists, and
    if it doesn't, create it."""
    from matplotlib.dates import DateFormatter, HourLocator, MinuteLocator
    from matplotlib.lines import TICKDOWN
    from matplotlib.figure import SubplotParams

    # Return immediately if file is already there
    filename = os.path.join(settings.HRAIN_STATIC_CACHE_PATH,
                 'hrain-e%04d-t%05d.png' % (tsev.event.id, tsev.timeseries.id))
    if os.path.exists(filename): return

    # Essential chart setup
    fig = plt.figure(figsize=(4, 2), dpi=96,
                                    subplotpars=SubplotParams(bottom=0.2))
    ax = fig.add_subplot(111)
    x, y = [], []
    t = Timeseries()
    t.read(StringIO(tsev.data))
    for i in t:
        x.append(_datetime_to_ordinal(i))
        y.append(t[i])
    ax.bar(x, y, width=0.006)

    # Y axis
    ax.set_ylim(0, int(1.0+max(5.0, tsev.event.max_measurement)))
    ax.set_ylabel(tsev.timeseries.unit_of_measurement.symbol)

    # X axis
    ax.set_xlim(_datetime_to_ordinal(tsev.event.start_date),
                _datetime_to_ordinal(tsev.event.end_date))
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d\n%H:%M'))
    ax.xaxis.set_major_locator(HourLocator())
    ax.xaxis.set_minor_locator(MinuteLocator(interval=10))
    majticks = ax.xaxis.get_major_ticks()
    for tick in majticks:
        tick.tick2On = tick.label1On = tick.label2On = False
        tick.tick1line.set_marker(TICKDOWN)
    for tick in (majticks[0], majticks[-1]):
        tick.label1On = True
        tick.tick1line.set_markersize(8)
        tick.label1.set_y(-0.08)
        tick.label1.set_fontsize(8)
    for tick in  ax.xaxis.get_minor_ticks():
        tick.tick2On = False
        tick.tick1line.set_marker(TICKDOWN)

    # Finito
    fig.savefig(filename)


def event(request, event_id):
    event_id = int(event_id)
    if event_id<0:
        from django.core.urlresolvers import reverse
        from django.db.models import Max
        from django.http import HttpResponseRedirect
        max_id = models.Event.objects.aggregate(Max('id'))['id__max']
        nid = max_id + 1 + event_id
        return HttpResponseRedirect(reverse('event', args=[nid]))
    ev = get_object_or_404(models.Event, id=event_id)
    _create_contour_map(ev)
    for tsev in ev.timeseriesevent_set.all():
        _create_chart(tsev)
    return render_to_response('rain-event.html', { 'event': ev, 
        'HRAIN_STATIC_CACHE_URL': settings.HRAIN_STATIC_CACHE_URL},
        context_instance=RequestContext(request))
