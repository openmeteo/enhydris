.. _install:

=======================================
Enhydris installation and configuration
=======================================

Prerequisites
=============

===================== =======
Prerequisite          Version
===================== =======
Python                2.6 [1]
PostgreSQL            8.3 [2]
PostGIS               1.4 [3]
psycopg2              2.2 [9]
setuptools            0.6 [5]
PIL with freetype     1.1.7 [14]
Django                1.4 [4]
django-registration   0.7 [13]
django-pagination     1.0 [4]
django-extensions     0.6 [8]
django-rest-framework 2.2.1 [4]
south                 0.7 [4]
django-notify         1.1 [4]
django-ajax-selects   1.2.5 [4]
json [10]                   
Mercurial [11]
python-markdown
===================== =======

.. admonition:: Note for production installations

   These prerequisites are for development installations. For
   production installations you also need a web server.

[1] Enhydris runs on Python 2.6 and 2.7. It should also run on
any later 2.x version. Enhydris does not run on Python 3.

[2] Enhydris is known to run on PostgreSQL 8.4 and 9.1, and it should also run
without problem on PostgreSQL 8.3. In order to avoid possible
incompatibilities with psycopg2, it is better to use the version
prepackaged by your operating system when running on GNU/Linux, and to
use the latest PostgreSQL version when running on Windows. If there is
a problem with your version of PostgreSQL, email us and we'll try to
check if it is easy to fix. 

[3] Except for PostGIS, more libraries, namely geos and proj, are
needed; however, you probably not need to worry about that, because in
most GNU/Linux distributions PostGIS has a dependency on them and
therefore they will be installed automatically, whereas in Windows the
installation file of PostGIS includes them. Enhydris is known to run
on PostGIS 1.4 and 1.5. It probably can run on later versions as well.
It is not known whether it can run on earlier versions.

[4] The table indicates the versions of various Python and Django
modules on which Enhydris is known to run. Usually it can run on later
versions as well.

[5] setuptools is needed in order to install the rest of the Python
modules; Enhydris does not actually need it.

[8] Enhydris is also known to run on earlier django-extensions;
however, some tests fail in that case.

[9] Because of a `Django bug`_ which is present in Django versions up
to and including 1.3, tests fail on psycopg2 2.4.2 or later. Therefore
you should either use Django 1.4 or later, or psycopg2 no later than
2.4.1, or not expect the tests to run.

.. _Django bug: https://code.djangoproject.com/ticket/16250

[10] json is included in Python 2.6 or later.

[11] Mercurial is needed in order to download openmeteo software, not
for running it.

[13] django-registration 0.8 does not work properly with this version of
enhydris (this may be an enhydris bug).

[14] The Python Imaging Library (PIL) must be compiled with libfreetype
support. This is common in Linux distributions. In Windows, however, the
`official packages`_ are not thus compiled. One solution is to get the
unofficial version from http://www.lfd.uci.edu/~gohlke/pythonlibs/.

.. _official packages: http://www.pythonware.com/products/pil/

.. admonition:: Example: Installing prerequisites on Debian/Ubuntu

   These instructions are for Debian squeeze. For Ubuntu they are similar,
   except that the postgis package version may be different::

       aptitude install python postgresql postgis postgresql-8.4-postgis \
           python-psycopg2 python-setuptools mercurial python-markdown \
           python-pip python-imaging
       pip install django==1.4.2 django-registration==0.7 \
           "django-pagination>=1.0,<1.1" django-extensions==0.6 \
           djangorestframework==2.2.1 south==0.7 django-notify==1.1 \
           "django-ajax-selects>=1.2,<1.3"

.. admonition:: Example: Installing prerequisites on Windows

   .. admonition:: Important

      We don't support Enhydris very well on Windows. We do provide
      instructions, and we do fix bugs, but honestly we can't install
      it; we get an error message related to "geos" at some point.
      Some people have had success by installing Enhydris using
      OSGeo4W_, but we haven't tried it. So, if you face installation
      problems, we won't be able to help (unless you provide funding).

      Also note that we don't think Enhydris can easily run on 64-bit
      Python or 64-bit PostgreSQL; the 32-bit versions of everything
      should be installed. This is because many prerequisites are not
      available in 64-bit versions, or they may be difficult to
      install. Such dependencies are PostGIS and some Python packages.

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
      
   Download and install an appropriate PostgreSQL version (8.4 and 9.0
   are known to work) from http://postgresql.org/ (use a binary Windows
   installer). Important: at some time the installer will create an
   operating system user and ask you to define a password for that user;
   keep the password; you will need it later.

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

   Download and install the Windows Installer package of TortoiseHg
   with Mercurial from http://mercurial.selenic.com/downloads/.

   Finally, open a Command Prompt and give the following commands::

       easy_install pip
       pip install django==1.4.2 
       pip install django-registration==0.7 "django-pagination>=1.0,<1.1"
       pip install django-extensions==0.6 djangorestframework==2.2.1
       pip install south==0.7 django-notify==1.1 "django-ajax-selects>=1.2,<1.3"

Creating a database
===================

You need to create a database user and a database (we use
``enhydris_user`` and ``enhydris_db`` in the examples below). Enhydris
will be connecting to the database as that user. The user should not
be a super user, not be allowed to create databases, and not be
allowed to create more users.

.. admonition:: GNU example

   ::

      sudo -u postgres -s
      createuser --pwprompt enhydris_user
      createdb --owner enhydris_user enhydris_db
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
      createuser -U postgres --pwprompt enhydris_user
      createdb -U postgres --owner enhydris_user enhydris_db

   At some point, these commands will ask you for the password of the
   operating system user.

Spatially enabling the database
===============================

Assuming the database is called "enhydris_db" and the user is
"enhydris_user", run the following::

   createlang -U postgres plpgsql enhydris_db
   psql -d enhydris_db -U postgres -f postgis.sql
   psql -d enhydris_db -U postgres -f postgis_comments.sql
   psql -d enhydris_db -U postgres -f spatial_ref_sys.sql
   psql -U postgres enhydris_db
     grant select on spatial_ref_sys to enhydris_user;
     grant all on geometry_columns to enhydris_user;
     \q

The location of the files :file:`postgis.sql`,
:file:`postgis_comments.sql` and :file:`spatial_ref_sys.sql` depends
on your installation. In Ubuntu 10.10 they are at
:file:`/usr/share/postgresql/8.4/contrib/`. In Windows, they are
somewhere like
:file:`C:\\Program Files\\PostgreSQL\\9.0\\share\\contrib\\postgis-1.5`;
also note that for these commands to run you must be in the PostgreSQL
bin directory, or have it in the path.

Getting the software
====================

Clone the Mercurial repository http://openmeteo.org/openmeteo.

.. admonition:: GNU example

   ::

      hg clone http://openmeteo.org/openmeteo

   This will create a :file:`openmeteo` directory inside the current
   directory, which should be somewhere inside your home directory for
   a development instance, or :file:`/usr/local` for a production
   instance.

.. admonition:: Windows example

   Go to the folder in which you want to download the software,
   right-click on the empty space, and choose TortoiseHg, Clone (if
   these options do not appear, it may be that you did not restart the
   machine after installing TortoiseHg). In the Source path field,
   specify http://openmeteo.org/openmeteo. Hit the Clone button.

Installing Dickinson and pthelma
================================

Dickinson is a shared library (a DLL in Windows parlance) which you
need to compile and install. Instructions for that are in the
downloaded :file:`openmeteo/dickinson/README` file.

.. admonition:: Note for Windows users who want to avoid compiling

   We occasionally compile the DLL and make the compiled version
   available at http://openmeteo.org/downloads/. The file is named
   something like :file:`dickinson-x86-rXXX.dll`. This means that it
   is the compiled file that corresponds to repository revision XXX.
   Right-click on your openmeteo directory and select "Hg Repository
   Explorer"; the current revision of your directory will be at the
   top of the list.  If there is a difference, the compiled version we
   provide may still work; this will be the case when there has been
   no change in pthelma or dickinson between the two revisions. If at
   all in doubt, go ahead and compile it. Otherwise, download
   :file:`dickinson-x86-rXXX.dll`, rename it to
   :file:`dickinson.dll`, and put it somewhere where the system can
   find it, such as :file:`C:\\Windows\\System32`.

Pthelma is a Python library. You can install it system wide by running
:command:`python setup.py install` inside the :file:`openmeteo/pthelma`
directory, but it is recommended to not install it, and instead to use
it directly from the :file:`openmeteo/pthelma`
directory. To do this, set the :envvar:`PYTHONPATH` environment
variable to the :file:`openmeteo/pthelma` directory.

.. admonition:: Bash example

   Assuming the :file:`openmeteo` directory is in your home directory::

      export PYTHONPATH=~/openmeteo/pthelma

   Instead of the above, what I actually do is prefix commands with
   the environment variable; for example, to run the Django
   development server::

      PYTHONPATH=~/openmeteo/pthelma ./manage.py runserver

   This has the added benefit that it works even if there are many
   openmeteo instances on my system.

.. admonition:: Windows example

   Assuming the :file:`openmeteo` directory is on your Desktop::

      set PYTHONPATH=C:\Documents and settings\%USERNAME%\Desktop\openmeteo\pthelma

Configuring Enhydris
====================

In the directory :file:`openmeteo/enhydris`, copy the file
:file:`settings-example.py` to :file:`settings.py`, and copy the file
:file:`urls-example.py` to :file:`urls.py`.  Open :file:`settings.py`
in an editor and make the following changes:

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
:file:`openmeteo/enhydris` directory::

   python manage.py syncdb --noinput
   python manage.py migrate dbsync
   python manage.py migrate hcore
   python manage.py createsuperuser

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

           ./manage.py syncdb --all

   Also make sure that when you are asked whether to create a superuser you answer NO!
   You can create the superuser **after** the migrations are completed. 

   By using south, Enhydris takes care of data migrations. If the data have
   been produced by the migration scripts, they correspond to the 0001 migration
   (named initial). So, in case you already have the data in this schema, before
   applying new updates you need to tell south that the first migration (0001)
   has already been completed and after that apply all the additional changes. In
   order to do that, after running the psql command, you issue the following:: 

           ./manage.py migrate hcore 0001 --fake
           ./manage.py migrate hcore


   After that, you may also create a super user by running::

           ./manage.py createsuperuser


   Initial Data
   ~~~~~~~~~~~~

   After all hcore models are up to date, you may proceed with  loading the initial 
   data needed. All initial data are stored in json formatted text files which
   you can acquire by asking the right people. 

   In order to load the actual data, issue the following command: ::

           ./manage.py loaddata hcore.json 
           

Running Enhydris
================

Inside the :file:`openmeteo/enhydris` directory, run the following
command::

    python manage.py runserver 8088

The above command will start the Django development server and set it
to listen to port 8088. If you then start your browser and point it to
``http://localhost:8088/``, you should see Enhydris in action. Note
that this only listens to the localhost; if you want it to listen on
all interfaces, use ``0.0.0.0:8088`` instead.

To use Enhydris in production, you need to setup a web server such as
apache. This is described in detail in `Deploying Django`_.

.. _deploying django: http://docs.djangoproject.com/en/1.4/howto/deployment/


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

.. _django settings: http://docs.djangoproject.com/en/1.1/ref/settings/

.. data:: FILTER_DEFAULT_COUNTRY

   When a default country is specified, the station search is locked
   within that country and the station search filter allows only searches
   in the selected country. If left blank, the filter allows all
   countries to be included in the search.

.. data:: FILTER_POLITICAL_SUBDIVISION1_NAME
.. data:: FILTER_POLITICAL_SUBDIVISION2_NAME 

   These are used only if :data:`FILTER_DEFAULT_COUNTRY` is set. They
   are the names of the first and the second level of political
   subdivision in a certain country.  For example, Greece is first
   divided in 'districts', then in 'prefecture', whereas the USA is
   first divided in 'states', then in 'counties'.

.. data:: GENTITYFILE_DIR

   This is the directory that all gentity files will be uploaded to and
   consequently served from. The default for this is
   ``/site_media/gentityfile/``.

.. data:: USERS_CAN_ADD_CONTENT

   This must be configured before syncing the database. If set to
   ``True``, it enables all logged in users to add content to the site
   (stations, instruments and timeseries). It enables the use of user
   space forms which are available to all registered users and also
   allows editing existing data. When set to ``False``, only
   privileged users are allowed to add/edit/remove data from the db.

.. data:: SITE_CONTENT_IS_FREE

   If this is set to ``True``, all registered users have access to the
   timeseries and can download timeseries data. If set to ``False``,
   the users may be restricted.


.. data:: TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS

   Setting this option to ``True`` will enable all users to download
   timeseries data without having to login first.

.. data:: STORE_TSDATA_LOCALLY

   This options controls whether this specific instance can store
   timeseries data locally. When set to ``True``, users can upload
   timeseries data to the site (possibly priviliged users, depending
   on :data:`USERS_CAN_ADD_CONTENT`).  If set to ``False``, the instance
   is configured to act as a data aggregator of other instances. This
   means that timeseries data are not stored locally and users cannot
   upload data in this instance. This is used to serve existing data
   from other instances which are aggregated using the
   ``hcore_remotesyncdb`` management command.

.. data:: REMOTE_INSTANCE_CREDENTIALS 

   If the instance is configured as a data aggregator and doesn't have
   the actual data locally stored, in order to fetch the data from
   another instance a user name and password must be provided which
   correspond to a superuser account in the remote instance. Many
   instances can be configured using this setting, each with its own
   user/pass combination following this scheme::

      REMOTE_INSTANCE_CREDENTIALS = {
        'kyy.hydroscope.gr': ('myusername','mypassword'),
        'itia.hydroscope.gr': ('anotheruser','anotherpass')
      }

.. data:: USE_OPEN_LAYERS

   Set this to :const:`False` to disable the map.

.. data:: MIN_VIEWPORT_IN_DEGS

   Set a value in degrees. When a geographical query has bounds with
   dimensions less than :data:`MIN_VIEWPORT_IN_DEGS`, the map will have at
   least a dimension of ``MIN_VIEWPORT_IN_DEGS²``. Useful when showing
   a single entity, such as a hydrometeorological station. Default
   value is 0.04, corresponding to an area approximately 4×4 km.

.. data:: MAP_DEFAULT_VIEWPORT

   A tuple containing the default viewport for the map in geographical
   coordinates, in cases of geographical queries that do not return
   anything.  Format is (minlon, minlat, maxlon, maxlat) where lon and
   lat is in decimal degrees, positive for north/east, negative for
   west/south.

.. data:: TS_GRAPH_CACHE_DIR

   The directory in which timeseries graphs are cached. It is
   automatically created if it does not exist. The default is
   subdirectory :file:`enhydris-timeseries-graphs` of the system or
   user temporary directory.

.. data:: TS_GRAPH_BIG_STEP_DENOMINATOR
          TS_GRAPH_FINE_STEP_DENOMINATOR

   Chart options for time series details page. The big step represents
   the max num of data points to be plotted, default is 200. The fine
   step are the max num of points between main data points to search
   for a maxima, default is 50. 
