from django.conf import settings
from django.contrib.auth import views as auth_views
from django.http import Http404
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns

from rest_auth.registration import views as auth_registration_views

from . import views


class RegistrationMixin:
    """Override dispatch method so that it raises 404 if registration isn't open.

    We want the views from rest_auth.registration to raise 404 if
    ENHYDRIS_REGISTRATION_OPEN is False.   We could just add them to
    urlpatterns conditionally, but then ENHYDRIS_REGISTRATION_OPEN wouldn't be
    overridable in tests. So what we do is we modify their dispatch() method so that
    it checks for ENHYDRIS_REGISTRATION_OPEN and then either raises 404 or calls the
    inherited dispatch().
    """

    def dispatch(self, *args, **kwargs):
        if settings.ENHYDRIS_REGISTRATION_OPEN:
            return super().dispatch(*args, **kwargs)
        else:
            raise Http404


class RegisterView(RegistrationMixin, auth_registration_views.RegisterView):
    pass


class VerifyEmailView(RegistrationMixin, auth_registration_views.VerifyEmailView):
    pass


urlpatterns = [
    path("auth/registration/", RegisterView.as_view(), name="rest_register"),
    path(
        "auth/registration/verify-email/",
        VerifyEmailView.as_view(),
        name="rest_verify_email",
    ),
    path("auth/", include("rest_auth.urls")),
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
    path("captcha/", include("rest_captcha.urls")),
]

urlpatterns = format_suffix_patterns(urlpatterns)

router = DefaultRouter()

router.register("stations", views.StationViewSet, "station")

urlstart = r"stations/(?P<station_id>\d+)/"
router.register(urlstart + "files", views.GentityFileViewSet, "file")
router.register(urlstart + "events", views.GentityEventViewSet, "event")
router.register(urlstart + "instruments", views.InstrumentViewSet, "instrument")
router.register(urlstart + "timeseries", views.TimeseriesViewSet, "timeseries")

router.register("gareas", views.GareaViewSet)
router.register("organizations", views.OrganizationViewSet)
router.register("persons", views.PersonViewSet)
router.register("timezones", views.TimeZoneViewSet)
router.register("intervaltypes", views.IntervalTypeViewSet)
router.register("filetypes", views.FileTypeViewSet)
router.register("eventtypes", views.EventTypeViewSet)
router.register("instrumenttypes", views.InstrumentTypeViewSet)
router.register("timesteps", views.TimeStepViewSet)
router.register("variables", views.VariableViewSet)
router.register("units", views.UnitOfMeasurementViewSet)
urlpatterns += router.urls
