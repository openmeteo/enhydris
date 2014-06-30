from django.db import models

import enhydris.hcore.models

AVAILABLE_METHODS = ( ('HeatIndex', 'Heat index calculation'),
                      ('SSI', 'SSI calculation'),
                      ('IDM_monthly', 'Martone index (monthly)'),
                      ('IDM_annual', 'Martone index (annual)'),
                      ('Aggregation', 'Time series aggregation'),
                      ('Tsupdate', 'Time series cache update'),
                      ('BaromFormula','Barometric formula'),
                      ('Interpolation', 'Curve interpolation'),
                      ('OneStepDiff', 'One step difference'),
                    )

AVAILABLE_TS_SPECS = ( ('irrelevant', 'Irrelevant'),
                       ('temp', 'Temperature'),
                       ('rh', 'Relative Humidity'),
                       ('precip', 'Precipitation'),
                       ('press', 'Barometric pressure'),
                     )

AVAILABLE_CURVE_METHODS = ( ('SingleCurve', 'Single interpol. curve'),
                            ('StageDischargeMulti','Stage discharge '
                                                   'multiple curves'), 
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

class CGeneric(enhydris.hcore.models.GentityGenericData):
    class Meta:
        proxy = True
        ordering = ["id"]
        verbose_name = "Curves"
    def __unicode__(self):
        return "%d (id) - %s"%(self.id, self.descr)

class ProcessUnit(models.Model):
    name = models.CharField(max_length=60)
    batch = models.ForeignKey(ProcessBatch)
    method = models.CharField(max_length=16, 
                              choices = AVAILABLE_METHODS)
    interpol_method = models.CharField(max_length=32,
                              choices = AVAILABLE_CURVE_METHODS,
                              default='', blank=True,
                       help_text= 'Set the desired interpolation '
                                  'method, has meaning only if '
                                  'method is "Curve Interpolation"',
                       verbose_name= 'Interpolation method' )
    order = models.IntegerField(default=0, 
                       help_text= 'Order of execution, '
                                  'Starts from smaller values '
                                  'going to larger')
    independent_column = models.IntegerField(default=0,
                       help_text= 'Independent values column')
    dependent_column = models.IntegerField(default=1,
                       help_text= 'Dependent values column')
    append_only = models.BooleanField(default = True)
    output_timeseries = models.ForeignKey(CTimeseries)
    curve = models.ForeignKey(CGeneric, null=True, blank=True)
    aggregation_missing_allowed = models.FloatField(default=0.0,
                       help_text= 'Has meaning only if '
                                  'method = Aggregation, '
                                  'or Altitude diff if '
                                  'barometric formula. '
                                  'Another alternative use: '
                                  'Offset in curve interpolation, '
                                  'if Single curve is considered',
                       verbose_name= 'Aggregation missing allowed '
                                     'or altitude diff or offset')
    aggregation_missing_flag = models.CharField(max_length=16,
                               default='MISSING',
                               help_text= 'Has meaning only if '
                                          'method = Aggregation')
    aggregation_last_incomplete = models.BooleanField(default = False,
                     help_text= 'Last aggregated time series record '
                                'could be derived from an incomplete '
                                'month, or year etc. Alternative use: '
                                'Set logarithmic curve if method is '
                                'Curve interpolation and Single '
                                'curve is considered.',
                     verbose_name = 'Allow last record of aggregation '
                                    'incomplete or logarithmic')
    aggregation_all_incomplete = models.BooleanField(default = False,
                     help_text= 'Last aggregated time series record '
                                'could be derived from an incomplete '
                                'month, or year etc. Then all '
                                'aggregated records are incomplete '
                                'to the same position',
                     verbose_name = 'Calculate all records incomplete'
                                    'to the same day number as the '
                                    'last record')

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
