from django.db import models

import enhydris.hcore.models

class ChartPage(models.Model):
    name = models.CharField(max_length=80)
    description = models.TextField()
    url_name = models.CharField(max_length=50, unique=True)
    option_daily = models.BooleanField(default=True)
    option_weekly = models.BooleanField(default=False)
    option_monthly = models.BooleanField(default=False)
    option_annual = models.BooleanField(default=False)
    def __unicode__(self):
        return self.name

class Chart(models.Model):
    name = models.CharField(max_length=80)
    order = models.IntegerField()
    can_zoom = models.BooleanField(default=False)
    display_min = models.BooleanField(default=False)
    display_max = models.BooleanField(default=False)
    display_avg = models.BooleanField(default=False)
    display_sum = models.BooleanField(default=False)
    display_lastvalue = models.BooleanField(default=False)
    chart_page = models.ForeignKey(ChartPage,
                                   related_name='chart_page')
    def __unicode__(self):
        return self.name
    #ToDo: Add axes formating - overrides

class CTimeseries(enhydris.hcore.models.Timeseries):
    class Meta:
        proxy = True
        ordering = ["id"]
    def __unicode__(self):
        return 'id:%d - %s'%(self.id, self.name)

class Variable(models.Model):
    name = models.CharField(max_length=80, blank=True)
    timeseries = models.ForeignKey(CTimeseries,
                                   related_name='variable_timeseries')
    chart = models.ForeignKey(Chart)
    is_main_variable = models.BooleanField(default=True)
    link_to_timeseries = models.BooleanField(default=True)
    def __unicode__(self):
        return self.name
    #ToDo: Add formating options



