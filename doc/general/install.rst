.. _install:

==============================
Installation and configuration
==============================

.. highlight:: bash

Prerequisites
=============

===================================================== ============
Prerequisite                                          Version
===================================================== ============
Python with setuptools and pip                        3 [1]
PostgreSQL + PostGIS + TimescaleDB_
GDAL                                                  1.9 [2]
===================================================== ============

[1] Enhydris runs on Python 3.5 or later.  It does not run on Python 2.
setuptools and pip are needed in order to install the rest of the Python
modules.

[2] In theory, installing the prerequisites with :command:`pip` will
also install gdal. However it can be tricky to install and it's
usually easier to install a prepackaged version for your operating
system.

.. _timescaledb: https://www.timescale.com

Install Enhydris
================

Install Enhydris by cloning it and then installing the requirements
specified in :file:`requirements.txt`, probably in a virtualenv::

    git clone https://github.com/openmeteo/enhydris.git
    git checkout 3.0
    virtualenv --system-site-packages --python=/usr/bin/python3 \
        enhydris/venv
    ./enhydris/venv/bin/pip install -r requirements.txt
    ./enhydris/venv/bin/pip install -r requirements-dev.txt

Configure Enhydris
==================

Create a Django settings file, either in
:file:`enhydris_project/settings/local.py`, or wherever you like. It
should begin with this::

    from enhydris_project.settings.development import *

and then it should go on to override ``DEBUG``, ``SECRET_KEY``,
``DATABASES`` and ``STATIC_ROOT``. More settings you may want to
override are the `Django settings`_ and the :ref:`Enhydris 
settings <enhydris_settings>`.

On production you need to import from ``enhydris_project.settings``
instead.

Create a spatially enabled database
===================================

(In the following examples, we use ``enhydris_db`` as the database
name, and ``enhydris_user`` as the PostgreSQL username. The user
should not be a super user, and not be allowed to create more users.
In production, it should not be allowed to create databases; in
testing, it should be allowed, in order to be able to run the unit
tests.)

Here is a **Debian buster example**::

   # Install PostgreSQL and PostGIS
   apt install postgis postgresql-11-postgis-2.5

   # Install TimescaleDB (you need to add repositories in /etc/apt as
   # explained in the TimescaleDB installation documentation)
   apt install timescaledb-postgresql-11
   timescaledb-tune

   # Create database template
   sudo -u postgres -s
   createdb template_postgis
   psql -d template_postgis -c "CREATE EXTENSION postgis;"
   psql -d template_postgis -c \
      "UPDATE pg_database SET datistemplate='true' \
      WHERE datname='template_postgis';"
   exit

   # Create database
   sudo -u postgres -s
   createuser --pwprompt enhydris_user
   createdb --template template_postgis --owner enhydris_user enhydris_db
   exit

   # Note: We don't need to install the timescaledb extension; the
   Django migrations of Enhydris will do so automatically.

Here is a **Windows example**, assuming PostgreSQL is installed at
the default location::

   cd C:\Program Files\PostgreSQL\11\bin
   createdb template_postgis
   psql -d template_postgis -c "CREATE EXTENSION postgis;"
   psql -d template_postgis -c "UPDATE pg_database SET datistemplate='true'
      WHERE datname='template_postgis';"
   createuser -U postgres --pwprompt enhydris_user
   createdb --template template_postgis --owner enhydris_user enhydris_db

At some point, these commands will ask you for the password of the
operating system user.

Note:

Initialize the database
=========================

In order to initialize your database and create the necessary database
tables for Enhydris to run, run the following commands inside the
Enhydris configuration directory::

   python manage.py migrate
   python manage.py createsuperuser

The above commands will also ask you to create a Enhydris superuser.

Start Django and Celery
=======================

Inside the Enhydris configuration directory, run the following
command::

    python manage.py runserver

The above command will start the Django development server and set it
to listen to port 8000.

In addition, run the following to start Celery::

    celery worker -A enhydris -l info --concurrency=1

Production
==========

To use Enhydris in production, you need to setup a web server such as
apache. This is described in detail in `Deploying Django`_ and in
https://djangodeployment.com/.

You also need to start celery as a service.

.. _deploying django: http://docs.djangoproject.com/en/3.2/howto/deployment/

Post-install configuration: domain name
=======================================

After you run Enhydris, logon as a superuser, visit the admin panel,
go to ``Sites``, edit the default site, and enter your domain name
there instead of ``example.com``. Emails to users for registration
confirmation will contain links to that domain.  Restart the
Enhydris (by restarting apache/gunicorn/whatever) after changing the
domain name.

.. _enhydris_settings:

Settings reference
==================
 
These are the settings available to Enhydris, in addition to the
`Django settings`_.

.. _django settings: http://docs.djangoproject.com/en/3.2/ref/settings/

.. data:: REGISTRATION_OPEN

   If ``True``, users can register, otherwise they have to be created
   by the administrator. The default is ``False``.

   (This setting is defined by ``django-registration-redux``.)

.. data:: ENHYDRIS_USERS_CAN_ADD_CONTENT

   If set to ``True``, it enables all logged in users to add stations to
   the site, and edit the data of the stations they have entered.  When
   set to ``False`` (the default), only privileged users are allowed to
   add/edit/remove data from the db.

   See also :data:`ENHYDRIS_OPEN_CONTENT`.

.. data:: ENHYDRIS_OPEN_CONTENT

   If set to ``True``, users who haven't logged on can view timeseries
   data and station file (e.g. image) content. Otherwise, only logged on
   users can do so. Logged on users can always view everything.

   When this setting is ``False``, ``REGISTRATION_OPEN`` must obviously
   also be set to ``False``.

.. data:: ENHYDRIS_MAP_BASE_LAYERS

   A dictionary of JavaScript definitions of base layers to use on the map.
   The default is::

       {
           "Open Street Map": r'''
               L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                   attribution: (
                       'Map data © <a href="https://www.openstreetmap.org/">' +
                       'OpenStreetMap</a> contributors, ' +
                       '<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>'
                   ),
                   maxZoom: 18,
               })
           ''',
           "Open Cycle Map": r'''
               L.tileLayer("https://{s}.tile.thunderforest.com/cycle/{z}/{x}/{y}.png", {
                   attribution: (
                       'Map data © <a href="https://www.openstreetmap.org/">' +
                       'OpenStreetMap</a> contributors, ' +
                       '<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>'
                   ),
                   maxZoom: 18,
               })
           '''
        }

.. data:: ENHYDRIS_MAP_DEFAULT_BASE_LAYER

   The name of the base layer that is visible by default; it must be a key in
   data:`ENHYDRIS_MAP_BASE_LAYERS`. The default is "Open Street Map".

.. data:: ENHYDRIS_MAP_MIN_VIEWPORT_SIZE

   Set a value in degrees. When a geographical query has a bounding box
   with dimensions less than :data:`ENHYDRIS_MAP_MIN_VIEWPORT_SIZE`, the
   map initially shown will be zoomed so that its dimension will be at
   least ``ENHYDRIS_MAP_MIN_VIEWPORT_SIZE²``. Useful when showing a
   single entity, such as a hydrometeorological station. Default value
   is 0.04, corresponding to an area approximately 4×4 km.

.. data:: ENHYDRIS_MAP_DEFAULT_VIEWPORT

   A tuple containing the default viewport for the map in geographical
   coordinates, in cases of geographical queries that do not return
   anything.  Format is (minlon, minlat, maxlon, maxlat) where lon and
   lat is in decimal degrees, positive for north/east, negative for
   west/south.

.. data:: ENHYDRIS_SITE_STATION_FILTER

   This is a quick-and-dirty way to create a web site that only
   displays a subset of an Enhydris database. For example, the
   database of http://system.deucalionproject.gr/ is the same as that
   of http://openmeteo.org/; however, the former only shows stations
   relevant to the Deucalion project, because it has this setting::

      ENHYDRIS_SITE_STATION_FILTER = {'owner__id__exact': '9'}

.. data:: ENHYDRIS_STATIONS_PER_PAGE

   Number of stations per page for the pagination of the station list.
   The default is 100.

.. data:: ENHYDRIS_CELERY_SEND_TASK_ERROR_EMAILS

   If this is ``True`` (the default), celery will email the ``ADMINS``
   whenever an exception occurs, like Django does by default.
