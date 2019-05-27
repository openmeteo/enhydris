#!/usr/bin/env python
import sys

from django.core.management import execute_from_command_line

from enhydris import set_django_settings_module

if __name__ == "__main__":
    set_django_settings_module()
    execute_from_command_line(sys.argv)
