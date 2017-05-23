#!/usr/bin/env python
import importlib
import os
import sys

from django.core.management import execute_from_command_line

if __name__ == "__main__":

    # The default value for settings is enhydris.settings.local if such a thing
    # exists, otherwise it's enhydris.settings, which always exists.
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        importlib.util.find_spec("enhydris.settings.local") and
        "enhydris.settings.local" or "enhydris.settings")

    execute_from_command_line(sys.argv)
