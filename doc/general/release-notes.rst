.. _release-notes:

=============
Release notes
=============

.. highlight:: bash

Development
===========

Upgrading from 3.0
------------------

 1. Make sure you are upgrading from 3.0
 2. Backup the database.
 3. Login as a superuser and go to the dashboard.
 4. Go to "Sites" and make sure they're set correctly.
 5. In the settings, make sure ``SITE_ID`` is set correctly.
 6. Update the database with ``python manage.py migrate``. This will put
    all stations to the site specified with ``SITE_ID``, and will add
    all users to the group whose name is the domain of the current site
    (the group will be created automatically if it does not exist).
 7. If you have been using a single database to power many sites, then:
     * In the settings, make sure :data:`ENHYDRIS_SITES_FOR_NEW_STATIONS`
       is set correctly. Restart the server if necessary.
     * Logon as a superuseri and go to the dashboard
     * Go to each of the stations that used to be specified by
       ``ENHYDRIS_SITE_STATION_FILTER`` and make sure the "Sites" field
       is set correctly.
     * If any users need to be able to log on to a different site from
       the one where you performed the database update, go to each of
       these users and put them in the appropriate groups.

Changes from 3.0
----------------

- Functionality for serving many sites from a single database has been
  added. Accordingly, the setting ``ENHYDRIS_SITE_STATION_FILTER`` has
  been abolished and replaced with
  :data:`ENHYDRIS_SITES_FOR_NEW_STATIONS`. For more information, see
  :ref:`Managing domains <domains>`.

Version 3.0
===========

Released on 17 August 2021.

Upgrading
---------

You may only upgrade from version 2.1 (version 2.1 only exists to
facilitate transition to 3.0, and it is otherwise not used; the old
stable Enhydris version is 2.0). The procedure is this:

 1. Make sure you are running version 2.0 (any release will do).

 2. Backup the database.

 3. Make sure you have read and understood the list of changes from 2.0
    below, as some of these changes may require manual intervention or
    automatically do things you might not want.

 4. Update the repository::

       git fetch origin

 5. Shut down the running service.

 6. Install version 2.1 and migrate::

       git checkout 2.1
       python manage.py migrate

 7. Empty the migrations table of the database for the ``hcore`` app::

       python manage.py migrate --fake hcore zero

    (This step is optional because in 3.0 the ``hcore`` app goes away
    and is replaced by ``enhydris``. You can omit it in case you need to
    go back or execute it if you want a cleaner database.)

 8. `Install TimescaleDB`_ and restart PostgreSQL. You don't need to
    create the extension in the database; the Django migrations will do
    so automatically. See "TimescaleDB" in the "Changes from 2.0" below
    for more information.

    .. _install timescaledb: https://docs.timescale.com/latest/getting-started/installation

 9. In the settings, make sure SITE_ID_, LANGUAGE_CODE_ and
    PARLER_LANGUAGES_ are set properly. See "Multilingual contents" in
    the "Changes from 2.0" below for more information.

 10. Install version 3.0::

       git checkout 3.0
       pip install -r requirements.txt

 11. If your settings file has been in ``enhydris/settings/``, you need
     to create a settings file in ``enhydris_project/settings/``, as this
     location has changed.

 12. Empty the migrations table for the registration app::

       python manage.py migrate --fake registration zero

     If you fail to perform this step, you may get the message 'relation
     "registration_registrationprofile" does not exist' or similar. The
     exact cause is not known, however lots of things have changed
     regarding the registration system.

 13. Execute migrations::

       python manage.py migrate --fake-initial

     If some migrations succeed and there is a failure later, you should
     probably omit the --fake-initial parameter in subsequent attempts.
     There is, notably, a possibility of an error related to
     registration happening (as described in the previous step); in such
     a case, repeat the previous step and then re-execute the above
     migration command (possibly without --fake-initial).

 14. Remove obsolete settings from the settings file.

 15. Start the service.

 16. Create and start a celery service.

Changes from 2.0
----------------

Time series groups
^^^^^^^^^^^^^^^^^^

In 2.0, a station has time series. Now it has time series groups and
each group consists of time series with essentially the same kind of
data but in a different time step or in a different checking status. For
example, if you have a temperature sensor that measures temperature
every 10 minutes, then you will have a "temperature" time series group,
which will contain the initial time series, and it may also contain the
checked time series, the regularized time series, the hourly time
series, etc. (If you have two temperature sensors, you'll have two time
series groups.)

We avoid showing the term "time series group" to the user (instead, we
are being vague, like "Data", or we might sometimes use "time series"
when we actually mean a time series group). Sometimes we can't avoid it
though (notably in the admin).

Each time series in the group has a "type" (which is enumerated): it can
be initial, checked, regularized, or aggregated.

During database upgrade, unless enhydris-autoprocess is installed, each
existing time series goes in a separate group, and it is assumed it is
the initial. In many cases, this is the correct assumption. If
enhydris-autoprocess is installed, the database upgrade attempts to find
out which time series is the initial, which is checked, and which is
aggregated (however enhydris-autoprocess did not exist for Enhydris 2.0,
so this applies only to installations of Enhydris development versions).

TimescaleDB
^^^^^^^^^^^

We now store time series data in the database using TimescaleDB_.
Before that, time series data was stored in files in the filesystem,
in CSV format, one file per time series.

The location where the files were being stored was specified by setting
``ENHYDRIS_TIMESERIES_DATA_DIR``. This setting has now been abolished.

The size of your database will increase considerably. The increase in
size maybe eight times the size of ``ENHYDRIS_TIMESERIES_DATA_DIR``.
Make sure you have the available disk space. Also make sure that your
PostgreSQL backup strategy can handle the increased size of the
database.

When executing the migrations, the time series data will be read from
the files and entered to the database. The files will not be removed.

The migration will only work if the PostgreSQL server runs in the same
machine as Enhydris. This is because, in order to speed up the importing
of the data to the database, the files are read directly by the database
server using the SQL ``COPY ... FROM`` command. See the code for the
migration for more details.

Since a single transaction could be too much for the entire importing
(it would use lots of space and be very slow), the transaction is
committed for each time series. This means that if you interrupt the
migration, the database will contain some, but not all, records.
Attempting to run the migration a second time will therefore fail. In
such a case, before attempting to re-run the migration, empty the table
like this::

   echo "DELETE FROM enhydris_timeseriesrecord" | ./manage.py dbshell

In addition, to speed up importing of the data, table constraints and
indexes are created after the data is imported. This may mean that it
could fail after importing if there are duplicate dates in the
timeseries data. This can happen because of an `old bug`_. In such a
case, reverse the migration (empty the table as above if needed), run
the following inside the ``ENHYDRIS_TIMESERIES_DATA_DIR`` directory to
find the problems, fix them and re-run the migration::

    for x in *; do
        a=`uniq -w 16 -D $x`
        if [ -n "$a" ]; then
            echo ========= $x
            echo "$a"
            echo
        fi
    done

As an order of magnitude, conversion of the data should take something
like 40 minutes per GB of ``ENHYDRIS_TIMESERIES_DATA_DIR`` storage
space, but of course this depends on several factors. Roughly half of
this time will be for the importing of the data, and another half for
the creation of the indexes (however these times might not actually be
linear).

.. timescaledb: https://www.timescale.com
.. _old bug: https://github.com/openmeteo/htimeseries/issues/22

Celery
^^^^^^

In 2.0, nothing was done asynchronously. In 3.0, the uploading of time
series data through the site (not through the Web API) is performed
asynchronously, i.e. the user receives a message that the time series
data are about to be imported, and he is emailed when importing
finishes.

Therefore, a Celery service must be running on the server.

Some add-on applications, like ``enhydris-synoptic`` and
``enhydris-autoprocess``, also use Celery.

Multilingual contents
^^^^^^^^^^^^^^^^^^^^^

The way we do multilingual database contents has changed.

We were using a hacky system where two languages were offered; e.g.
there was ``Gentity.name`` and ``Gentity.name_alt``, where the latter
was the name in the "alternative" language. This system, rather than a
"correct" one that uses, e.g., django-parler, was more trouble than it
was worth, therefore all fields ending in ``_alt`` have been abolished.

In the new Enhydris version, several lookups, such as variable names,
are multilingual using django-parler. However, station and timeseries
names and remarks, event reports, etc. (i.e. everything a non-admin user
is expected to enter), are not multilingual. The idea is that a station
in Greece will have a Greek name, and this does not need to be
transliterated. The rationale is the same as for
`OSM's-avoid-transliteration`_ rule: transliterations can be automated,
and having users enter them manually would only create noise in the
database. There may be valid cases for translation (e.g. when the name
of a station is "bridge X", or translation of remarks), but users
generally don't enter translations so we haven't developed this
functionality yet.

.. _osm's-avoid-transliteration: https://wiki.openstreetmap.org/wiki/Names#Avoid_transliteration

For the case of fields that are untranslated in the new version, while
upgrading, for each row, whichever of ``fieldname`` and
``fieldname_alt`` is nonempty will be used for ``fieldname``. If both
are nonempty and they are single-line fields, "value of ``fieldname``
[value of ``fieldname_alt``]" will be used for ``fieldname``, i.e. the
value of ``fieldname_alt`` will be appended in square brackets. If the
number of characters available is insufficient an error message will be
given and the upgrade will fail. If both fields are nonempty and they
are multi-line fields such as ``TextField``, they will be joined
together separated by ``\n\n---ALT---\n\n``.

For the case of lookups translated with django-parler, ``fieldname``
becomes the main language (set by LANGUAGE_CODE_ or
PARLER_DEFAULT_LANGUAGE_CODE_), and ``fieldname_alt`` becomes the second
language, i.e. the second entry of PARLER_LANGUAGES_. If
PARLER_LANGUAGES_ has fewer than two languages, then the conversion
described in the previous paragraph takes place.

(In fact, because abolishing of ``_alt`` fields was decided and
implemented several months before deciding to use django-parler on
lookups, the migration system will convert everything to unilingual as
described above, and then it will convert lookups back to multilingual.)

Before upgrading the database, it is important to set SITE_ID_,
LANGUAGE_CODE_, and PARLER_LANGUAGES_. SITE_ID_ is probably already set,
probably by the default Enhydris settings. Keep it as it is. Set
LANGUAGE_CODE_ to the language that corresponds to the main language of
the site, i.e. the one to which lookup descriptions not ending in
``_alt`` correspond. Finally, set PARLER_LANGUAGES_ as follows::

   PARLER_LANGUAGES = {
       SITE_ID: [
         {"code": LANGUAGE_CODE},
         {"code": "specify_your_second_language_here"},
       ],
   }

Because of what is likely a `bug in django-parler`_ (at least 2.0), it
is important to use ``SITE_ID`` as the key and not ``None``.

.. _SITE_ID: https://docs.djangoproject.com/en/3.2/ref/settings/#site-id
.. _LANGUAGE_CODE: https://docs.djangoproject.com/en/3.2/ref/settings/#language-code
.. _PARLER_DEFAULT_LANGUAGE_CODE: https://django-parler.readthedocs.io/en/latest/configuration.html#parler-default-language-code
.. _PARLER_LANGUAGES: https://django-parler.readthedocs.io/en/latest/configuration.html#parler-languages
.. _bug in django-parler: https://stackoverflow.com/questions/40187339/django-parler-doesnt-show-tabs-in-admin/

Geographical areas
^^^^^^^^^^^^^^^^^^

Each station (and more generally each Gentity) used to have three
foreign keys to water basins, water divisions, and political divisions
(the latter were hierarchical, being countries at the top level). This
is no longer the case. Water basins, water divisions, and political
divisions have been abolished. Instead, there is a mere Garea entity,
that can belong in a category. You create as many categories as you want
(countries, water basins, prefectures, whatever you like) and you upload
a shapefile of them (it's mandatory that they have a geometry).

There is no foreign key between stations (or other Gentities) and
Gareas. To find which stations are in a Garea, the system does a
point-in-polygon query.

The upgrade will delete all existing water basins, water divisions, and
political divisions, and all existing relationships between them. This
change is non-reversible. It will not create any Gareas. You can use the
admin to upload Gareas.

Other changes
^^^^^^^^^^^^^

- The Web API has been reworked. Applications using the Enhydris 2.0 web
  API won't work unchanged with 3.0.
- The templates have been refactored. Applications and installations
  with custom templates or templates inheriting the Enhydris templates
  may need to be modified.
- Instruments have been abolished. Upgrading requires the database to
  not have any instruments. If you try to upgrade and there are
  instruments, it will give you an error message with instructions on
  how to empty the instruments table.
- GentityGenericData and GentityAltCode have been abolished, as they
  were practically not being used in any of the known installations.
  Upgrading requires the tables to be empty; if not, upgrading will stop
  with an error message. Make sure the tables are empty before
  upgrading.
- ``Gpoint.point`` has been renamed to ``Gpoint.geom``.
- Stations now must have co-ordinates, i.e. the related database field
  ``gpoint.geometry`` (formerly ``gpoint.point``) is not null. If you
  have any stations with null co-ordinates, they will be silently
  converted to latitude zero and longitude zero during upgrading.
- The time step is now stored as a pandas "frequency" string, e.g.
  "10min", "H", "M", "Y". The ``TimeStep`` model does not exist any
  more. The ``timestamp_rounding``, ``timestamp_offset`` and
  ``interval_type`` properties have been abolished. During the database
  upgrade, they are simply dropped.
- SQLite is no longer supported.
- The fields ``approximate`` (used to denote that a station's location
  has been assigned roughly) and ``asrid`` (altitude SRID) have been
  abolished. The field ``srid`` has been renamed to ``original_srid``.
- The field ``Gentity.short_name`` has been renamed to ``Gentity.code``.
- Station types have been abolished. Stations now don't have a type.
  The related information previously stored in the database will be
  deleted in the upgrade.
- Stations can now only have a single overseer, specified as a text
  field. Upgrading will convert as needed, and it will also delete any
  unreferenced Person objects.
- The field ``Station.is_automatic`` has been abolished.
- The database fields ``copyright_years`` and ``copyright_holder`` have
  been abolished. The database upgrade will remove them and any
  information stored in them will be lost. Accordingly, the setting
  ``ENHYDRIS_DISPLAY_COPYRIGHT_INFO`` has been abolished.
- OpenLayers has been replaced with Leaflet. Accordingly, the form of
  the :data:`ENHYDRIS_MAP_BASE_LAYERS` setting has been changed and the
  setting :data:`ENHYDRIS_MAP_DEFAULT_BASE_LAYER` has been added.
- The setting ``ENHYDRIS_SITE_CONTENT_IS_FREE`` has been abolished.
  ``ENHYDRIS_TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS`` has been renamed to
  :data:`ENHYDRIS_OPEN_CONTENT`. Several other settings that were rarely
  being used have been abolished or renamed.

Version 2.0
===========

Upgrading
---------

You can upgrade directly from versions 0.8 and later. If you have an older
version, first upgrade to 0.8.

Enhydris is no longer pip-installable. Instead, it is a typical Django
application with its :file:`manage.py` and all. Install it as described
in :ref:`install` and execute the database upgrade procedure::

    python manage.py migrate

Changes from 1.1.2
------------------

- Now a normal Django project, no longer pip-installable.
- Django 1.11 and only that is now supported.
- A favicon has been added.
- Several bugs have been fixed. Notably, object deletions are confirmed.

Changes in 2.0 microversions
----------------------------

- Version 2.0.1 removes ``EMAIL_BACKEND`` from the base settings and leaves the
  Django default (this broke some production sites that did not specify
  ``EMAIL_BACKEND`` and were expecting the Django default.)
- Version 2.0.2 adds pagination to the list of stations and requires a
  Django-1.11-compatible version of django-simple-captcha.
- Version 2.0.3 fixes an undocumented CSV view that sends you a zip file with
  stations, instruments and time series in CSV when you add ?format=csv to a
  stations list URL. Apparently this had been broken since version 1.0.
- Version 2.0.4 fixes several crashes.

Version 1.1
===========

Upgrading
---------

There are no database migrations since version 0.8, so you just need to
install the new version and you're good to go.

Changes in 1.1 microversions
----------------------------

- Version 1.1.0 changes an internal API;
  :meth:`enhydris.hcore.models.Timeseries.get_all_data()` is renamed to
  :meth:`enhydris.hcore.models.Timeseries.get_data()` and accepts arguments to
  specify a start and end date.
- Version 1.1.1 puts the navbar inside a {% block %}, so that it can be
  overriden in custom skins.
- Version 1.1.2 fixes two bugs when editing time series: appending wasn't
  working properly, and start and end dates were shown as editable fields.

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
