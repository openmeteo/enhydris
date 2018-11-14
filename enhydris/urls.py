from django.conf.urls import url
from django.views.generic.base import RedirectView
from django.contrib.auth import views as auth_views

from enhydris import views

urlpatterns = [
    url(r"^$", views.StationListView.as_view(), name="station_list"),
    url(r"^stations/l/$", RedirectView.as_view(url="../..", permanent=True)),
    url(
        r"^stations/d/(?P<pk>\d+)/$",
        views.StationDetailView.as_view(),
        name="station_detail",
    ),
    url(
        r"^stations/b/(?P<pk>\d+)/$",
        views.StationBriefView.as_view(),
        name="station_brief",
    ),
    url(
        r"^instruments/d/(?P<pk>\d+)/$",
        views.InstrumentDetailView.as_view(),
        name="instrument_detail",
    ),
    url(
        r"^timeseries/d/(?P<pk>\d+)/$",
        views.TimeseriesDetailView.as_view(),
        name="timeseries_detail",
    ),
    url(
        r"^timeseries/d/(?P<object_id>\d+)/download/"
        r"((?P<start_date>[^/]*)/((?P<end_date>[^/]*)/)?)?$",
        views.download_timeseries,
        {},
        "timeseries_text",
    ),
    url(
        r"^timeseries/d/(?P<object_id>\d+)/bottom/$",
        views.timeseries_bottom,
        {},
        "timeseries_bottom",
    ),
    url(
        r"^gentityfile/(?P<gf_id>\d+)/download/$",
        views.download_gentityfile,
        {},
        "gentityfile_dl",
    ),
    url(
        r"^gentitygenericdata/(?P<gg_id>\d+)/download/$",
        views.download_gentitygenericdata,
        {},
        "gentitygenericdata_dl",
    ),
    url(
        r"^(?P<layer>[^/]+)/kml/$",
        views.StationListView.as_view(template_name="placemarks.kml"),
    ),
    url(r"^bounding_box/$", views.BoundingBoxView.as_view(), {}, "bounding_box"),
    #   http://stackoverflow.com/questions/19985103/
    url(r"^password/change/$", auth_views.password_change, name="password_change"),
    url(
        r"^password/change/done/$",
        auth_views.password_change_done,
        name="password_change_done",
    ),
    url(r"^password/reset/$", auth_views.password_reset, name="password_reset"),
    url(
        r"^accounts/password/reset/done/$",
        auth_views.password_reset_done,
        name="password_reset_done",
    ),
    url(
        r"^password/reset/complete/$",
        auth_views.password_reset_complete,
        name="password_reset_complete",
    ),
    url(
        r"^password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$",
        auth_views.password_reset_confirm,
        name="password_reset_confirm",
    ),
]
