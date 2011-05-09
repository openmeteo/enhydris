from django.views.generic import list_detail
from django.shortcuts import get_object_or_404
from enhydris.contourplot.models import ChartPage, CPoint
from django.http import (HttpResponse, HttpResponseRedirect,
                            HttpResponseForbidden, Http404)
from enhydris.hcore.views import inc_month, timeseries_data
from enhydris.hcore.models import TimeStep as TTimeStep
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
from pthelma.timeseries import TimeStep
from datetime import datetime, timedelta
from pytz import utc


def get_concurent_timestamp(urlcode):
    page = get_object_or_404(ChartPage, url_name = urlcode)
    time_step = page.time_step
    now = datetime.now(utc).replace(second=0, microsecond=0, tzinfo=None) 
    now+= timedelta(minutes = page.utc_offset_minutes)
    ts = TimeStep(length_minutes = time_step.length_minutes,
                  length_months = time_step.length_months,
                  nominal_offset = (page.ts_offset_minutes,
                                    page.ts_offset_months))
    tstamp = ts.down(now)
    if now-tstamp<timedelta(minutes=page.data_available_after_x_minutes):
        tstamp = ts.previous(tstamp)
    return tstamp


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
        file_elements = file_name.split('-')
        file_elements_count = len(file_elements)
        if file_elements_count not in range(1,4):
            raise
        d = {'datestr': None, 'large_dimension': None}
        d['urlcode'] = file_elements[0]
        for i in range(1, file_elements_count):
            if len(file_elements[i])==12:
                d['datestr'] = file_elements[i]
            else:
                d['large_dimension'] = file_elements[i]
        if not d['datestr']:
            filedate = get_concurent_timestamp(d['urlcode'])
            d['datestr'] = filedate.strftime('%Y%m%d%H%M')
        else:
            filedate = datetime(*map(lambda x:int(d['datestr'][x[0]:x[1]]), ((0,4),(4,6),(6,8),(8,10),(10,12))))
    except:
        raise Http404
    urlcode = d['urlcode']
    datestr = d['datestr']
    page = get_object_or_404(ChartPage, url_name = urlcode)
    if not d['large_dimension']:
        chart_large_dimension = str(page.default_dimension)
    else:
        chart_large_dimension = d['large_dimension']
    filename = os.path.join(settings.CONTOURPLOT_STATIC_CACHE_PATH,
               '.'.join(('-'.join((urlcode, datestr,
                         chart_large_dimension)),'png')))
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
                                    'last': 'moment', 'exact_datetime': 'true'})
        try:
            v = json.loads(timeseries_data(dummyrequest).content)[u'data'][0][1]
            if v!=u'null':
                v = float(v)
            else:
                continue
        except:
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

