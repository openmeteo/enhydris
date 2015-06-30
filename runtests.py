# This file mainly exists to allow "python setup.py test" to work

import os
import sys

import django
from django.test.utils import get_runner
from django.conf import settings


def runtests():
    os.environ['DJANGO_SETTINGS_MODULE'] = 'test_settings'
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=1, interactive=True)
    failures = test_runner.run_tests(['enhydris'])
    sys.exit(bool(failures))


if __name__ == '__main__':
    runtests()
