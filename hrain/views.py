from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.conf import settings
from enhydris.hrain import models
from pthelma.timeseries import Timeseries


def index(request):
    eventgroups = []
    year = 0
    for e in models.Event.objects.order_by('id').all():
        if e.start_date.year != year:
            year = e.start_date.year
            eventgroups.append({ 'year': year, 'events': [] })
        eventgroups[-1]['events'].append(e)
    return render_to_response('rain-index.html',
                                    { 'eventgroups': eventgroups },
                                    context_instance=RequestContext(request))


def _datetime_to_ordinal(dt):
    return dt.toordinal() + dt.hour/24.0 + dt.minute/1440.0

import matplotlib
matplotlib.use('Agg')

def _create_chart(tsev):
    """Check whether a chart for specified event and timeseries exists, and
    if it doesn't, create it."""
    import matplotlib.pyplot as plt
    from matplotlib.dates import DateFormatter, HourLocator, MinuteLocator
    from matplotlib.lines import TICKDOWN
    from matplotlib.figure import SubplotParams

    from StringIO import StringIO
    import os.path

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
    ev = get_object_or_404(models.Event, id=event_id)
    for tsev in ev.timeseriesevent_set.all():
        _create_chart(tsev)
    return render_to_response('rain-event.html', { 'event': ev, 
        'HRAIN_STATIC_CACHE_URL': settings.HRAIN_STATIC_CACHE_URL},
        context_instance=RequestContext(request))
