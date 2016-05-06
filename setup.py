#!/usr/bin/env python

import itertools
import os

from setuptools import setup, find_packages


installation_requirements = [
    "Django>=1.8,<1.9",
    "django-registration-redux>=1.2,<2",
    "djangorestframework>=3.1,<3.2",
    "django-ajax-selects>=1.3.4,<2",
    "Markdown>=2.1,<3",
    "django-simple-captcha>=0.4",
    "pthelma>=0.12,<1",
    "gdal>=1.6",
    "django-bootstrap3>=5.1,<6",
    "simpletail>=0.1.2",
    "iso8601",
    "pytz",
]


def get_recursive_package_data(packagedir, subdirs):
    """
    Return a list of files, not directories, in packagedir, recursively.

    subdirs are a list of subdirectories of packagedir whose files to include.
    The list of paths returned are relative, starting inside packagedir.
    """
    result = []
    saved_cwd = os.getcwd()
    os.chdir(packagedir)
    try:
        items = itertools.chain.from_iterable([os.walk(d) for d in subdirs])
        for dirpath, dirnames, filenames in items:
            result.extend([os.path.join(dirpath, f) for f in filenames])
        return result
    finally:
        os.chdir(saved_cwd)


packages = find_packages(exclude=['*.tests', '*.tests.*', 'tests.*', 'tests',
                                  'enhydris.conf', 'enhydris.hcore.templates'])

# Contrary to appearances, enhydris.conf isn't a package; it's a data
# directory. The .py files it contains are files and templates to be copied
# by the enhydris-admin command. This is why we have excluded it above. We now
# proceed to add it as package data.
package_data = {
    'enhydris': ['conf/*'],
    'enhydris.hcore': get_recursive_package_data(
        os.path.join('enhydris', 'hcore'), ['templates', 'static']),
}


kwargs = {
    'name': "enhydris",
    'version': __import__('enhydris').__version__,
    'license': "AGPL3",
    'description': "Web application for meteorological data storage",
    'author': "Antonis Christofides",
    'author_email': "anthony@itia.ntua.gr",
    'packages': packages,
    'package_data': package_data,
    'scripts': ['enhydris/bin/enhydris-admin'],
    'install_requires': installation_requirements,
    'test_suite': 'runtests.runtests',
    'tests_require': ['model-mommy>=1.2.4'],
}

setup(**kwargs)
