from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from django_stubs_ext import StrOrPromise

from enhydris.telemetry.forms import (
    ChooseSensorForm,
    ChooseStationForm,
    ConnectionDataForm,
    EssentialDataForm,
)
from enhydris.telemetry.models import Telemetry


class TelemetryAPIClientBase:
    device_locator_label: StrOrPromise = _("URL")
    device_locator_help_text: StrOrPromise = ""
    hide_device_locator = False
    hide_username = False
    hide_data_timezone = False
    username_label: StrOrPromise = _("Username")
    password_label: StrOrPromise = _("Password")
    forms = [EssentialDataForm, ConnectionDataForm, ChooseStationForm, ChooseSensorForm]
    sensor_prompt: StrOrPromise = _(
        "To which Enhydris time series does sensor {sensor_label} correspond?"
    )
    ignore_sensor_prompt: StrOrPromise = _("Ignore this sensor")

    def __init__(self, telemetry: Telemetry):
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
