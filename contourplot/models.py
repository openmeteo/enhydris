from django.db import models

import enhydris.hcore.models

AVAILABLE_TIMESTEPS = (
    (1, 'Ten-minute'),
    (2, 'Hourly'),
    (3, 'Daily'),
    (4, 'Monthly'),
    (5, 'Annual'),
)

class ChartPage(models.Model):
    name = models.CharField(max_length=80)
    description = models.TextField(null=False, blank=True)
    url_name = models.CharField(max_length=50, unique=True)
    chart_bounds_bl_x = models.FloatField("Chart bounds bottom left abscissa")
    chart_bounds_bl_y = models.FloatField("Chart bounds bottom left ordinate")
    chart_bounds_tr_x = models.FloatField("Chart bounds top right abscissa")
    chart_bounds_tr_y = models.FloatField("Chart bounds top right ordinate")
    chart_bounds_srid = models.IntegerField(default=4326)
    show_mean_value = models.BooleanField(default=False)
    time_step = models.IntegerField(choices = AVAILABLE_TIMESTEPS,
                                    default=3)
    ts_offset_minutes = models.IntegerField(default=0)
    ts_offset_months = models.IntegerField(default=0)
    def __unicode__(self):
        return self.name

class CTimeseries(enhydris.hcore.models.Timeseries):
    class Meta:
        proxy = True
        ordering = ["id"]
        verbose_name = "Timeseries"
    def __unicode__(self):
        return 'id:%d - %s'%(self.id, self.name)

class CPoint(models.Model):
    point = models.ForeignKey(enhydris.hcore.models.Gpoint,
                                   related_name="cpoint_gpoint")
    timeseries = models.ForeignKey(CTimeseries,
                                   related_name='variable_timeseries')
    chart_page = models.ForeignKey(ChartPage)
    weight = models.FloatField(default=1)
    display_name = models.CharField(max_length=80, blank=True)
    display_point_on_map = models.BooleanField(default=True)
    display_point_label = models.BooleanField(default=True)
    class Meta:
        verbose_name = "Entity (point)"
        verbose_name_plural = "Entities (points)"
    def __unicode__(self):
        return self.point.name
