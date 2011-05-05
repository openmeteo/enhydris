from django.views.generic import list_detail
from django.shortcuts import get_object_or_404
from enhydris.contourplot.models import ChartPage, CPoint
from django.http import (HttpResponse, HttpResponseRedirect,
                            HttpResponseForbidden, Http404)
from enhydris.hcore.views import inc_month, timeseries_data
from datetime import datetime,timedelta
from django.core.servers.basehttp import FileWrapper
from django.conf import settings
import mimetypes
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm


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
    from scipy.interpolate import Rbf
    import numpy as np
    filename = os.path.join(settings.CONTOURPLOT_STATIC_CACHE_PATH, imgurl)
    try:
        file_name, file_ext = imgurl.split('.')
        if file_ext.lower()!='png':
            raise
        urlcode, datestr, img_width, img_height = file_name.split('-')
        filedate = datetime(*map(lambda x:int(datestr[x[0]:x[1]]), ((0,4),(4,6),(6,8),(8,10),(10,12))))
    except:
        raise Http404
    page = get_object_or_404(ChartPage, url_name = urlcode)
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
    # Get the grid parameters
    GRANULARITY=100
    (x0, y0, x1, y1) = (page.chart_bounds_bl_x, page.chart_bounds_bl_y,
                        page.chart_bounds_tr_x, page.chart_bounds_tr_y)
    dx, dy = (x1-x0)/GRANULARITY, (y1-y0)/GRANULARITY
    width, height = x1-x0, y1-y0

    # If we just interpolate, then the contours can be bad. What we actually
    # need to do is to tell the interpolator that far away the rainfall becomes
    # zero. So we actually work on a grid that is larger (three times larger),
    # we define rainfall at the edges as zero, we interpolate in there and
    # calculate the contours, and we crop it so that only its middle part is
    # shown. We call this grid the "greater" grid, so we suffix variables with
    # "gr" when they refer to it.
    xgr0, ygr0, xgr1, ygr1 = (x0-width, y0-height, x1+width, y1+height)
    a.append((xgr0, ygr0, 0.0, 'virtual'))
    a.append((xgr1, ygr0, 0.0, 'virtual'))
    a.append((xgr0, ygr1, 0.0, 'virtual'))
    a.append((xgr1, ygr1, 0.0, 'virtual'))
    a.append((xgr0+width/2, ygr0, 0.0, 'virtual'))
    a.append((xgr0+width/2, ygr1, 0.0, 'virtual'))
    a.append((xgr0, ygr0+height/2, 0.0, 'virtual'))
    a.append((xgr1, ygr0+height/2, 0.0, 'virtual'))

    # Now interpolate
    x = [i[0] for i in a]
    y = [i[1] for i in a]
    z = [i[2] for i in a]
    rbfi = Rbf(x, y, z, function='linear')
    xx = np.arange(xgr0, xgr1+dx, dx)
    yy = np.arange(ygr0, ygr1+dy, dy)
    zz = np.empty([3*GRANULARITY+1, 3*GRANULARITY+1])
    for i in xrange(0, 3*GRANULARITY):
        for j in xrange(0, 3*GRANULARITY):
            zz[j][i] = rbfi(xx[i], yy[j])
    # Crop
    zz = zz[GRANULARITY:2*GRANULARITY+1, GRANULARITY:2*GRANULARITY+1]

    # Create the chart
    chart_large_dimension = 400 # pixels
    chart_small_dimension = chart_large_dimension*min(y1-y0, x1-x0)/max(
                                                                y1-y0, x1-x0)
    if x1-x0>y1-y0:
        x_dim, y_dim = chart_large_dimension, chart_small_dimension
    else:
        x_dim, y_dim = chart_small_dimension, chart_large_dimension
    fig = plt.figure(figsize=(x_dim/96.0, y_dim/96.0), dpi=96)
    ax = plt.axes([0.0, 0.0, 1.0, 1.0]) # Axes should occupy no space
    ax.set_xticks([])
    ax.set_yticks([])
    plt.axis('off')
    for x, y, z, name in a:
        if name=='virtual': continue
        plt.plot(x, y, marker='x', linestyle='None', color='black')
        plt.text(x, y, name, color='black')
    im = plt.imshow(zz, interpolation='bilinear', origin='lower',
        cmap=cm.winter_r, extent=(x0, x1, y0, y1))
    cs = plt.contour(zz, extent=(x0, x1, y0, y1), colors="red")
    plt.clabel(cs, inline=1, fontsize=10, fmt="%1.0f")

    fig.savefig(filename)



def image_serve(request, imgurl, **kwargs):
    filename = os.path.join(settings.CONTOURPLOT_STATIC_CACHE_PATH, imgurl)
    if not os.path.exists(filename):
        create_contours(imgurl)
    try:
        wrapper  = FileWrapper(open(filename))
    except:
        raise Http404
    content_type = mimetypes.guess_type(filename)[0]
    response = HttpResponse(content_type='image/png')
    response['Content-Length'] = os.path.getsize(filename)
    response['Content-Disposition'] = "attachment; filename=%s"%imgurl
    for chunk in wrapper:
        response.write(chunk)
    return response


