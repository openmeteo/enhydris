from django.conf import settings
from django.conf.urls import include, url
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
    url(r"^captcha/", include("rest_captcha.urls")),
    url(r"^tsdata/(?P<pk>\d+)/$", views.Tsdata.as_view(), name="tsdata"),
    url(r"^Station/$", views.StationList.as_view(), name="Station-list"),
    url(
        r"^Station/(?P<pk>\d+)/$", views.StationDetail.as_view(), name="Station-detail"
    ),
    url(r"^Timeseries/$", views.TimeseriesList.as_view(), name="Timeseries-list"),
    url(
        r"^Timeseries/(?P<pk>\d+)/$",
        views.TimeseriesDetail.as_view(),
        name="Timeseries-detail",
    ),
]

urlpatterns = format_suffix_patterns(urlpatterns)

router = DefaultRouter()
router.register("WaterDivision", views.WaterDivisionViewSet)
router.register("GentityAltCodeType", views.GentityAltCodeTypeViewSet)
router.register("Organization", views.OrganizationViewSet)
router.register("Person", views.PersonViewSet)
router.register("StationType", views.StationTypeViewSet)
router.register("TimeZone", views.TimeZoneViewSet)
router.register("PoliticalDivision", views.PoliticalDivisionViewSet)
router.register("IntervalType", views.IntervalTypeViewSet)
router.register("FileType", views.FileTypeViewSet)
router.register("EventType", views.EventTypeViewSet)
router.register("InstrumentType", views.InstrumentTypeViewSet)
router.register("WaterBasin", views.WaterBasinViewSet)
router.register("TimeStep", views.TimeStepViewSet)
router.register("Variable", views.VariableViewSet)
router.register("UnitOfMeasurement", views.UnitOfMeasurementViewSet)
router.register("GentityAltCode", views.GentityAltCodeViewSet)
router.register("GentityFile", views.GentityFileViewSet)
router.register("GentityEvent", views.GentityEventViewSet)
router.register("Overseer", views.OverseerViewSet)
router.register("Instrument", views.InstrumentViewSet)
urlpatterns += router.urls
