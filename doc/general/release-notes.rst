.. _release-notes:

=============
Release notes
=============

.. highlight:: bash

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
