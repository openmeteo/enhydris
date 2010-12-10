import settings
from django.db import connection
from django.shortcuts import render_to_response

from pthelma.timeseries import Timeseries, identify_events

def index(request):
    ts_list = [Timeseries(id=x) for x in settings.HRAIN_TIMESERIES]
    for x in ts_list:
        x.read_from_db(connection) 
    events = identify_events(ts_list, settings.HRAIN_START_THRESHOLD,
        settings.HRAIN_NTIMESERIES_START_THRESHOLD,
        settings.HRAIN_TIME_SEPARATOR,
        settings.HRAIN_END_THRESHOLD, settings.HRAIN_NTIMESERIES_END_THRESHOLD)
    return render_to_response('rain-index.html', { 'events': events })
