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
PostgreSQL + PostGIS
GDAL                                                  1.9 [2]
node.js + yarn                                        [3]
===================================================== ============

[1] Enhydris runs on Python 3.5 or later.  It does not run on Python 2.
setuptools and pip are needed in order to install the rest of the Python
modules.

[2] In theory, installing the prerequisites with :command:`pip` will
also install gdal. However it can be tricky to install and it's
usually easier to install a prepackaged version for your operating
system.

[3] Production doesn't need node.js and yarn, but they are needed to
compile the Javascript.

.. note::

   Example: Installing prerequisites on Debian/Ubuntu

   ::

      apt install python3 postgresql-9.6-postgis-2.3 python3-psycopg2 \
          python3-pip python3-gdal

Install Enhydris
================

Install Enhydris by cloning it and then installing the requirements
specified in :file:`requirements.txt`, probably in a virtualenv::

    git clone https://github.com/openmeteo/enhydris.git
    git checkout 3.0
    virtualenv --system-site-packages --python=/usr/bin/python3 \
        enhydris/venv
    ./enhydris/venv/bin/pip install -r enhydris/requirements.txt
    ./enhydris/venv/bin/pip install -r enhydris/requirements-dev.txt

Configure the backend
=====================

Create a Django settings file, either in
:file:`enhydris_project/settings/local.py`, or wherever you like. It
should begin with this::

    from enhydris_project.settings.development import *

and it then it should go on to override ``DEBUG``, ``SECRET_KEY``,
``DATABASES`` and ``STATIC_ROOT``. More settings you may want to
override are the `Django settings`_ and the :ref:`Enhydris backend
settings <backend_settings>`.

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

Here is a **Debian stretch example**::

   # Install PostgreSQL and PostGIS
   apt install postgis postgresql-9.6-postgis-2.3

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

Here is a **Windows example**, assuming PostgreSQL is installed at
the default location::

   cd C:\Program Files\PostgreSQL\9.6\bin
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

Start the backend
=================

Inside the Enhydris configuration directory, run the following
command::

    python manage.py runserver

The above command will start the Django development server and set it
to listen to port 8000.

Configure and start the frontend
================================

::

    cd frontend

Copy ``.env.sample`` to ``.env`` and change ``API_ROOT`` to
``http://localhost:8000/api/`` (for other settings see the
backend_settings_).

Install the front-end dependencies::

    yarn install

Run a development server on port 3000::

    yarn dev

That's it. You can visit Enhydris at http://localhost:3000/.

Production
==========

To use Enhydris in production, you need to setup a web server such as
apache. This is described in detail in `Deploying Django`_ and in
https://djangodeployment.com/.

For the frontend, instead of ``yarn dev``, execute ``yarn generate``;
this will compile (transpile) the JavaScript and create several static
files in the `dist` directory. You must put these files in the
top-level directory of your web site, such as ``/var/www/mysite``.
Configure your web server to send ``/api/`` and ``/admin/`` to Django,
and serve the rest from static files.

.. _deploying django: http://docs.djangoproject.com/en/2.1/howto/deployment/

Post-install configuration: domain name
=======================================

After you run Enhydris, logon as a superuser, visit the admin panel,
go to ``Sites``, edit the default site, and enter your domain name
there instead of ``example.com``. Emails to users for registration
confirmation will contain links to that domain.  Restart the
Enhydris (by restarting apache/gunicorn/whatever) after changing the
domain name.

.. _backend_settings:

Backend settings reference
==========================
 
These are the settings available to Enhydris, in addition to the
`Django settings`_.

.. _django settings: http://docs.djangoproject.com/en/2.1/ref/settings/

.. data:: ENHYDRIS_REGISTRATION_OPEN

   If ``True`` (the default), users can register, otherwise they have to
   be created by the administrator.

.. data:: ENHYDRIS_USERS_CAN_ADD_CONTENT

   If set to ``True``, it enables all logged in users to add stations to
   the site, and edit the data of the stations they have entered.  When
   set to ``False`` (the default), only privileged users are allowed to
   add/edit/remove data from the db.

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

.. data:: ENHYDRIS_SITE_STATION_FILTER

   This is a quick-and-dirty way to create a web site that only
   displays a subset of an Enhydris database. For example, the
   database of http://system.deucalionproject.gr/ is the same as that
   of http://openmeteo.org/; however, the former only shows stations
   relevant to the Deucalion project, because it has this setting::

      ENHYDRIS_SITE_STATION_FILTER = {'owner__id__exact': '9'}

.. _frontend_settings:

Frontend settings reference
===========================

.. data:: API_ROOT

   The URL of the backend; for example, ``https://openmeteo.org/api/``
   or ``http://localhost:8000/api/``.
