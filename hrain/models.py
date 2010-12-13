from django.db import models, connection
from django.conf import settings


class Event(models.Model):
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def __unicode__(self):
        return "%s - %s" % (self.start_date.isoformat(),
                                                self.end_date.isoformat())


def refresh_events():
    from pthelma.timeseries import Timeseries, identify_events
    ts_list = [Timeseries(id=x) for x in settings.HRAIN_TIMESERIES]
    for x in ts_list:
        x.read_from_db(connection) 
    events = identify_events(ts_list, settings.HRAIN_START_THRESHOLD,
        settings.HRAIN_NTIMESERIES_START_THRESHOLD,
        settings.HRAIN_TIME_SEPARATOR,
        settings.HRAIN_END_THRESHOLD, settings.HRAIN_NTIMESERIES_END_THRESHOLD)
    Event.objects.all().delete()
    for event in events:
        e = Event(start_date=event[0], end_date=event[1])
        e.save()
