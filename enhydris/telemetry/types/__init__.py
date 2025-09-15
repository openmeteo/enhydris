from django.utils.translation import gettext_lazy as _

from enhydris.telemetry.forms import (
    ChooseSensorForm,
    ChooseStationForm,
    ConnectionDataForm,
    EssentialDataForm,
)


class TelemetryAPIClientBase:
    device_locator_label = _("URL")
    device_locator_help_text = ""
    hide_device_locator = False
    hide_username = False
    hide_data_timezone = False
    username_label = _("Username")
    password_label = _("Password")
    forms = [EssentialDataForm, ConnectionDataForm, ChooseStationForm, ChooseSensorForm]
    sensor_prompt = _(
        "To which Enhydris time series does sensor {sensor_label} correspond?"
    )
    ignore_sensor_prompt = _("Ignore this sensor")

    def __init__(self, telemetry):
        self.telemetry = telemetry

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

    def connect(self):
        pass

    def disconnect(self):
        pass
