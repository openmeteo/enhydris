from django.db import models, connection
from django.conf import settings

import enhydris.hcore.models

class Event(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def __unicode__(self):
        return "%s - %s" % (self.start_date.isoformat(),
                                                self.end_date.isoformat())


class TimeseriesEvent(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    event = models.ForeignKey(Event)
    timeseries = models.ForeignKey(enhydris.hcore.models.Timeseries)
    total_precipitation = models.FloatField(null=True)
    data = models.TextField(blank=True)


def refresh_events():
    from pthelma.timeseries import Timeseries, identify_events
    from StringIO import StringIO
    import fpconst
    ts_list = [Timeseries(id=x) for x in settings.HRAIN_TIMESERIES]
    for x in ts_list:
        x.read_from_db(connection) 
    events = identify_events(ts_list, settings.HRAIN_START_THRESHOLD,
        settings.HRAIN_NTIMESERIES_START_THRESHOLD,
        settings.HRAIN_TIME_SEPARATOR,
        settings.HRAIN_END_THRESHOLD, settings.HRAIN_NTIMESERIES_END_THRESHOLD)
    Event.objects.all().delete()
    fp = StringIO('')
    teid = 1
    for i, event in enumerate(events, start=1):
        e = Event(id=i, start_date=event[0], end_date=event[1])
        e.save()
        for x in ts_list:
            total=x.sum(e.start_date, e.end_date)
            if fpconst.isNaN(total): total = None
            fp.truncate(0)
            x.write(fp, e.start_date, e.end_date)
            te = TimeseriesEvent(id=teid, event=e,
                       timeseries=enhydris.hcore.models.Timeseries.objects.get(
                       id=x.id), total_precipitation=total, data=fp.getvalue())
            te.save()
            teid += 1
