from StringIO import StringIO
import os.path

from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, TemplateDoesNotExist
from django.conf import settings
from django.http import Http404, HttpResponse

from pthelma.timeseries import Timeseries
from pthelma.cplot import plot_contours
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
        if tsev.total_precipitation is None: continue
        gp = tsev.timeseries.gentity.gpoint
        (x, y) = gp.point.transform(settings.HRAIN_CONTOUR_SRID, clone=True)
        a.append((x, y, tsev.total_precipitation, gp.name))

    (x0, y0, x1, y1) = [float(x) for x in settings.HRAIN_CONTOUR_CHART_BOUNDS]
    (backgrounds_path, background_filename, mask_filename) = (None,
                                                              None, None)
    if hasattr(settings, HRAIN_BACKGROUNDS_PATH):
        backgrounds_path = settings.HRAIN_BACKGROUNDS_PATH
        if hasattr(settings, HRAIN_BACKGROUND_IMAGE):
            background_filename = os.path.join(backgrounds_path,
                                               HRAIN_BACKGROUND_IMAGE)
        if hasattr(settings, HRAIN_MASK_IMAGE):
            mask_filename = os.path.join(backgrounds_path,
                                         HRAIN_MASK_IMAGE)
    options ={'contours_font_size': 10, 'labels_format': '%1.0f',
              'draw_contours': True, 'color_map': 'winter_r',
              'labels_font_size': 10, 'text_color': 'black',
              'contours_color': 'red', 'draw_labels': True,
              'markers_color': 'black', 'markers_style': '+',
              'draw_markers': True, 'granularity': 100,
              'chart_bounds_bl_x': x0, 'chart_bounds_bl_y': y0,
              'chart_bounds_tr_x': x1, 'chart_bounds_tr_y': y1,
              'chart_bounds_srid': settings.HRAIN_CONTOUR_SRID,
              'compose_background': (background_filename is not None),
              'background_image': background_filename,
              'mask_image': mask_filename,
              'compose_method': ('composite' if mask_filename else 'multiply'),
              'swap_bg_fg': False, 'compose_alpha': 0.5, 
              'compose_offset': 0, 'chart_large_dimension': 400,
              'backgrounds_path': backgrounds_path }
    plot_contours(filename, a, options)


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
    # FIXME: The following line hangs and eternally increases memory
    # consumption in the (very unlikely) case that the event consists of only
    # one time stamp.
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


def _get_monthly_surface_timeseries():
    from datetime import datetime

    # Create a monthly timeseries spanning all event range, with all zeros 
    result = Timeseries()
    s = models.Event.objects.order_by('start_date')[0].start_date
    e = models.Event.objects.order_by('-end_date')[0].end_date
    start = datetime(s.year, s.month, 1)
    end = datetime(e.year, e.month, 1)
    d = start
    while d<=end:
        result[d] = 0.0
        m, y = d.month, d.year
        m += 1
        if m>12:
            m = 1
            y += 1
        d = datetime(y, m, 1)

    # Fill it in
    for ev in models.Event.objects.all():
        s = ev.start_date
        e = ev.end_date
        depth = ev.average_precipitation_depth
        if s.month == e.month:
            result[datetime(s.year, s.month, 1)] += depth
        else:
            s_part = (datetime(e.year, e.month, 1) - s).seconds
            e_part = (e - datetime(e.year, e.month, 1)).seconds
            result[datetime(s.year, s.month, 1)] += depth*s_part/(s_part+e_part)
            result[datetime(e.year, e.month, 1)] += depth*e_part/(s_part+e_part)

    # Finito
    return result


def event(request, event_id):
    event_id = int(event_id)
    if event_id<0:
        from django.core.urlresolvers import reverse
        from django.db.models import Max
        from django.http import HttpResponseRedirect
        max_id = models.Event.objects.aggregate(Max('id'))['id__max']
        nid = max_id + 1 + event_id
        target_url = reverse('event', args=[nid])
        g = request.GET
        if len(g):
            target_url += '?' + '&'.join(['%s=%s' % (x, g[x]) for x in g])
        return HttpResponseRedirect(target_url)
    ev = get_object_or_404(models.Event, id=event_id)
    _create_contour_map(ev)
    for tsev in ev.timeseriesevent_set.all():
        _create_chart(tsev)
    t = request.GET.get('template', None)
    template_name = t if t and t.startswith('rain-event') else 'rain-event.html'
    try:
        from django.template.loader import get_template
        template = get_template(template_name)
    except TemplateDoesNotExist:
        template = get_template('rain-event.html')
    return HttpResponse(template.render(RequestContext(request, { 'event': ev, 
            'event_with_max_average': models.Event.objects.order_by(
                                            '-average_precipitation_depth')[0],
            'event_with_max_max': models.Event.objects.order_by(
                                            '-max_measurement')[0],
            'monthly_surface_timeseries': _get_monthly_surface_timeseries(),
            'HRAIN_STATIC_CACHE_URL': settings.HRAIN_STATIC_CACHE_URL})))
            # FIXME: must create db indexes for average_precipitation_depth
            # and max_measurement
