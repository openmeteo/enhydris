from django.conf.urls import url
from django.views.generic.base import RedirectView
from django.contrib.auth import views as auth_views

from enhydris import views

urlpatterns = [
    url(r'^$', views.StationListView.as_view(),
        name='station_list'),
    url(r'^stations/l/$', RedirectView.as_view(url='../..', permanent=True)),
    url(r'^stations/d/(?P<pk>\d+)/$', views.StationDetailView.as_view(),
        name='station_detail'),
    url(r'^stations/b/(?P<pk>\d+)/$', views.StationBriefView.as_view(),
        name='station_brief'),
    url(r'^stations/edit/(?P<station_id>\d+)/$', views.station_edit, {},
        'station_edit'),
    url(r'^stations/add/$', views.station_add, {}, 'station_add'),
    url(r'^stations/delete/(?P<station_id>\d+)/$', views.station_delete, {},
        'station_delete'),

    url(r'^instruments/d/(?P<pk>\d+)/$',
        views.InstrumentDetailView.as_view(), name='instrument_detail'),
    url(r'^instrument/edit/(?P<instrument_id>\d+)/$', views.instrument_edit,
        {}, 'instrument_edit'),
    url(r'^instrument/add/$', views.instrument_add, {}, 'instrument_add'),
    url(r'^instrument/delete/(?P<instrument_id>\d+)/$',
        views.instrument_delete, {}, 'instrument_delete'),

    url(r'^timeseries/d/(?P<pk>\d+)/$', views.TimeseriesDetailView.as_view(),
        name='timeseries_detail'),
    url(r'^timeseries/data/$', views.timeseries_data, {}, 'timeseries_data'),
    url(r'^timeseries/d/(?P<object_id>\d+)/download/'
        r'((?P<start_date>[^/]*)/((?P<end_date>[^/]*)/)?)?$',
        views.download_timeseries, {}, 'timeseries_text'),
    url(r'^timeseries/d/(?P<object_id>\d+)/bottom/$', views.timeseries_bottom,
        {}, 'timeseries_bottom'),
    url(r'^timeseries/edit/(?P<timeseries_id>\d+)/$', views.timeseries_edit,
        {}, 'timeseries_edit'),
    url(r'^timeseries/add/$', views.timeseries_add, {}, 'timeseries_add'),
    url(r'^timeseries/delete/(?P<timeseries_id>\d+)/$',
        views.timeseries_delete, {}, 'timeseries_delete'),

    url(r'^gentityfile/(?P<gf_id>\d+)/download/$', views.download_gentityfile,
        {}, 'gentityfile_dl'),
    url(r'^gentityfile/edit/(?P<gentityfile_id>\d+)/$', views.gentityfile_edit,
        {}, 'gentityfile_edit'),
    url(r'^gentityfile/add/$', views.gentityfile_add, {}, 'gentityfile_add'),
    url(r'^gentityfile/delete/(?P<gentityfile_id>\d+)/$',
        views.gentityfile_delete, {}, 'gentityfile_delete'),

    url(r'^gentitygenericdata/(?P<gg_id>\d+)/download/$',
        views.download_gentitygenericdata, {}, 'gentitygenericdata_dl'),
    url(r'^gentitygenericdata/edit/(?P<ggenericdata_id>\d+)/$',
        views.gentitygenericdata_edit, {}, 'gentitygenericdata_edit'),
    url(r'^gentitygenericdata/add/$', views.gentitygenericdata_add, {},
        'gentitygenericdata_add'),
    url(r'^gentitygenericdata/delete/(?P<ggenericdata_id>\d+)/$',
        views.gentitygenericdata_delete, {}, 'gentitygenericdata_delete'),

    url(r'^gentityevent/edit/(?P<gentityevent_id>\d+)/$',
        views.gentityevent_edit, {}, 'gentityevent_edit'),
    url(r'^gentityevent/add/$', views.gentityevent_add, {},
        'gentityevent_add'),
    url(r'^gentityevent/delete/(?P<gentityevent_id>\d+)/$',
        views.gentityevent_delete, {}, 'gentityevent_delete'),

    url(r'^gentityaltcode/edit/(?P<gentityaltcode_id>\d+)/$',
        views.gentityaltcode_edit, {}, 'gentityaltcode_edit'),
    url(r'^gentityaltcode/add/$', views.gentityaltcode_add, {},
        'gentityaltcode_add'),
    url(r'^gentityaltcode/delete/(?P<gentityaltcode_id>\d+)/$',
        views.gentityaltcode_delete, {}, 'gentityaltcode_delete'),

    url(r'^overseer/edit/(?P<overseer_id>\d+)/$', views.overseer_edit, {},
        'overseer_edit'),
    url(r'^overseer/add/$', views.overseer_add, {}, 'overseer_add'),
    url(r'^overseer/delete/(?P<overseer_id>\d+)/$', views.overseer_delete, {},
        'overseer_delete'),

    url(r'^(?P<layer>[^/]+)/kml/$',
        views.StationListView.as_view(template_name='placemarks.kml')),

    url(r'^bounding_box/$', views.BoundingBoxView.as_view(), {},
        'bounding_box'),

    url(r'^add/(?P<model_name>.+)/$', views.ModelAddView.as_view(),
        name='model_add'),

    #   http://stackoverflow.com/questions/19985103/
    url(r'^password/change/$', auth_views.password_change,
        name='password_change'),
    url(r'^password/change/done/$', auth_views.password_change_done,
        name='password_change_done'),
    url(r'^password/reset/$', auth_views.password_reset,
        name='password_reset'),
    url(r'^accounts/password/reset/done/$', auth_views.password_reset_done,
        name='password_reset_done'),
    url(r'^password/reset/complete/$', auth_views.password_reset_complete,
        name='password_reset_complete'),
    url(r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
        auth_views.password_reset_confirm, name='password_reset_confirm'),
]
