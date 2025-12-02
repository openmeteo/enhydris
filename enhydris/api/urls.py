from django.contrib.auth import views as auth_views
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns

from . import views

urlpatterns = [
    path("auth/", include("dj_rest_auth.urls")),
    path(
        "auth/password/reset/confirm/<str:uidb64>/<str:token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "auth/password/reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]

urlpatterns = format_suffix_patterns(urlpatterns)

router = DefaultRouter()

router.register("stations", views.StationViewSet, "station")

urlstart = r"stations/(?P<station_id>\d+)/"
router.register(urlstart + "files", views.GentityFileViewSet, "file")
router.register(urlstart + "images", views.GentityImageViewSet, "image")
router.register(urlstart + "events", views.GentityEventViewSet, "event")
router.register(
    urlstart + "timeseriesgroups",
    views.TimeseriesGroupViewSet,
    "timeseries_group",
)
router.register(
    urlstart + r"timeseriesgroups/(?P<timeseries_group_id>\d+)/timeseries",
    views.TimeseriesViewSet,
    "timeseries",
)

router.register("gareas", views.GareaViewSet)
router.register("organizations", views.OrganizationViewSet)
router.register("persons", views.PersonViewSet)
router.register("eventtypes", views.EventTypeViewSet)
router.register("variables", views.VariableViewSet)
router.register("units", views.UnitOfMeasurementViewSet)
urlpatterns += router.urls
