import sys
from glob import glob
from importlib import import_module
from os.path import basename, dirname, isfile, join

from django.apps import AppConfig


class TelemetryConfig(AppConfig):
    name = "enhydris.telemetry"

    def ready(self):

        files = glob(join(dirname(__file__), "types", "*.py"))
        modules = [
            basename(f[:-3])
            for f in files
            if isfile(f) and not basename(f).startswith("_")
        ]

        drivers = {}
        for module_name in modules:
            module = import_module(f".{module_name}", "enhydris.telemetry.types")
            TelemetryAPIClient = getattr(module, "TelemetryAPIClient")
            drivers[module_name] = TelemetryAPIClient

        sys.modules["enhydris.telemetry"].drivers = drivers
