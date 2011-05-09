from django.db import models

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
    class Meta:
        verbose_name = "Entity (point)"
        verbose_name_plural = "Entities (points)"
    def __unicode__(self):
        return self.point.name
