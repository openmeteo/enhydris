from enhydris.contourplot.models import *
from django.contrib import admin

class CPointInline(admin.TabularInline):
    model = CPoint
    extra = 1

class OtherPageInline(admin.TabularInline):
    model = OtherPlot
    fk_name = 'page'
    raw_id_fields = ('rpage',)

class ChartPageAdmin(admin.ModelAdmin):
    inlines = [CPointInline, OtherPageInline]
    fieldsets = ( (None, {'fields': (('name', 'url_name', 'description'),
                    ('chart_bounds_bl_x', 'chart_bounds_bl_y',
                     'chart_bounds_tr_x', 'chart_bounds_tr_y',
                     'chart_bounds_srid'),
                    ('show_mean_value'),
                    ('utc_offset_minutes', 'time_step', 'ts_offset_minutes', 
                     'ts_offset_months', 'data_available_after_x_minutes'),
                    ('draw_contours', 'contours_font_size', 'contours_color'),
                    ('draw_labels', 'labels_font_size', 'labels_format'),
                    ('draw_markers', 'markers_style', 'markers_color'),
                    ('color_map', 'reverse_color_map'),
                    ('granularity'),
                    ('compose_background', 'background_image',
                     'compose_method', 'swap_bg_fg'),
                    ('compose_alpha', 'compose_offset', 'mask_image'),
                    ('always_refresh', 'default_dimension'),
                    ('side_text', 'timestamp_notice'),
                    ('boundary_distance_factor', 'boundary_value',
                     'boundary_mode'),
                    ('up_timestamp','display_station_values'),
                )}),)

    list_display = ('id', 'name', 'url_name')

class CPointAdmin(admin.ModelAdmin):
    fieldsets = ( (None, {'fields': (('display_name', 'chart_page',
                   'point', 'timeseries', 'weight'),
                   )
                   }),)

    list_display = ('id', 'display_name', 'chart_page')

admin.site.register(CPoint, CPointAdmin)
admin.site.register(ChartPage, ChartPageAdmin)
