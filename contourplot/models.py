from django.db import models
from datetime import datetime, timedelta
from pytz import utc
from pthelma.timeseries import TimeStep

import enhydris.hcore.models

AVAILABLE_COLORMAPS = ( ('', 'none'),
    ('autumn', 'autumn'), ('bone', 'bone'), ('cool', 'cool'),
    ('copper', 'copper'), ('flag', 'flag'), ('gray', 'gray'),
    ('hot', 'hot'), ('hsv', 'hsv'), ('jet', 'jet'),
    ('pink', 'pink'), ('prism', 'prism'), ('spring', 'spring'),
    ('summer', 'summer'), ('winter', 'winter'),
    ('special', 'special'),)

AVAILABLE_COMPOSE_METHODS = ( ('lighter', 'lighter'),
    ('darker', 'darker'), ('difference', 'difference'),
    ('multiply', 'multiply'), ('screen', 'screen'),
    ('add', 'add'), ('subtract', 'subtract'), ('blend', 'blend'),
    ('composite', 'composite'),)

AVAILABLE_BOUNDARY_MODES = ( (0, 'Constant value on boundary' ),
                             (1, 'Value on boundary is a ratio of the '
                                 'mean value'),)

class ChartPage(models.Model):
    name = models.CharField(max_length=80)
    description = models.TextField(null=False, blank=True)
    url_name = models.CharField(max_length=50, unique=True)
    chart_bounds_bl_x = models.FloatField("Chart bounds bottom left abscissa")
    chart_bounds_bl_y = models.FloatField("Chart bounds bottom left ordinate")
    chart_bounds_tr_x = models.FloatField("Chart bounds top right abscissa")
    chart_bounds_tr_y = models.FloatField("Chart bounds top right ordinate")
    chart_bounds_srid = models.IntegerField(default=2100,
                           help_text='Use a projected - conformal '
                                     'coordinate system such as '
                                     'UTM, with x_scale=y_scale.')
    show_mean_value = models.BooleanField(default=False)
    time_step = models.ForeignKey(enhydris.hcore.models.TimeStep,
                                    default=1)
    ts_offset_minutes = models.IntegerField(default=0)
    ts_offset_months = models.IntegerField(default=0)
    data_available_after_x_minutes = models.IntegerField(default=0)
    utc_offset_minutes = models.IntegerField(default=0)
    draw_markers = models.BooleanField(default=True)
    draw_labels = models.BooleanField(default=True)
    contours_font_size = models.IntegerField(default=8)
    labels_format = models.CharField(max_length=10, default='%1.0f')
    draw_contours = models.BooleanField(default=True)
    labels_font_size = models.IntegerField(default=8)
    color_map = models.CharField(max_length=8, choices=AVAILABLE_COLORMAPS,
                                default='winter')
    reverse_color_map = models.BooleanField(default=True)
    text_color = models.CharField(max_length=12, default='black')
    contours_color = models.CharField(max_length=12, default='red')
    markers_color = models.CharField(max_length=12, default='black')
    markers_style = models.CharField(max_length=3, default='x')
    granularity = models.IntegerField(default=50)
    compose_background = models.BooleanField(default=False)
    background_image = models.CharField(max_length=80, default='')
    mask_image = models.CharField(max_length=80, default='',
                 help_text='Should be specified for composite '
                           'image composition')
    compose_method = models.CharField(max_length=12, 
                     choices=AVAILABLE_COMPOSE_METHODS,
                     default='multiply')
    swap_bg_fg = models.BooleanField(default=False, 
                 verbose_name='Reverse bg fg images',
                 help_text='Reverse the order of background and '
                           'contours images for the image composition')
    compose_alpha = models.FloatField(default=0.5,
                 verbose_name='Alpha or scale parameter',
                 help_text='Used as alpha for blend composition or '
                           'as scale for add or subtract comp.')
    compose_offset = models.FloatField(default=0,
                 help_text='Used only in add or subtract composition mode')
    always_refresh = models.BooleanField(default=False)
    default_dimension = models.IntegerField(default=480)
    side_text = models.TextField(null=False, blank=True)
    boundary_distance_factor = models.FloatField(default=1.0)
    boundary_value = models.FloatField(default=0.0)
    boundary_mode = models.IntegerField(default=0,
                                        choices = AVAILABLE_BOUNDARY_MODES)
    timestamp_notice = models.CharField(max_length=80, null=False,
                                        blank=True)
    up_timestamp = models.BooleanField(default=False,
                  help_text='By default down timestamp is used. '
                            'Use up timestamp for the cases of '
                            'incomplete time intervalas, containing '
                            'current date / time.')
    display_station_values = models.BooleanField(default=False,
                  help_text='Display station values on page')
    display_station_old_values = models.IntegerField(default=0,
                  help_text='Display historical values on page. '
                            'Specify the number of old values.')
    old_values_step_minutes = models.IntegerField(default=0)
    old_values_step_months  = models.IntegerField(default=0)
    old_values_title = models.CharField(max_length=80, blank=True)
    old_values_main_value_title = models.CharField(max_length=40, blank=True)
    old_values_secondary_value_title = models.CharField(max_length=40, blank=True)
    old_values_date_format = models.CharField(max_length=16, blank=True)

    def __unicode__(self):
        return self.name

    def get_concurent_timestamp(self):
        time_step = self.time_step
        now = datetime.now(utc).replace(second=0, microsecond=0, tzinfo=None) 
        now+= timedelta(minutes = self.utc_offset_minutes)
############################
# Maybe nominal_offset should be that of the time_step..
        ts = TimeStep(length_minutes = time_step.length_minutes,
                      length_months = time_step.length_months,
                      nominal_offset = (self.ts_offset_minutes,
                                        self.ts_offset_months))
        tstamp = ts.down(now) if not self.up_timestamp else ts.up(now)
#########WARNING!!! This is a temp work-arround!!! Find a more general ########
#########Solution. Stefanos 2011-05-31  #######################################
        if time_step.length_months>=1:
    		tstamp = ts.previous(tstamp)
###############################################################################
        tstamp2 = tstamp
        if self.up_timestamp: tstamp2 = ts.previous(tstamp2)
        if now-tstamp2<timedelta(minutes=self.data_available_after_x_minutes):
            tstamp = ts.previous(tstamp)
        return tstamp

    def get_concurent_timestamp_str(self):
        return self.get_concurent_timestamp().strftime('%Y-%m-%d %H:%M')+\
                    ' (UTC'+"%+03d%02d"%((abs(self.utc_offset_minutes)/60)* \
                      (-1 if self.utc_offset_minutes<0 else 1),
                      (abs(self.utc_offset_minutes)%60),)+')'

class OtherPlot(models.Model):
    page = models.ForeignKey(ChartPage)
    sequence = models.PositiveSmallIntegerField()
    rpage = models.ForeignKey(ChartPage, related_name="rpage_set")
    def __unicode__(self):
        return str(self.page)
    class Meta:
        ordering = ("page", "sequence")
        unique_together = (("page", "rpage"),
                           ("page", "sequence"))

class CTimeseries(enhydris.hcore.models.Timeseries):
    class Meta:
        proxy = True
        ordering = ["id"]
        verbose_name = "Timeseries"
    def __unicode__(self):
        return '%d (id) - %s'%(self.id, self.name)

class CPoint(models.Model):
    point = models.ForeignKey(enhydris.hcore.models.Gpoint,
                                   related_name="cpoint_gpoint")
    timeseries = models.ForeignKey(CTimeseries,
                                   related_name='variable_timeseries')
    secondary_timeseries = models.ForeignKey(CTimeseries,
                                   null=True, blank=True,
                                   related_name="variable_2nd_Timeseries")
    chart_page = models.ForeignKey(ChartPage)
    weight = models.FloatField(default=1)
    display_name = models.CharField(max_length=80, blank=True)
    class Meta:
        verbose_name = "Entity (point)"
        verbose_name_plural = "Entities (points)"
    def __unicode__(self):
        return self.point.name
