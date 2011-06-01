from django.db import models

import enhydris.hcore.models

AVAILABLE_METHODS = ( ('HeatIndex', 'Heat index calculation'),
                      ('SSI', 'SSI calculation'),
                      ('IDM_monthly', 'Martone index (monthly)'),
                      ('IDM_annual', 'Martone index (annual)'),
                      ('Aggregation', 'Time series aggregation'),
                      ('Tsupdate', 'Time series cache update'),
                    )

AVAILABLE_TS_SPECS = ( ('irrelevant', 'Irrelevant'),
                       ('temp', 'Temperature'),
                       ('rh', 'Relative Humidity'),
                       ('precip', 'Precipitation'),
                     )


class ProcessBatch(models.Model):
    name = models.CharField(max_length=80)
    description = models.TextField(null=False, blank=True)
    unique_name = models.CharField(max_length=50, unique=True)
    def __unicode__(self):
        return self.name


class CTimeseries(enhydris.hcore.models.Timeseries):
    class Meta:
        proxy = True
        ordering = ["id"]
        verbose_name = "Timeseries"
    def __unicode__(self):
        return '%d (id) - %s'%(self.id, self.name)


class ProcessUnit(models.Model):
    name = models.CharField(max_length=60)
    batch = models.ForeignKey(ProcessBatch)
    method = models.CharField(max_length=16, 
                              choices = AVAILABLE_METHODS)
    order = models.IntegerField(default=0, 
                               help_text= 'Order of execution, '
                                          'Starts from smaller values '
                                          'going to larger')
    append_only = models.BooleanField(default = True)
    output_timeseries = models.ForeignKey(CTimeseries)
    aggregation_missing_allowed = models.FloatField(default=0.0,
                               help_text= 'Has meaning only if '
                                          'method = Aggregation')
    aggregation_missing_flag = models.CharField(max_length=16,
                               default='MISSING',
                               help_text= 'Has meaning only if '
                                          'method = Aggregation')
    def __unicode__(self):
        return '%s - %s - %s'%(unicode(self.batch), self.method,
                               self.name)


class ProcessInputVariable(models.Model):
    process_unit = models.ForeignKey(ProcessUnit)
    spec = models.CharField(max_length=15, choices =
                             AVAILABLE_TS_SPECS)
    timeseries = models.ForeignKey(CTimeseries)
    def __unicode__(self):
        return '%s - %s'%(unicode(self.process_unit),
                                    self.spec)
