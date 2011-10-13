from django.views.generic import list_detail
from django.shortcuts import get_object_or_404
from enhydris.contourplot.models import ChartPage, CPoint, OtherPlot
from django.http import (HttpResponse, HttpResponseRedirect,
                            HttpResponseForbidden, Http404)
from enhydris.hcore.views import inc_month, timeseries_data
from enhydris.hcore.models import TimeStep as TTimeStep
from pthelma.cplot import plot_contours
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


def last_update(request, urlcode, **kwargs):
    page = get_object_or_404(ChartPage, url_name = urlcode)
    return HttpResponse(page.get_concurent_timestamp_str(),
                        mimetype='text/plain')


class DummyRequest:
    def __init__(self, method, GET):
        self.method = method
        self.GET = GET


def fetch_value(point, date, secondary=False):
    timeseries = getattr(point, ('timeseries',
                                  'secondary_timeseries')[secondary])
    dummyrequest = DummyRequest('GET', {'object_id': timeseries.id,
                                'date': date.strftime('%Y-%m-%d'),
                                'time': date.strftime('%H:%M'),
                                'last': 'moment', 'exact_datetime': 'true'})
    try:
        v = json.loads(timeseries_data(dummyrequest).content)[u'data'][0][1]
        if v!=u'null':
            v = float(v)
        else:
            v = None
    except:
        v = None
    return v


def format_date(date, format):
    if format!='%l':
        return date.strftime(format)
    else:
        date2 = inc_month(date, 12)
        return '%s-%s'%(date.strftime('%Y'),date2.strftime('%y'),)


def contourpage_detail(request, urlcode, **kwargs):
    kwargs["queryset"] = ChartPage.objects.all()
    page = get_object_or_404(ChartPage, url_name = urlcode)
    object_id = page.id
    large_dimension = page.default_dimension
    (x0, y0, x1, y1) = [getattr(page, x) for x in ('chart_bounds_bl_x', 
                               'chart_bounds_bl_y','chart_bounds_tr_x', 
                                                   'chart_bounds_tr_y')]
    width, height = x1-x0, y1-y0
    small_dimension = int(round(large_dimension*min(height, width)/max(
                                                        height, width)))
    if width>height:
        x_dim, y_dim = large_dimension, small_dimension
    else:
        x_dim, y_dim = small_dimension, large_dimension
    x_thumb = 140
    y_thumb = x_thumb*y_dim/x_dim
    last_update = page.get_concurent_timestamp_str()
    last_update_tstmp = page.get_concurent_timestamp()
    image_filename = page.url_name
    if request.GET.has_key("date") and request.GET['date']:
        datetimestr = request.GET['date']
        datetimefmt = '%Y-%m-%d'
        if request.GET.has_key('time') and request.GET['time']:
            datetimestr = datetimestr + ' '+ request.GET['time']
            datetimefmt = datetimefmt + ' %H:%M'
        try:
            adate = datetime.strptime(datetimestr, datetimefmt)
            last_update_tstmp = page.get_nominal_timestamp(adate)
            last_update = last_update_tstmp.strftime('%Y-%m-%d %H:%M')+\
                          ' (UTC'+"%+03d%02d"%((abs(page.utc_offset_minutes)/60)* \
                               (-1 if page.utc_offset_minutes<0 else 1),
                               (abs(page.utc_offset_minutes)%60),)+')'
            image_filename+= '-'+last_update_tstmp.strftime('%Y%m%d%H%M')
        except ValueError:
            raise Http404
    if page.display_station_values:
        mean_value = 0.0
        count = 0
        points = CPoint.objects.filter(chart_page__id=page.id)
        for point in points:
            point.old_values=[]
            point.value= fetch_value(point, last_update_tstmp)
            if point.value is not None:
                mean_value+=point.value*point.weight
                count+=point.weight
        if count>0:
            mean_value/=count
        atstmp = last_update_tstmp
        old_values_meta=[]
        secondary_timeseries_exist = False
        for it in range(page.display_station_old_values):
            mean_value1 = 0.0
            mean_value2 = 0.0
            count1 = 0
            count2 = 0
            atstmp+= timedelta(minutes=-page.old_values_step_minutes)
            atstmp = inc_month(atstmp, -page.old_values_step_months)
            for point in points:
                if point.secondary_timeseries:
                    v2 = fetch_value(point, atstmp, True)
                    secondary_timeseries_exist = True
                else:
                    v2 = None
                v1 = fetch_value(point, atstmp)
                point.old_values.append({'v1':v1, 'v2':v2})
                if v1 is not None:
                    mean_value1+=v1*point.weight
                    count1+=point.weight
                if v2 is not None:
                    mean_value2+=v2*point.weight
                    count2+=point.weight
            if count1>0:
                mean_value1/=count1
            if count2>0:
                mean_value2/=count2
            old_values_meta.append({'ts':format_date(atstmp,
                                page.old_values_date_format), 
                                    'date':format_date(atstmp,
                                           '%Y-%m-%d'),
                                    'time':format_date(atstmp,
                                           '%H:%M'),
                                    'mv1':mean_value1, 
                                    'mv2':mean_value2})
    other_pages = None
    try:
        other_pages = OtherPlot.objects.filter(page__id=page.id)
    except OtherPlot.DoesNotExist:
        pass
    kwargs["template_name"] = "contours_detail.html"
    kwargs["template_object_name"] = "page"
    kwargs["extra_context"] = {'last_update': last_update,
                               'other_pages': other_pages,
                               'x_dim': x_dim, 'y_dim': y_dim,
                               'x_thumb': x_thumb, 'y_thumb': y_thumb,
                               'image_filename': image_filename,}
    if page.display_station_values:
        kwargs["extra_context"]['points'] = points
        kwargs["extra_context"]['mean_value'] = mean_value
        kwargs["extra_context"]['old_values_meta'] = old_values_meta
        kwargs["extra_context"]['secondary_timeseries_exist'] = \
                                secondary_timeseries_exist
    return list_detail.object_detail(request, object_id = object_id, **kwargs)


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
            page = get_object_or_404(ChartPage, url_name = d['urlcode'])
            filedate = page.get_concurent_timestamp()
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
# The two following lines may be useless and erroneous. Check please.
# Commenting the following two lines, prety sure errors,
# Stefanos 2011-07-18
#    filedate = filedate+timedelta(minutes=page.ts_offset_minutes)
#    filedate = inc_month(filedate, page.ts_offset_months)
    page_id = page.id
    points = CPoint.objects.filter(chart_page=page_id)
    a = []
    s =''
    for point in points:
        (x, y) = point.point.point.transform(page.chart_bounds_srid , clone=True)
        v = fetch_value(point, filedate)
        if v is None:
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
                    'swap_bg_fg', 'compose_alpha', 'compose_offset',
                    'boundary_distance_factor', 'boundary_value',
                    'boundary_mode')
    options = {}
    for item in db_opts_list:
        options[item] = getattr(page, item)
    if page.reverse_color_map:
        options['color_map']+='_r'
    options['backgrounds_path']=settings.CONTOURPLOT_BACKGROUNDS_PATH
    options['chart_large_dimension']=chart_large_dimension
    plot_contours(filename, a, options)
    return filename


def push_image(filename, imgurl):
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


def image_serve(request, imgurl, **kwargs):
    filename = create_contours(imgurl)
    return push_image(filename, imgurl)


def thumb_serve(request, imgurl, **kwargs):
    try:
        file_name, file_ext = imgurl.split('.')
        if file_ext.lower()!='png':
            raise
        img_name, thumb_size = file_name.split('_')
    except:
        raise Http404
    img_filename = create_contours('.'.join((img_name, 'png')))
    actual_imgurl = img_filename.split('/')[-1]
    thumb_url = '_'.join( (actual_imgurl.split('.')[0], thumb_size) )
    thumb_url = '.'.join( (thumb_url, 'png') )
    thumb_filename = os.path.join(settings.CONTOURPLOT_STATIC_CACHE_PATH,
                                  'thumbs', thumb_url)
    if not os.path.exists(os.path.dirname(thumb_filename)):
        os.mkdir(os.path.dirname(thumb_filename))
    from stat import ST_MTIME
    if not os.path.exists(thumb_filename) or \
           os.stat(img_filename)[ST_MTIME] >\
           os.stat(thumb_filename)[ST_MTIME]:
        from PIL import Image
        THUMBNAIL_SIZE = (int(thumb_size), int(thumb_size))
        image = Image.open(img_filename)
        if image.mode not in ('L', 'RGB'): 
            image = image.convert('RGB') 
        image.thumbnail(THUMBNAIL_SIZE, Image.ANTIALIAS)
        image.save(thumb_filename)
    return push_image(thumb_filename, imgurl)
