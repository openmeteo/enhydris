#!/usr/bin/env python

from setuptools import setup, find_packages


installation_requirements = [
    "psycopg2>=2.2,<3",
    "Django>=1.8,<1.9",
    "django-registration-redux>=1.2,<2",
    "djangorestframework>=2.3,<3",
    "django-ajax-selects>=1.3.4,<2",
    "Markdown>=2.1,<3",
    "django-simple-captcha>=0.4",
    "pthelma>=0.9,<1",
    "gdal>=1.6",
    "django-bootstrap3>=5.1,<5.2",
]

kwargs = {
    'name': "enhydris",
    'version': __import__('enhydris').__version__,
    'license': "AGPL3",
    'description': "Web application for meteorological data storage",
    'author': "Antonis Christofides",
    'author_email': "anthony@itia.ntua.gr",
    'packages': find_packages(),
    'install_requires': installation_requirements,
    'test_suite': 'runtests.runtests',
}

setup(**kwargs)
