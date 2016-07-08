==================================================
Enhydris - Web-based hydro/meteorological database
==================================================

.. image:: https://travis-ci.org/openmeteo/enhydris.svg?branch=master
    :alt: Build button
    :target: https://travis-ci.org/openmeteo/enhydris

.. image:: https://codecov.io/github/openmeteo/enhydris/coverage.svg?branch=master
    :alt: Coverage
    :target: https://codecov.io/gh/openmeteo/enhydris

.. image:: https://img.shields.io/pypi/l/enhydris.svg
    :alt: License

.. image:: https://img.shields.io/pypi/status/enhydris.svg
    :alt: Status

.. image:: https://img.shields.io/pypi/v/enhydris.svg
    :alt: Latest version
    :target: https://pypi.python.org/pypi/enhydris

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
version 3 or any later version.  It is being used by openmeteo.org_,
`Hydrological Observatory of Athens`_, the `Athens Water Supply
Company`_, and `WQ DREAMS`_.

.. _openmeteo.org: http://openmeteo.org/
.. _hydrological observatory of athens: http://hoa.ntua.gr/
.. _hydroscope: http://main.hydroscope.gr/
.. _athens water Supply Company: http://itia.ntua.gr/eydap/db/
.. _wq dreams: http://wq-dreams.eu/

For more information about Enhydris, read its documentation in the
``doc`` directory or `live at readthedocs`_.

.. _live at readthedocs: http://enhydris.readthedocs.io/

**Installing a development instance**

After creating a `virtualenv` and installing prerequisites, execute
this in the top-level directory::

    python enhydris/bin/enhydris-admin newinstance devinstance

Then, edit file ``devinstance/settings.py``, and execute this::

    python devinstance/manage.py runserver

Finally, point your browser at http://localhost:8000/.
