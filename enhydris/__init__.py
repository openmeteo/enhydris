import importlib
import os

__version__ = "DEV"
VERSION = __version__  # synonym


def set_django_settings_module():
    # The default value for settings is enhydris_project.settings.local if such a thing
    # exists, otherwise it's enhydris_project.settings, which always exists.
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        importlib.util.find_spec("enhydris_project.settings.local")
        and "enhydris_project.settings.local"
        or "enhydris_project.settings",
    )
