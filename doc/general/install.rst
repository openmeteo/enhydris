.. _install:

==============================
Installation and configuration
==============================

.. highlight:: bash

Download Enhydris
=================

Download Enhydris from https://github.com/openmeteo/enhydris/ (if you
are uncomfortable with git and github, click on the "Download ZIP"
button).

Prerequisites
=============

===================================================== ============
Prerequisite                                          Version
===================================================== ============
Python                                                2.6 [1]
PostgreSQL                                            [2]
PostGIS                                               1.4 [3]
GDAL                                                  1.9
psycopg2                                              2.2 [4]
setuptools                                            0.6 [5]
pip                                                   1.1 [5]
PIL with freetype                                     1.1.7 [6]
Dickinson                                             0.1.0 [7]
The Python modules listed in :file:`requirements.txt` See file
===================================================== ============

.. admonition:: Note for production installations

   These prerequisites are for development installations. For
   production installations you also need a web server.

[1] Enhydris runs on Python 2.6 and 2.7. It should also run on
any later 2.x version. Enhydris does not run on Python 3.

[2] Enhydris should run on all supported PostgreSQL versions.  In
order to avoid possible incompatibilities with psycopg2, it is better
to use the version prepackaged by your operating system when running
on GNU/Linux, and to use the latest PostgreSQL version when running on
Windows. If there is a problem with your version of PostgreSQL, email
us and we'll check if it is easy to fix. 

[3] Except for PostGIS, more libraries, namely geos and proj, are
needed; however, you probably not need to worry about that, because in
most GNU/Linux distributions PostGIS has a dependency on them and
therefore they will be installed automatically, whereas in Windows the
installation file of PostGIS includes them. Enhydris is known to run
on PostGIS 1.4 and 1.5. It probably can run on later versions as well.
It is not known whether it can run on earlier versions.

[4] psycopg2 is listed in :file:`requirements.txt` together with the
other Python modules. However, in contrast to them, it can be tricky
to install (because it needs compilation and has a dependency on
PostgreSQL client libraries), and it is therefore usually better to
not leave its installation to :command:`pip`. It's better to install a
prepackaged version for your operating system.

[5] setuptools and pip are needed in order to install the rest of the
Python modules; Enhydris does not actually need it.

[6] PIL is not directly required by Enhydris, but by other python
modules required my Enhydris. In theory, installing the requirements
listed in :file:`requirements.txt` will indirectly result in
:command:`pip` installing it.  However, it can be tricky to install,
and it may be better to not leave its installation to :command:`pip`;
it's better to install a prepackaged version for your operating
system. It must be compiled with libfreetype support. This is common
in Linux distributions. In Windows, however, the `official packages`_
are not thus compiled. One solution is to get the unofficial version
from http://www.lfd.uci.edu/~gohlke/pythonlibs/. If there is any
difficulty, Pillow might work instead of PIL.

.. _official packages: http://www.pythonware.com/products/pil/

[7] Dickinson_ is not required directly by Enhydris, but by pthelma_,
which is required by Enhydris and is listed in
:file:`requirements.txt`.

.. _dickinson: http://dickinson.readthedocs.org/
.. _pthelma: http://pthelma.readthedocs.org/

.. admonition:: Example: Installing prerequisites on Debian/Ubuntu

   These instructions are for Debian wheezy. For Ubuntu they are similar,
   except that the postgis package version may be different::

      aptitude install python postgresql postgis postgresql-9.1-postgis \
          python-psycopg2 python-setuptools git python-pip python-imaging \
          python-gdal

      # Install Dickinson
      cd /tmp
      wget https://github.com/openmeteo/dickinson/archive/0.1.0.tar.gz
      tar xzf 0.1.0.tar.gz
      cd dickinson-0.1.0
      ./configure
      make
      sudo make install

      pip install -r requirements.txt

   It is a good idea to use a virtualenv before running the last
   command, but you are on your own with that, sorry.

.. admonition:: Example: Installing prerequisites on Windows

   .. admonition:: Important

      We don't support Enhydris very well on Windows. We do provide
      instructions, and we do fix bugs, but honestly we can't install
      it; we get an error message related to "geos" at some point.
      Some people have had success by installing Enhydris using
      OSGeo4W_, but we haven't tried it. So, if you face installation
      problems, we won't be able to help (unless you provide funding).

      Also note that we don't think Enhydris on Windows can easily run
      on 64-bit Python or 64-bit PostgreSQL; the 32-bit versions of
      everything should be installed. This is because some
      prerequisites are not available for Windows in 64-bit versions,
      or they may be difficult to install. Such dependencies are
      PostGIS and some Python packages.

      That said, we provide instructions below on how it should (in
      theory) be installed. If you choose to use OSGeo4W_, some things
      will be different - you are on your own anyway.

      .. _OSGeo4W: http://osgeo4w.osgeo.org/

   Download and install the latest Python 2.x version from
   http://python.org/ (use the Windows Installer package).

   Add the Python installation directory (such as
   :file:`C:\\Python27`) and its :file:`Scripts` subdirectory (such as
   :file:`C:\\Python27\\Scripts`) to the system path (right-click on
   My Computer, Properties, Advanced, Environment variables, under
   "System variables" double-click on Path, and add the two new
   directory names at the end, using semicolon to delimit them).
      
   Download and install an appropriate PostgreSQL version from
   http://postgresql.org/ (use a binary Windows installer). Important:
   at some time the installer will create an operating system user and
   ask you to define a password for that user; keep the password; you
   will need it later.

   Go to Start, All programs, PostgreSQL, Application Stack Builder,
   select your PostgreSQL installation on the first screen, then, on
   the application selection screen, select Spatial Extensions,
   PostGIS. Allow it to install (you don't need to create a spatial
   database at this stage).

   Download and install psycopg2 for Windows from
   http://www.stickpeople.com/projects/python/win-psycopg/.

   Download and install setuptools from
   http://pypi.python.org/pypi/setuptools (you probably need to go to
   http://pypi.python.org/pypi/setuptools#files and pick the .exe file
   that corresponds to your Python version).

   Download and install PIL from http://www.lfd.uci.edu/~gohlke/pythonlibs/.

   Download the latest dickinson DLL from
   http://openmeteo.org/downloads/ and put it in
   :file:`C:\\Windows\\System32\\dickinson.dll`.

   Finally, open a Command Prompt and give the following commands
   inside the downloaded and unpacked :file:`enhydris` directory::

       easy_install pip
       pip install -r requirements.txt

Creating a spatially enabled database
=====================================

You need to create a database user and a spatially enabled database
(we use ``enhydris_user`` and ``enhydris_db`` in the examples below).
Enhydris will be connecting to the database as that user. The user
should not be a super user, not be allowed to create databases, and
not be allowed to create more users.

.. admonition:: GNU example

   First, you need to create a spatially enabled database template. For
   PostGIS 2.0 or later (for earlier version refer to the GeoDjango
   instructions)::

      sudo -u postgres -s
      createdb template_postgis
      psql -d template_postgis -c "CREATE EXTENSION postgis;"
      psql -d template_postgis -c \
         "UPDATE pg_database SET datistemplate='true' \
         WHERE datname='template_postgis';"
      exit

   The create the database::

      sudo -u postgres -s
      createuser --pwprompt enhydris_user
      createdb --template template_postgis --owner enhydris_user \
         enhydris_db
      exit

   You may also need to edit your ``pg_hba.conf`` file as needed
   (under ``/var/lib/pgsql/data/`` or ``/etc/postgresql/8.x/main/``,
   depending on your system). The chapter on `client authentication`_
   of the PostgreSQL manual explains this in detail. A simple setup is
   to authenticate with username and password, in which case you
   should add or modify the following lines in ``pg_hba.conf``::

       local   all         all                               md5
       host    all         all         127.0.0.1/32          md5
       host    all         all         ::1/128               md5

   Restart the server to read the new ``pg_hba.conf`` configuration.
   For example, in Ubuntu::

       service postgresql restart

   .. _client authentication: http://www.postgresql.org/docs/8.4/static/client-authentication.html


.. admonition:: Windows example

   Assuming PostgreSQL is installed at the default location, run these
   at a command prompt::
   
      cd C:\Program Files\PostgreSQL\9.0\bin
      createdb template_postgis
      psql -d template_postgis -c "CREATE EXTENSION postgis;"
      psql -d template_postgis -c "UPDATE pg_database SET datistemplate='true'
         WHERE datname='template_postgis';"
      createuser -U postgres --pwprompt enhydris_user
      createdb --template template_postgis --owner enhydris_user enhydris_db

   At some point, these commands will ask you for the password of the
   operating system user.

Configuring Enhydris
====================

In the directory :file:`enhydris/settings`, copy the file
:file:`example.py` to :file:`local.py`.  Open
:file:`local.py` in an editor and make the following changes:

* Set :data:`ADMINS` to a list of admins (the administrators will get
  all enhydris exceptions by mail and also all user emails, as
  generated by the contact application).
* Under :data:`DATABASES`, set :data:`NAME` to the name of the
  database, and :data:`USER` and :data:`PASSWORD` according to the
  user created above.

Initializing the database
=========================

In order to initialize your database and create the necessary database
tables for Enhydris to run, run the following commands inside the
:file:`enhydris` directory::

   python manage.py syncdb --settings=enhydris.settings.local --noinput
   python manage.py migrate --settings=enhydris.settings.local dbsync
   python manage.py migrate --settings=enhydris.settings.local hcore
   python manage.py createsuperuser --settings=enhydris.settings.local 

The above commands will also ask you to create a Enhydris superuser.

.. admonition:: Confused by users?

   There are operating system users, database users, and Enhydris
   users. PostgreSQL runs as an operating system user, and so does the
   web server, and so does Django and therefore Enhydris. Now the
   application (i.e. Enhydris/Django) needs a database connection to
   work, and for this connection it connects to the database as a
   database user.  For the end users, that is, for the actual people
   who use Enhydris, Enhydris/Django keeps a list of usernames and
   passwords in the database, which have nothing to do with operating
   system users or database users. The Enhydris superuser created by
   the ``./manage.py createsuperuser`` command is such an Enhydris
   user, and is intended to represent a human.

   Advanced Django administrators can also use `alternative
   authentication backends`_, such as LDAP, for storing the Enhydris
   users.

.. _alternative authentication backends: http://docs.djangoproject.com/en/1.1/topics/auth/#other-authentication-sources

..
   FIXME: Either update or delete the following

   Initialize the database using old data
   --------------------------------------

   *** Probably Deprecated. Better ask for the json file of the data!**

   Under the migration directory there are 3 scripts which take care of migrating
   data from the old hydroscope schema to the new one. If the initial sql
   file contains data in this schema a few additional steps are required in order
   to update the schema to the current version. 

   If you want to import an old sql file, be sure to import the ``sql`` file
   first by running:: 

           psql -h localhost hydrotest hydro < hydro.sql

   and **THEN** run::

           ./manage.py syncdb --settings=enhydris.settings.local --all

   Also make sure that when you are asked whether to create a superuser you answer NO!
   You can create the superuser **after** the migrations are completed. 

   By using south, Enhydris takes care of data migrations. If the data have
   been produced by the migration scripts, they correspond to the 0001 migration
   (named initial). So, in case you already have the data in this schema, before
   applying new updates you need to tell south that the first migration (0001)
   has already been completed and after that apply all the additional changes. In
   order to do that, after running the psql command, you issue the following:: 

           ./manage.py migrate --settings=enhydris.settings.local hcore 0001 --fake
           ./manage.py migrate --settings=enhydris.settings.local hcore


   After that, you may also create a super user by running::

           ./manage.py createsuperuser --settings=enhydris.settings.local 


   Initial Data
   ~~~~~~~~~~~~

   After all hcore models are up to date, you may proceed with  loading the initial 
   data needed. All initial data are stored in json formatted text files which
   you can acquire by asking the right people. 

   In order to load the actual data, issue the following command: ::

           ./manage.py loaddata --settings=enhydris.settings.local hcore.json 
           

Running Enhydris
================

Inside the :file:`openmeteo/enhydris` directory, run the following
command::

    python manage.py runserver --settings=enhydris.settings.local 8088

The above command will start the Django development server and set it
to listen to port 8088. If you then start your browser and point it to
``http://localhost:8088/``, you should see Enhydris in action. Note
that this only listens to the localhost; if you want it to listen on
all interfaces, use ``0.0.0.0:8088`` instead.

To use Enhydris in production, you need to setup a web server such as
apache. This is described in detail in `Deploying Django`_.

.. _deploying django: http://docs.djangoproject.com/en/1.5/howto/deployment/


Post-install configuration
==========================

Domain name
-----------

.. FIXME: Is it really necessary to restart the web server?

After you run Enhydris, logon as a superuser, visit the admin panel,
go to ``Sites``, edit the default site, and enter your domain name
there instead of ``example.com``. Emails to users for registration
confirmation will appear to be coming from that domain.  Restart the
webserver after changing the domain name.

.. _settings:

Settings reference
==================
 
These are the settings available to Enhydris, in addition to the
`Django settings`_.

.. _django settings: http://docs.djangoproject.com/en/1.5/ref/settings/

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

.. data:: ENHYDRIS_USERS_CAN_ADD_CONTENT

   This must be configured before syncing the database. If set to
   ``True``, it enables all logged in users to add content to the site
   (stations, instruments and timeseries). It enables the use of user
   space forms which are available to all registered users and also
   allows editing existing data. When set to ``False`` (the default),
   only privileged users are allowed to add/edit/remove data from the
   db.

.. data:: ENHYDRIS_SITE_CONTENT_IS_FREE

   If this is set to ``True``, all registered users have access to the
   timeseries and can download timeseries data. If set to ``False``
   (the default), the users may be restricted.


.. data:: ENHYDRIS_TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS

   Setting this option to ``True`` will enable all users to download
   timeseries data without having to login first. The default is
   ``False``.

.. data:: ENHYDRIS_STORE_TSDATA_LOCALLY

   **Deprecated.**

   By default, this is ``True``. If set to ``False``, the installation
   does not store the actual time series records. The purpose of this
   setting is to be used together with the `dbsync` application, in
   order to create a website that contains the collected data (except
   time series records) of several other Enhydris installations (see
   the ``hcore_remotesyncdb`` management command).
   However, all this is under reconsideration.

.. data:: ENHYDRIS_REMOTE_INSTANCE_CREDENTIALS 

   If the instance is configured as a data aggregator and doesn't have
   the actual data locally stored, in order to fetch the data from
   another instance a user name and password must be provided which
   correspond to a superuser account in the remote instance. Many
   instances can be configured using this setting, each with its own
   user/pass combination following this scheme::

      ENHYDRIS_REMOTE_INSTANCE_CREDENTIALS = {
        'kyy.hydroscope.gr': ('myusername','mypassword'),
        'itia.hydroscope.gr': ('anotheruser','anotherpass')
      }

.. data:: ENHYDRIS_MIN_VIEWPORT_IN_DEGS

   Set a value in degrees. When a geographical query has bounds with
   dimensions less than :data:`MIN_VIEWPORT_IN_DEGS`, the map will have at
   least a dimension of ``MIN_VIEWPORT_IN_DEGS²``. Useful when showing
   a single entity, such as a hydrometeorological station. Default
   value is 0.04, corresponding to an area approximately 4×4 km.

.. data:: ENHYDRIS_MAP_DEFAULT_VIEWPORT

   A tuple containing the default viewport for the map in geographical
   coordinates, in cases of geographical queries that do not return
   anything.  Format is (minlon, minlat, maxlon, maxlat) where lon and
   lat is in decimal degrees, positive for north/east, negative for
   west/south.

.. data:: ENHYDRIS_TS_GRAPH_CACHE_DIR

   The directory in which timeseries graphs are cached. It is
   automatically created if it does not exist. The default is
   subdirectory :file:`enhydris-timeseries-graphs` of the system or
   user temporary directory.

.. data:: ENHYDRIS_TS_GRAPH_BIG_STEP_DENOMINATOR
          ENHYDRIS_TS_GRAPH_FINE_STEP_DENOMINATOR

   Chart options for time series details page. The big step represents
   the max num of data points to be plotted, default is 200. The fine
   step are the max num of points between main data points to search
   for a maxima, default is 50. 

.. data:: ENHYDRIS_SITE_STATION_FILTER

   This is a quick-and-dirty way to create a web site that only
   displays a subset of an Enhydris database. For example, the
   database of http://deucalionproject.gr/db/ is the same as that of
   http://openmeteo.org/db/; however, the former only shows stations
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
