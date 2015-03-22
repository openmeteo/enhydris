#!/usr/bin/env python

from setuptools import setup, find_packages


_django_profiles_version = '0.3b1'
_django_sorting_version = '0.2b1'

installation_requirements = [
    "psycopg2>=2.2,<3",
    "Django>=1.5,<1.7",
    "django-registration>=1.0,<2",
    "django-profiles=={}".format(_django_profiles_version),
    "djangorestframework>=2.3,<3",
    "South>=0.8",
    "django-notify>=1.1,<2",
    "django-ajax-selects>=1.3.4,<2",
    "Markdown>=2.1,<3",
    "django-simple-captcha>=0.4",
    "pthelma>=0.9,<1",
    "django-appconf>=0.6",
    "gdal>=1.6",
    "django-tables2>=0.14",
    "django-sorting=={}".format(_django_sorting_version),
    "django-bootstrap3>=5.1,<5.2",
]

_django_profiles_url = \
    "https://bitbucket.org/aptiko/django-profiles" \
    "/get/{0}.tar.gz#egg=django-profiles-{0}".format(_django_profiles_version)
_django_sorting_url = \
    "https://github.com/aptiko/django-sorting/archive" \
    "/{0}.tar.gz#egg=django-sorting-{0}".format(_django_sorting_version)

from setuptest import test

kwargs = {
    'name': "enhydris",
    'version': "dev",
    'license': "GPL3",
    'description': "Web application for meteorological data storage",
    'author': "Antonis Christofides",
    'author_email': "anthony@itia.ntua.gr",
    'packages': find_packages(),
    'install_requires': installation_requirements,
    'dependency_links': [_django_profiles_url, _django_sorting_url],
    'test_suite': 'runtests.runtests',
}

setup(**kwargs)
