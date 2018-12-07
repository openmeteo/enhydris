from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView

from enhydris import views

urlpatterns = [
    url(r"^stations/l/$", RedirectView.as_view(url="../..", permanent=True)),
    url(
        r"^timeseries/d/(?P<object_id>\d+)/bottom/$",
        views.timeseries_bottom,
        {},
        "timeseries_bottom",
    ),
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
