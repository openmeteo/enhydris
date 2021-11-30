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

[1] Enhydris runs on Python 3.9 or later.  It does not run on Python 2.
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

Set the domain name
===================

You must setup the Django sites framework. Visit Enhydris through your
browser, login as a superuser, go to the dashboard, and under "Sites"
add a site (i.e. a domain) (or, if a site such as ``example.com`` is
already there, replace it). After that, make sure ``SITE_ID`` in the
settings has the appropriate id.

There are several reasons this needs to be done:
 1. Some generated links, such as links in emails to users for
    registration confirmation, may contain the domain.
 2. Users will not be able to log on unless registered with the domain,
    and stations will only show if registered with the domain. For more
    information about this, see :ref:`Managing domains <domains>`.

If you modify an existing site (e.g. if you change ``example.com`` to
something else), most likely you need to restart the Enhydris server for
the changes to take effect.

Production
==========

To use Enhydris in production, you need to setup a web server such as
apache. This is described in detail in `Deploying Django`_ and in
https://djangodeployment.com/.

You also need to start celery as a service.

.. _deploying django: https://docs.djangoproject.com/en/3.2/howto/deployment/

.. _domains:

Managing domains
================

Enhydris has functionality to power many sites (i.e. domains) from a
single database. For this, it uses the Django sites framework.

Each station has a ``sites`` attribute (a Django ``ManyToManyField``)
with the sites in which the station should show. Normally this attribute
is handled automatically and need not be touched, and in fact the
relevant field does not normally show in the station edit form.  When a
station is added to the system, it is automatically added to the current
site (i.e. the one specified with ``SITE_ID``). In most cases, this is
satisfactory.

Sometimes we want a single database to power two sites, for example,
openmeteo.org (id=1) and system.openhi.net (id=2). There are therefore
two Enhydris instances, each with a different ``SITE_ID``, and each
instance filters out stations that are not registered with that
particular site (i.e. stations whose ``sites`` attribute does not
contain the site of the Enhydris instance). In this case, when a station
is created, it is automatically added only to the site of the Enhydris
instance being used. Superusers, however, can add and remove existing
stations to/from sites. This is done in the station form, which shows a
"Sites" field—however the field is shown only for superusers, only when
editing (not creating) a station, and only if there are at least two
sites registered with the Django Sites framework.

The setting :data:`ENHYDRIS_SITES_FOR_NEW_STATIONS` can modify this
behaviour. In fact, when I said above that new stations are
automatically added only to the site of the Enhydris instance being
used, I was lying. The truth is that when a user uses openmeteo.org and
creates a station, that station is indeed only added to openmeteo.org.
But when a user uses system.openhi.net and adds a station, that station
is added to both system.openhi.net and openmeteo.org.  In order to
achieve this, these are the relevant settings for openmeteo.org::

    SITE_ID = 1
    ENHYDRIS_SITES_FOR_NEW_STATIONS = set()  # Redundant; it's the default

And these are for system.openhi.net::

    SITE_ID = 2
    ENHYDRIS_SITES_FOR_NEW_STATIONS = {1}

This usage of the sites framework affects not only stations but also
users and logins. When a user is created, he is automatically added to a
group whose name is the domain name of the current site (the group is
created if it does not exist). Enhydris only allows a user to logon if
he is a member of that group. Thus, the superuser can decide which users
can log on to which sites.

In the Django admin, when a normal user lists stations, only stations of
the current site are listed. However, when a superuser lists stations,
all stations are listed, and there is a list filter to only show those
of a site.

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

.. data:: ENHYDRIS_SITES_FOR_NEW_STATIONS

   A set of site (i.e. domain) ids of the Django sites framework. The
   default is an empty set. It specifies to which sites (apart from the
   current site) new stations will automatically be added to. New
   stations are always added to the current site, regardless this
   setting.

   For more information, see :ref:`Managing domains <domains>`.

.. data:: ENHYDRIS_STATIONS_PER_PAGE

   Number of stations per page for the pagination of the station list.
   The default is 100.

.. data:: ENHYDRIS_CELERY_SEND_TASK_ERROR_EMAILS

   If this is ``True`` (the default), celery will email the ``ADMINS``
   whenever an exception occurs, like Django does by default.
