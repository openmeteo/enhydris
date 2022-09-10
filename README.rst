==================================================
Enhydris - Web-based hydro/meteorological database
==================================================

.. image:: https://github.com/openmeteo/enhydris/actions/workflow/run-tests-automatically.yml/badge.svg
    :alt: Build button
    :target: https://travis-ci.com/openmeteo/enhydris/actions/workflow/run-tests-automatically.yml

.. image:: https://codecov.io/github/openmeteo/enhydris/coverage.svg?branch=master
    :alt: Coverage
    :target: https://codecov.io/gh/openmeteo/enhydris

Enhydris is a system for the storage and management of hydrological
and meteorological time series. You can see it in action at
http://openmeteo.org/.

The database is accessible through a web interface, which includes
several data representation features such as tables, graphs and
mapping capabilities. Data access is configurable to allow or to
restrict user groups and/or privileged users to contribute or to
download data. With these capabilities, Enhydris can be used either as
a public repository of free data or as a private
system for data storage. Time series can be downloaded in plain text
format that can be directly loaded to Hydrognomon_, a free
tool for analysis and processing of meteorological time series.

.. _hydrognomon: http://hydrognomon.org/

Enhydris is written in Python/Django, and can be installed on every
operating system on which Python runs, including GNU/Linux and Windows.
It is free software, available under the GNU General Public License
version 3 or any later version.

For more information about Enhydris, read its documentation in the
``doc`` directory or `live at readthedocs`_.

.. _live at readthedocs: http://enhydris.readthedocs.io/
