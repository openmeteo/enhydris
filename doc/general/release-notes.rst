.. _release-notes:

=============
Release notes
=============

.. highlight:: bash

Versions later than 1.0
=======================

Upgrading
---------

If you are already running Enhydris version 1.0 or later, you can upgrade to
any later 1.x version with this procedure:

1. Backup your database (you are not going to use this backup unless
   something goes wrong and you need to restore everything to the
   state it was before).

2. Install the new version and execute the database upgrade procedure::

      python manage.py migrate

Changes in 1.x minor- and micro- versions
-----------------------------------------

- Version 1.1.0 changes an internal API;
  :meth:`enhydris.hcore.models.Timeseries.get_all_data()` is renamed to
  :meth:`enhydris.hcore.models.Timeseries.get_data()` and accepts arguments to
  specify a start and end date.
- Version 1.1.1 puts the navbar inside a {% block %}, so that it can be
  overriden in custom skins.

Version 1.0
===========

Overview
--------

This version has important internal changes, but no change in
functionality (except for the fix of a minor bug, that the time series
chart would apparently "hang" with a waiting cursor showing for ever
when a time series was empty). These important changes are:

- Python 3 is now supported, and there is no more support for Python 2.

- Pthelma is not used anymore; instead, there is a dependency on
  ``pandas`` and on the new ``pd2hts`` module.

Upgrading from 0.8
------------------

Make sure you are running Enhydris 0.8. Discard your virtualenv and
follow the Enhydris installation instructions to install the necessary
operating system packages and install Enhydris in a new Python 3
virtualenv. You don't need to change anything in the configuration or
perform any database migration.

Changes in 1.0 microversions
----------------------------

- When downloading time series and specifying a start date, the
  resulting time series could start on a slightly different start date
  because of some confusion with the time zone. The bug was fixed in
  1.0.1.
- Gentity files could not be downloading because of a bug in the downloading
  code. Fixed in 1.0.2.

Version 0.8
===========

Overview
--------

- The time series data are now stored in files instead of in database
  blobs. They are stored uncompressed, which means that much more disk
  space is consumed, but it has way more benefits. If disk space is
  important to you, use a file system with transparent compression.

- Experimental spatialite support.

Upgrading from 0.6
------------------

The upgrade procedure is slightly complicated, and uses the intermediate
Enhydris version 0.7, which exists only for this purpose.

(Note for developers: the reason for this procedure is that the
migrations have been reset. Previously the migrations contained
PostgreSQL-specific stuff.)

The upgrade procedure is as follows:

1. Backup your database, your media files, and your configuration (you
   are not going to use this backup unless something goes wrong and you
   need to restore everything to the state it was before).

2. Make sure you are running Enhydris 0.6.

3. Follow the Enhydris 0.8 installation instructions to install
   Enhydris in a new virtualenv; however, rather than installing
   Enhydris 0.8, install, instead, Enhydris 0.7, like this::

       pip install 'enhydris>=0.7,<0.8'

4. Open your ``settings.py`` and add the configuration setting
   :data:`ENHYDRIS_TIMESERIES_DATA_DIR`. Make sure your server has
   enough space for that directory (four times as much as your current
   database, and possibly more), and that it will be backing it up.

5. Apply the database upgrades::

       python manage.py migrate

6. Install Enhydris 0.8::

       pip install --upgrade --no-deps 'enhydris>=0.8,<0.9'

7. Have your database password ready and run the following to empty
   the `django_migrations` database table::

       python manage.py dbshell
       delete from django_migrations;
       \q

8. Repopulate the `django_migrations` table::

       python manage.py migrate --fake


Version 0.6
===========

Overview
--------

- The skin overhaul has been completed.

- The confusing fields "Nominal offset" and "Actual offset" have been
  renamed to "Timestamp rounding" and "Timestamp offset". For this,
  pthelma>=0.12 is also required.

- Data entry of station location has been greatly simplified. The user
  now merely specifies latitude and longitude, and only if he chooses
  the advanced option does he need, instead, to specify ordinate,
  abscissa, and srid.

- Several bugs have been fixed.

Backwards incompatible changes
------------------------------

- The ``is_active`` fields have been removed.

  Stations and instruments had an is_active field.  Apparently the
  original designers of Enhydris thought that it would be useful to
  make queries of, e.g., active stations, as opposed to all stations
  (including obsolete ones).

  However, the correctness of this field depends on the procedures
  each organization has. Many organizations don't have a specific
  procedure for obsoleting a station; a station merely falls out of
  use (e.g. an overseer stops working and (s)he is never replaced).
  Therefore, it is unlikely that someone will go and enter the correct
  value in the is_active field. Even if an organization does have
  processes that could ensure correctness of the field, they could
  merely specify an end date to a station or instrument, and therefore
  is_active is superfluous.

  Indeed, in all Hydroscope databases, the field seems to be randomly
  chosen, and in openmeteo.org it makes even less sense, since it is an
  open database whose users are expected to merely abandon their stations
  and not care about "closing" them properly.

  Therefore, the fields have been removed. However, the database
  upgrade script will verify that they are not being used before going
  on to remove them.

Upgrading from 0.5
------------------

1. Backup your database (you are not going to use this backup unless
   something goes wrong and you need to restore everything to the
   state it was before).

2. Make sure you are running the latest version of Enhydris 0.5 and
   that you have applied all its database upgrades (running
   :command:`python manage.py migrate` should apply all such upgrades,
   and should do nothing if they are already applied).

3. Install 0.6 and execute the database upgrade procedure::

      python manage.py migrate

Changes in 0.6 microversions
----------------------------

- Added some explanatory text for timestamp rounding and timestamp
  offset in the time series form (in 0.6.1).


Version 0.5
===========

Overview
--------

- There has been a huge overhaul of the Javascript.

- The map base layers are now configurable in `settings.py`.

- The map has been simplified and now uses OpenLayers 2.12.

- The "advanced search" has been removed. Instead, it is possible to
  perform advanced searches by writing the appropriate code in the
  single search box. The "Search tips" link beside the search box
  provides instructions.

- The skin has been modernized and simplified and uses Bootstrap. This
  is work in progress.

- The installation procedure has been greatly simplified.

- Django 1.8 support.

Backwards incompatible changes
------------------------------

- Only supports Python 2.7 and Django 1.8.

- Removed apps hchartpages and dbsync. These are expected to be
  replaced by independent applications in the future, but no promises
  are made.  Enhydris is to become a small, reliable and
  well-maintained core.

Upgrading from 0.2
------------------

Version 0.5 contains some tricky database changes. The upgrade
procedure is slightly complicated, and uses the intermediate Enhydris
version 0.3, which exists only for this purpose.

(Note for developers: the reason for this procedure is that hcore used
to have a foreign key to a dbsync model. As a result, the initial
Django migration listed dbsync as a dependency, making it impossible
to remove dbsync.)

The upgrade procedure is as follows:

1. Backup your database (you are not going to use this backup unless
   something goes wrong and you need to restore everything to the
   state it was before).

2. Make sure you are running the latest version of Enhydris 0.2 and
   that you have applied all its database upgrades (running
   :command:`python manage.py migrate` should apply all such upgrades,
   and should do nothing if they are already applied).

3. Follow the Enhydris 0.5 installation instructions to install
   Enhydris in a new virtualenv; however, rather than installing
   Enhydris 0.5, install, instead, Enhydris 0.3, like this::

       pip install 'enhydris>=0.3,<0.4'

4. Apply the database upgrades::

       python manage.py migrate --fake-initial

5. Install Enhydris 0.5. The simplest way (but not the safest) is this::

       pip install --upgrade --no-deps 'enhydris>=0.5,<0.6'

   However, it is best to discard your Enhydris 0.3 virtualenv and create a new
   one, in which case you would install Enhydris 0.5 like this::

       pip install 'enhydris>=0.5,<0.6'

6. Have your database password ready and run the following to empty
   the `django_migrations` database table::

       python manage.py dbshell
       delete from django_migrations;
       \q

7. Repopulate the `django_migrations` table::

       python manage.py migrate --fake

Changes in 0.5 microversions
----------------------------

- Removed embedmap view (in 0.5.1)
- Removed ``example_project``, which was used for development
  instances; instead, added instructions in :file:`README.rst` on how
  to create one (in 0.5.1).
- Fixed internal server error when editing station with
  ``ENHYDRIS_USERS_CAN_ADD_CONTENT=True`` (in 0.5.2).
- Since 0.5.3, Enhydris depends on pthelma<0.12, since pthelma 0.12
  has a backwards incompatible change.


Version 0.2
===========

Changes
-------

There have been too many changes to list here in detail. The most
important ones (particularly those affecting backwards compatibility)
are:

- Removed apps hrain, gis_objects, contourplot, hfaq, contact. hfaq
  and contact should be replaced with flatpages. hrain, gis_objects,
  and contourplot are not supported any more. If they are included
  again in the future, they will be maintained separately as distinct
  applications. Enhydris is to become a small, reliable and
  well-maintained core.

- Removed front page; front page is now station list

- Compatible with Django 1.5 and 1.6.

Upgrading from 0.1
------------------

Essentially you are on your own. It's likely that just installing
Enhydris 0.2 and executing :command:`python manage.py migrate` will do
the trick. Don't forget to backup your database before attempting
anything!
