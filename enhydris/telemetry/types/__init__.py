from django.utils.translation import ugettext_lazy as _


class TelemetryAPIClientBase:
    device_locator_label = _("URL")
    device_locator_help_text = ""
    hide_device_locator = False
    username_label = _("Username")
    password_label = _("Password")

    def __init__(self, telemetry):
        self.telemetry = telemetry
