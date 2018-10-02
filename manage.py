#!/usr/bin/env python
import importlib
import os
import sys

from django.core.management import execute_from_command_line

if __name__ == "__main__":

    # The default value for settings is enhydris_project.settings.local if such a thing
    # exists, otherwise it's enhydris_project.settings, which always exists.
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        importlib.util.find_spec("enhydris_project.settings.local")
        and "enhydris_project.settings.local"
        or "enhydris_project.settings",
    )

    execute_from_command_line(sys.argv)
