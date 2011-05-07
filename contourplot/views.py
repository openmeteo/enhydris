from django.views.generic import list_detail
from django.shortcuts import get_object_or_404
from enhydris.contourplot.models import ChartPage, CPoint
from django.http import (HttpResponse, HttpResponseRedirect,
                            HttpResponseForbidden, Http404)
from enhydris.hcore.views import inc_month, timeseries_data
from enhydris.contourplot.cplot import plot_contours
from datetime import datetime,timedelta
from django.core.servers.basehttp import FileWrapper
from django.conf import settings
import mimetypes
import os
try:
    import json
except ImportError:
    import simplejson as json


def contourpage_detail(request, urlcode, **kwargs):
    return HttpResponse('Mr. John Foufotos page: '+urlcode, mimetype='text/plain')


class DummyRequest:
    def __init__(self, method, GET):
        self.method = method
        self.GET = GET


def create_contours(imgurl):
    filename = os.path.join(settings.CONTOURPLOT_STATIC_CACHE_PATH, imgurl)
    try:
        file_name, file_ext = imgurl.split('.')
        if file_ext.lower()!='png':
            raise
        urlcode, datestr, chart_large_dimension = file_name.split('-')
        filedate = datetime(*map(lambda x:int(datestr[x[0]:x[1]]), ((0,4),(4,6),(6,8),(8,10),(10,12))))
    except:
        raise Http404
    page = get_object_or_404(ChartPage, url_name = urlcode)
    if not (page.always_refresh or not os.path.exists(filename)):
        return filename
    filedate = filedate+timedelta(minutes=page.ts_offset_minutes)
    filedate = inc_month(filedate, page.ts_offset_months)
    page_id = page.id
    points = CPoint.objects.filter(chart_page=page_id)
    a = []
    s =''
    for point in points:
        (x, y) = point.point.point.transform(page.chart_bounds_srid , clone=True)
        dummyrequest = DummyRequest('GET', {'object_id': point.timeseries.id,
                                    'date': filedate.strftime('%Y-%m-%d'),
                                    'time': filedate.strftime('%H:%M'),
                                    'last': 'moment', 'exact': 'true'})
        v = json.loads(timeseries_data(dummyrequest).content)[u'data'][0][1]
        if v!=u'null':
            v = float(v)
        else:
            continue
        a.append((x, y, v, point.display_name))
    db_opts_list = ('contours_font_size', 'labels_format', 'draw_contours',
                    'color_map', 'labels_font_size', 'text_color',
                    'contours_color', 'draw_labels', 'markers_color',
                    'markers_style', 'draw_markers', 'granularity',
                    'chart_bounds_bl_x', 'chart_bounds_bl_y',
                    'chart_bounds_tr_x', 'chart_bounds_tr_y',
                    'chart_bounds_srid', 'compose_background',
                    'background_image', 'mask_image', 'compose_method',
                    'swap_bg_fg', 'compose_alpha', 'compose_offset')
    options = {}
    for item in db_opts_list:
        options[item] = getattr(page, item)
    if page.reverse_color_map:
        options['color_map']+='_r'
    options['chart_large_dimension']=chart_large_dimension
    plot_contours(filename, a, options)
    return filename


def image_serve(request, imgurl, **kwargs):
    filename = create_contours(imgurl)
    try:
        wrapper  = FileWrapper(open(filename))
    except:
        raise Http404
    response = HttpResponse(content_type='image/png')
    response['Content-Length'] = os.path.getsize(filename)
    response['Content-Disposition'] = "inline; filename=%s"%imgurl
    for chunk in wrapper:
        response.write(chunk)
    return response

