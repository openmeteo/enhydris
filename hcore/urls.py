from django.conf import settings
from django.conf.urls.defaults import *
from django.http import Http404
from django.views.generic import list_detail

from enhydris.hcore import views
from enhydris.hcore.models import (Instrument, Timeseries, Station)

instruments = {'queryset': Instrument.objects.all(),
               'template_object_name': 'instrument',}

timeseries = {'queryset': Timeseries.objects.all(),
              'template_object_name': 'timeseries',}

stations = {'queryset': Station.objects.all(),
            'template_object_name': 'station',}

urlpatterns = patterns('',
    (r'^$', views.index, {}, 'index'),

    (r'^stations/l/$',
     views.station_list, stations, 'station_list'),

    (r'^stations/info/$',
     views.station_info, {}, 'station_info'),

    (r'^stations/d/(?P<object_id>\d+)/$',
     views.station_detail, stations, 'station_detail'),

    (r'^map/$',
        views.map_view, stations , 'map_view'),

    (r'^get_subdivision/(?P<division_id>\d+)/$',
     views.get_subdivision, {}, 'get_subdivision'),

    (r'^instruments/d/(?P<object_id>\d+)/$',
     views.instrument_detail, instruments, 'instrument_detail'),

    (r'^timeseries/d/(?P<object_id>\d+)/$',
     views.timeseries_detail, timeseries, 'timeseries_detail'),

    (r'^timeseries/data/$',
     views.timeseries_data, {}, 'timeseries_data'),

    (r'^timeseries/d/(?P<object_id>\d+)/download/$',
     views.download_timeseries, {}, 'timeseries_text'),

    (r'^gentityfile/(?P<gf_id>\d+)/download/$',
     views.download_gentityfile, {}, 'gentityfile_dl'),

    (r'^site_media/'+settings.GENTITYFILE_DIR+'/.*$',
     views.protect_gentityfile, {}, ''),
)

# If users can modify content, enable these views
if settings.USERS_CAN_ADD_CONTENT:
    urlpatterns += patterns('',
    (r'^stations/edit/(?P<station_id>\d+)/$',
     views.station_edit, {} , 'station_edit'),

    (r'^stations/add/$',
     views.station_add, {}, 'station_add'),

    (r'^stations/delete/(?P<station_id>\d+)/$',
     views.station_delete, {} , 'station_delete'),

    (r'^timeseries/edit/(?P<timeseries_id>\d+)/$',
     views.timeseries_edit, {} , 'timeseries_edit'),

    (r'^timeseries/add/$', views.timeseries_add, {}, 'timeseries_add'),

    (r'^timeseries/delete/(?P<timeseries_id>\d+)/$',
     views.timeseries_delete, {} , 'timeseries_delete'),

    (r'^gentityfile/edit/(?P<gentityfile_id>\d+)/$',
     views.gentityfile_edit, {} , 'gentityfile_edit'),

    (r'^gentityfile/add/$', views.gentityfile_add, {}, 'gentityfile_add'),

    (r'^gentityfile/delete/(?P<gentityfile_id>\d+)/$',
     views.gentityfile_delete, {} , 'gentityfile_delete'),

    (r'^gentityevent/edit/(?P<gentityevent_id>\d+)/$',
     views.gentityevent_edit, {} , 'gentityevent_edit'),

    (r'^gentityevent/add/$', views.gentityevent_add, {}, 'gentityevent_add'),

    (r'^gentityevent/delete/(?P<gentityevent_id>\d+)/$',
     views.gentityevent_delete, {} , 'gentityevent_delete'),

    (r'^instrument/edit/(?P<instrument_id>\d+)/$',
     views.instrument_edit, {} , 'instrument_edit'),

    (r'^instrument/add/$', views.instrument_add, {}, 'instrument_add'),

    (r'^instrument/delete/(?P<instrument_id>\d+)/$',
     views.instrument_delete, {} , 'instrument_delete'),


    (r'^add/(?P<model_name>.+)/$',
     views.model_add, {} , 'model_add'),
)

if settings.STATIC_SERVE:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
    )


