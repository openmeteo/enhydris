from django.conf import settings
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from django.http import Http404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns

from rest_auth.registration import views as auth_registration_views

from . import views


@api_view()
def null_view(request):
    return Response(status=status.HTTP_400_BAD_REQUEST)


def wrapped_registration_view(registration_view):
    def func(*args, **kwargs):
        if settings.ENHYDRIS_REGISTRATION_OPEN:
            return registration_view(*args, **kwargs)
        else:
            raise Http404

    return func


# For why we have this URL, see
# https://github.com/Tivix/django-rest-auth/issues/292#issuecomment-305085402
urlpatterns = [
    url(
        r"^auth/registration/account-email-verification-sent",
        null_view,
        name="account_email_verification_sent",
    )
]

# Normally we could just put this in urlpatterns:
#   url(r"^/auth/registration/", include("rest_auth.registration.urls"))
# However, we want these views to return 404 if ENHYDRIS_REGISTRATION_OPEN is False,
# so we wrap them in a wrapper that does this. (We could just add them to
# urlpatterns conditionally, but then ENHYDRIS_REGISTRATION_OPEN wouldn't be
# overridable in tests.)
urlpatterns += [
    url(
        r"^auth/registration/$",
        wrapped_registration_view(auth_registration_views.RegisterView.as_view()),
        name="rest_register",
    ),
    url(
        r"^auth/registration/verify-email/$",
        wrapped_registration_view(auth_registration_views.VerifyEmailView.as_view()),
        name="rest_verify_email",
    ),
    url(
        r"^auth/registration/account-confirm-email/(?P<key>[-:\w]+)/$",
        null_view,
        name="account_confirm_email",
    ),
]

urlpatterns += [
    url(r"^auth/", include("rest_auth.urls")),
    url(
        r"^auth/password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$",
        auth_views.password_reset_confirm,
        name="password_reset_confirm",
    ),
    url(
        r"^auth/password/reset/complete/$",
        auth_views.password_reset_complete,
        name="password_reset_complete",
    ),
    url(r"^captcha/", include("rest_captcha.urls")),
]

urlpatterns = format_suffix_patterns(urlpatterns)

router = DefaultRouter()

router.register("stations", views.StationViewSet, "station")

urlstart = r"stations/(?P<station_id>\d+)/"
router.register(urlstart + "altcodes", views.GentityAltCodeViewSet, "altcode")
router.register(urlstart + "files", views.GentityFileViewSet, "file")
router.register(urlstart + "events", views.GentityEventViewSet, "event")
router.register(urlstart + "overseers", views.OverseerViewSet, "overseer")
router.register(urlstart + "instruments", views.InstrumentViewSet, "instrument")
router.register(urlstart + "timeseries", views.TimeseriesViewSet, "timeseries")

router.register("waterdivisions", views.WaterDivisionViewSet)
router.register("gentityaltcodetypes", views.GentityAltCodeTypeViewSet)
router.register("organizations", views.OrganizationViewSet)
router.register("persons", views.PersonViewSet)
router.register("stationtypes", views.StationTypeViewSet)
router.register("timezones", views.TimeZoneViewSet)
router.register("politicaldivisions", views.PoliticalDivisionViewSet)
router.register("intervaltypes", views.IntervalTypeViewSet)
router.register("filetypes", views.FileTypeViewSet)
router.register("eventtypes", views.EventTypeViewSet)
router.register("instrumenttypes", views.InstrumentTypeViewSet)
router.register("basins", views.WaterBasinViewSet)
router.register("timesteps", views.TimeStepViewSet)
router.register("variables", views.VariableViewSet)
router.register("units", views.UnitOfMeasurementViewSet)
urlpatterns += router.urls
