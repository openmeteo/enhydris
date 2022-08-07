from django.urls import path

from enhydris.telemetry import views

urlpatterns = [
    path(
        "stations/<int:station_id>/telemetry/<int:seq>/",
        views.TelemetryWizardView.as_view(),
        name="telemetry_wizard",
    ),
    path(
        "stations/<int:station_id>/telemetry/logs/",
        views.TelemetryLogsView.as_view(),
        name="telemetry_logs",
    ),
    path(
        "stations/<int:station_id>/telemetry/logs/<int:pk>/",
        views.TelemetryLogDetailView.as_view(),
        name="telemetry_log_detail",
    ),
]
