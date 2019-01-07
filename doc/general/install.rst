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
Database supported by GeoDjango                       [2]
GDAL                                                  1.9
PIL or Pillow with freetype                           1.1.7 [3]
===================================================== ============

[1] Enhydris runs on Python 3.5 or later.  It does not run on Python 2.
setuptools and pip are needed in order to install the rest of the Python
modules.

[2] Enhydris has been tested with PostgreSQL+PostGIS and spatialite, the
latter only in development.

[3] PIL/Pillow is not directly required by Enhydris, but by other
python modules required my Enhydris. In theory, installing Enhydris
with :command:`pip` will indirectly result in also installing
PIL/Pillow.  However, it can be tricky to install, and it may be
better to install a prepackaged version for your operating
system. It must be compiled with libfreetype support. This is common
in Linux distributions.

.. note::

   Example: Installing prerequisites on Debian/Ubuntu

   In this example, we also install package ``python3-pandas`` to avoid
   compilation.

   ::

      apt-get install python3 postgresql python3-setuptools python3-pip \
          python3-pil python3-gdal python3-pandas

Install Enhydris
================

Install Enhydris by cloning it and then installing the requirements
specified in :file:`requirements.txt`, probably in a virtualenv, like
this::

    cd /opt
    git clone https://github.com/openmeteo/enhydris.git
    git checkout 3.0
    virtualenv --system-site-packages --python=/usr/bin/python3 \
        enhydris/venv
    ./enhydris/venv/bin/pip install -r enhydris/requirements.txt

You may or may not want to use the ``--system-site-packages`` parameter.
The main reason to use it is that it will then use your systemwide
``python3-gdal``, ``python3-pil`` and ``python3-pandas`` (and
``python3-psycopg2``, if you use PostgreSQL), which means it won't need
to compile these for the virtualenv.

Configuring Enhydris
====================

Create a Django settings file, either in
:file:`enhydris_project/settings/local.py`, or wherever you like. It
should begin with this::

    from enhydris_project.settings import *

and it then it should go on to override ``DEBUG``, ``SECRET_KEY``,
``DATABASES`` and ``STATIC_ROOT``. More settings you may want to
override are the `Django settings`_ and the :ref:`Enhydris settings
<settings>`.


Initializing the database
=========================

In order to initialize your database and create the necessary database
tables for Enhydris to run, run the following commands inside the
Enhydris configuration directory::

   python manage.py migrate
   python manage.py createsuperuser

The above commands will also ask you to create a Enhydris superuser.

.. note:: Using PostgreSQL+PostGIS

   If you use PostgreSQL+PostGIS, you need to create a spatially enabled
   database before running the commands above.

   (In the following examples, we use ``enhydris_db`` as the database
   name, and ``enhydris_user`` as the PostgreSQL username. The user
   should not be a super user, and not be allowed to create more users.
   In production, it should not be allowed to create databases; in
   testing, it should be allowed, in order to be able to run the unit
   tests.)

   The first step is to create a spatially enabled database template.

   Here is a **Debian Jessie example**::

      # Install PostgreSQL and PostGIS
      apt-get install postgis postgresql-9.4-postgis

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
      createdb --template template_postgis --owner enhydris_user \
         enhydris_db
      exit

   You may also need to edit your ``pg_hba.conf`` file as needed
   (under ``/var/lib/pgsql/data/`` or ``/etc/postgresql/9.x/main/``,
   depending on your system). The chapter on `client authentication`_
   of the PostgreSQL manual explains this in detail. A simple setup is
   to authenticate with username and password, in which case you
   should add or modify the following lines in ``pg_hba.conf``::

       local   all         all                               md5
       host    all         all         127.0.0.1/32          md5
       host    all         all         ::1/128               md5

   Restart the server to read the new ``pg_hba.conf`` configuration.
   For example::

       service postgresql restart

   .. _client authentication: http://www.postgresql.org/docs/9.4/static/client-authentication.html

   Here is a **Windows example**, assuming PostgreSQL is installed at
   the default location::
   
      cd C:\Program Files\PostgreSQL\9.4\bin
      createdb template_postgis
      psql -d template_postgis -c "CREATE EXTENSION postgis;"
      psql -d template_postgis -c "UPDATE pg_database SET datistemplate='true'
         WHERE datname='template_postgis';"
      createuser -U postgres --pwprompt enhydris_user
      createdb --template template_postgis --owner enhydris_user enhydris_db

   At some point, these commands will ask you for the password of the
   operating system user.


Running Enhydris
================

Inside the Enhydris configuration directory, run the following
command::

    python manage.py runserver

The above command will start the Django development server and set it
to listen to port 8000. If you then start your browser and point it to
``http://localhost:8000/``, you should see Enhydris in action. Note
that this only listens to the localhost; if you want it to listen on
all interfaces, use ``0.0.0.0:8000`` instead.

To use Enhydris in production, you need to setup a web server such as
apache. This is described in detail in `Deploying Django`_ and in
https://djangodeployment.com/.

.. _deploying django: http://docs.djangoproject.com/en/2.1/howto/deployment/


Post-install configuration: domain name
=======================================

After you run Enhydris, logon as a superuser, visit the admin panel,
go to ``Sites``, edit the default site, and enter your domain name
there instead of ``example.com``. Emails to users for registration
confirmation will contain links to that domain.  Restart the
Enhydris (by restarting apache/gunicorn/whatever) after changing the
domain name.

.. _settings:

Settings reference
==================
 
These are the settings available to Enhydris, in addition to the
`Django settings`_.

.. _django settings: http://docs.djangoproject.com/en/2.1/ref/settings/

.. data:: ENHYDRIS_FILTER_DEFAULT_COUNTRY

   When a default country is specified, the station search is locked
   within that country and the station search filter allows only searches
   in the selected country. If left blank, the filter allows all
   countries to be included in the search.

.. data:: ENHYDRIS_FILTER_POLITICAL_SUBDIVISION1_NAME
.. data:: ENHYDRIS_FILTER_POLITICAL_SUBDIVISION2_NAME 

   These are used only if :data:`FILTER_DEFAULT_COUNTRY` is set. They
   are the names of the first and the second level of political
   subdivision in a certain country.  For example, Greece is first
   divided in 'districts', then in 'prefecture', whereas the USA is
   first divided in 'states', then in 'counties'.

.. data:: ENHYDRIS_REGISTRATION_OPEN

   If ``True`` (the default), users can register, otherwise they have to
   be created by the administrator.

.. data:: ENHYDRIS_USERS_CAN_ADD_CONTENT

   If set to ``True``, it enables all logged in users to add stations to
   the site, and edit the data of the stations they have entered.  When
   set to ``False`` (the default), only privileged users are allowed to
   add/edit/remove data from the db.

.. data:: ENHYDRIS_SITE_CONTENT_IS_FREE

   If this is set to ``True``, all registered users have access to the
   timeseries and can download timeseries data. If set to ``False``
   (the default), the users may be restricted.

.. data:: ENHYDRIS_TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS

   Setting this option to ``True`` will enable all users to download
   timeseries data without having to login first. The default is
   ``False``.

.. data:: ENHYDRIS_MIN_VIEWPORT_IN_DEGS

   Set a value in degrees. When a geographical query has a bounding
   box with dimensions less than :data:`MIN_VIEWPORT_IN_DEGS`, the map
   will have at least a dimension of ``MIN_VIEWPORT_IN_DEGS²``. Useful
   when showing a single entity, such as a hydrometeorological
   station. Default value is 0.04, corresponding to an area
   approximately 4×4 km.

.. data:: ENHYDRIS_MAP_DEFAULT_VIEWPORT

   A tuple containing the default viewport for the map in geographical
   coordinates, in cases of geographical queries that do not return
   anything.  Format is (minlon, minlat, maxlon, maxlat) where lon and
   lat is in decimal degrees, positive for north/east, negative for
   west/south.

.. data:: ENHYDRIS_TIMESERIES_DATA_DIR

   The directory where the files with the time series data are stored;
   for example, ``/var/local/enhydris/timeseries_data``. You must
   specify this in production. The default is ``timeseries_data``,
   relative to the directory from which you start the server.

   You might choose to put that under :data:`MEDIA_ROOT`, but in that
   case all data might be publicly available, without permission
   checking.

.. data:: ENHYDRIS_TS_GRAPH_BIG_STEP_DENOMINATOR
          ENHYDRIS_TS_GRAPH_FINE_STEP_DENOMINATOR

   Chart options for time series details page. The big step represents
   the max num of data points to be plotted, default is 200. The fine
   step are the max num of points between main data points to search
   for a maxima, default is 50. 

.. data:: ENHYDRIS_SITE_STATION_FILTER

   This is a quick-and-dirty way to create a web site that only
   displays a subset of an Enhydris database. For example, the
   database of http://system.deucalionproject.gr/ is the same as that
   of http://openmeteo.org/; however, the former only shows stations
   relevant to the Deucalion project, because it has this setting::

      ENHYDRIS_SITE_STATION_FILTER = {'owner__id__exact': '9'}

.. data:: ENHYDRIS_DISPLAY_COPYRIGHT_INFO

   If ``True``, the station detail page shows copyright information
   for the station. By default, it is ``False``. If all the stations
   in the database belong to one organization, you probably want to
   leave it to ``False``. If the database is going to be openly
   accessed and contains data that belongs to many owners, you
   probably want to set it to ``True``.

.. data:: ENHYDRIS_WGS84_NAME

   Sometimes Enhydris displays the reference system of the
   co-ordinates, which is always WGS84. In some installations, it is
   desirable to show something other than "WGS84", such as "ETRS89".
   This parameter specifies the name that will be displayed; the
   default is WGS84.

   This is merely a cosmetic issue, which does not affect the actual
   reference system used, which is always WGS84. The purpose of this
   parameter is merely to enable installations in Europe to display
   "ETRS89" instead of "WGS84" whenever this is preferred. Given that
   the difference between WGS84 and ETRS89 is only a few centimeters,
   which is considerably less that the accuracy with which
   station co-ordinates are given, whether WGS84 or ETRS89 is
   displayed is actually irrelevant.

.. data:: ENHYDRIS_MAP_BASE_LAYERS

   A list of Javascript definitions of base layers to use on the map.
   The default is::

        [r'''OpenLayers.Layer.OSM.Mapnik("Open Street Map",
            {isBaseLayer: true,
            attribution: "Map by <a href='http://www.openstreetmap.org/'>OSM</a>"})''',
         r'''OpenLayers.Layer.OSM.CycleMap("Open Cycle Map",
            {isBaseLayer: true,
                attribution: "Map by <a href='http://www.openstreetmap.org/'>OSM</a>"})'''
        ]

.. data:: ENHYDRIS_MAP_BOUNDS

   A pair of points, each one being a pair of co-ordinates in WGS84; the first
   one is the bottom-left point and the second is the top-right. The default
   is Greece::

       ENHYDRIS_MAP_BOUNDS = ((19.3, 34.75), (29.65, 41.8))

   The bounds are automatically enlarged in order to encompass all registered
   objects, so this setting is useful only if there are no objects or a few
   objects.

.. data:: ENHYDRIS_MAP_MARKERS

   The map can show different station types with different markers. For
   example::

      ENHYDRIS_MAP_MARKERS = {
          '0': 'images/drop_marker.png',
          '1': 'images/drop_marker_cyan.png',
          '3': 'images/drop_marker_orange.png',
          '11': 'images/drop_marker_green.png',
      }
                                
   In the example above, stations whose type id is 3 will be shown with
   :file:`drop_marker_orange.png`, and any marker whose id is not one
   of 1, 3, or 11 will show with :file:`drop_marker.png`. The files
   are URLs; if they are relative, they are relative to
   :data:`STATIC_URL`.

   The default is::

      ENHYDRIS_MAP_MARKERS = {
          '0': 'images/drop_marker.png', 
      }

.. data:: ENHYDRIS_STATIONS_PER_PAGE

   Number of stations per page for the paginatin of the station list. The
   default is 100.
