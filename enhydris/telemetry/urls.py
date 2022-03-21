from django.urls import path

from enhydris.telemetry import views

urlpatterns = [
    path(
        "stations/<int:station_id>/telemetry/<int:seq>/",
        views.TelemetryWizardView.as_view(),
        name="telemetry_wizard",
    ),
]
