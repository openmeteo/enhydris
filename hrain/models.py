from django.db import models, connection
from django.conf import settings

import enhydris.hcore.models

class Event(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    max_measurement = models.FloatField()
    average_precipitation_depth = models.FloatField()

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
    from glob import glob
    import os
    import os.path

    ts_list = [(Timeseries(id=x[0]), x[1]) for x in settings.HRAIN_TIMESERIES]
    for x in ts_list:
        x[0].read_from_db(connection) 
    events = identify_events([x[0] for x in ts_list],
        settings.HRAIN_START_THRESHOLD,
        settings.HRAIN_NTIMESERIES_START_THRESHOLD,
        settings.HRAIN_TIME_SEPARATOR,
        settings.HRAIN_END_THRESHOLD, settings.HRAIN_NTIMESERIES_END_THRESHOLD)
    Event.objects.all().delete()
    fp = StringIO('')
    teid = 1
    for i, event in enumerate(events, start=1):
        e = Event(id=i, start_date=event[0], end_date=event[1],
                              max_measurement=0, average_precipitation_depth=0)
        e.save()
        weighted_total = 0.0
        weighted_divider = 0.0
        for x in ts_list:
            total=x[0].sum(e.start_date, e.end_date)
            e.max_measurement = max(e.max_measurement,
                                            x[0].max(e.start_date, e.end_date))
            if fpconst.isNaN(total):
                total = None
            else:
                weighted_total += total
                weighted_divider += x[1]
            fp.truncate(0)
            x[0].write(fp, e.start_date, e.end_date)
            te = TimeseriesEvent(id=teid, event=e,
                       timeseries=enhydris.hcore.models.Timeseries.objects.get(
                       id=x[0].id), total_precipitation=total,
                       data=fp.getvalue())
            te.save()
            teid += 1
        e.average_precipitation_depth += weighted_total/weighted_divider
        e.save()    # Save max_measurement and average_precipitation_depth
    for path in glob(os.path.join(settings.HRAIN_STATIC_CACHE_PATH, 'hrain*')):
        os.unlink(path)
