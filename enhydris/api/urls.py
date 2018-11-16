from django.conf.urls import url
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns

from . import views

urlpatterns = [
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


# _urls.append(
#     url(
#         r"^{0}/modified_after/(?P<modified_after>.*)/$".format(_x),
#         list_view,
#         name=_x + "-list",
#     )
# )
