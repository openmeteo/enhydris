.. _hrain:

:mod:`hrain` --- Precipitation event reports
============================================

hrain is a small application that produces reports about precipitation
events at an area where there are some rainfall measuring stations.
You can see it in action at http://hoa.ntua.gr/ (choose "Rainfall
events"). It automatically searches the time series to find rainfall
events, which it displays in an index resembling a tag cloud (we call
this the "event cloud"), and also displays a short report about each
event.

Installation
------------

To install hrain:

 1. In :file:`settings.py`, add ``enhydris.hrain`` to
    :data:`INSTALLED_APPS`, and also specify the configuration
    variables presented in the next section.

 2. Add the following to :file:`urls.py`::

       urlpatterns += patterns('', ('^rain/', include('enhydris.hrain.urls')))

    The above will result in the URL of your hrain installation being
    "rain/", but you can choose something else if you prefer.

 3. Run :command:`python manage.py syncdb` to create the database tables
    for hrain. Note that hrain does not use South for migrations,
    because its database tables only store information that can be
    re-created, and therefore you can safely delete them and recreate
    them.

 4. Run :command:`python manage.py hrain_refresh_events`. This command
    will retrieve the time series from the database, analyze them, and
    cache the necessary information in the database tables. Any
    information already existing in the database tables is removed
    before this, as are any cached charts. You probably want to setup
    this command to run periodically, e.g. once a day.

Configuration variables
-----------------------

.. data:: HRAIN_TIMESERIES

   A tuple of pairs. Let's look at an example from
   http://hoa.ntua.gr/::

     HRAIN_TIMESERIES = (( 14,  7), # Agios Kosmas
                         (793,  8), # Anw liosia
                         (378,  7), # Galatsi
                         (296,  7), # Hlioupoli
                         (453, 10), # Mandra
                         (  1, 10), # Menidi
                         (645, 12), # Pendeli
                         (718, 12), # Pikermi
                         ( 27, 17), # Psyttalia
                         (586, 10), # Zografou
                        )

   The first number of each pair is the time series id, and the second
   is a weight for calculating the surface precipitation of each
   event. The weights do not need to add up to 1 or 100; the result is
   divided by their sum.

.. data:: HRAIN_START_THRESHOLD
          HRAIN_END_THRESHOLD
          HRAIN_NTIMESERIES_START_THRESHOLD
          HRAIN_NTIMESERIES_END_THRESHOLD
          HRAIN_TIME_SEPARATOR

    These variables are parameters that define how the rainfall event
    identification algorithm works.  The first two of these variables
    are floats; the next two are integers; and the last one is a
    :class:`datetime.timedelta`. For an explanation of their meaning,
    see :cfunc:`ts_identify_events`.  Example from
    http://hoa.ntua.gr/::

       from datetime import timedelta
       HRAIN_START_THRESHOLD = 0.39
       HRAIN_NTIMESERIES_START_THRESHOLD = 2
       HRAIN_END_THRESHOLD = 0.19
       HRAIN_NTIMESERIES_END_THRESHOLD = 1
       HRAIN_TIME_SEPARATOR = timedelta(hours=2)

.. data:: HRAIN_STATIC_CACHE_PATH
          HRAIN_STATIC_CACHE_URL

   hrain generates some charts (on demand) and stores them in a
   directory. :data:`HRAIN_STATIC_CACHE_PATH` defines the directory,
   and :data:`HRAIN_STATIC_CACHE_URL` defines how to access the
   contents of this directory from the web. Example from
   http://hoa.ntua.gr/::

      import os
      HRAIN_STATIC_CACHE_PATH = os.path.join(MEDIA_ROOT, 'cache')
      HRAIN_STATIC_CACHE_URL = MEDIA_URL + '/cache/'

.. data:: HRAIN_BACKGROUNDS_PATH
          HRAIN_BACKGROUND_IMAGE
          HRAIN_BACKGROUND_MASK

   specify the full path of the directory where background pictures
   are stored. Background pictures are composed with the main
   contours image. When specifying a mask image then a composite
   composing method is applied, see PIL documentation.

.. data:: HRAIN_CHART_LARGE_DIMENSION

   specify the large dimension of the contour chart. If not specified
   a default value of 480 is used.

.. data:: HRAIN_CONTOUR_CHART_BOUNDS
          HRAIN_CONTOUR_SRID

   These variables define the co-ordinates of the rain contour map.
   The first variable is a tuple of four elements, which are x0, y0,
   x1, and y1; that is, the co-ordinates of the lower left and the
   upper right corner. The second variable is the SRID in which these
   co-ordinates are given. Example from http://hoa.ntua.gr/::

      HRAIN_CONTOUR_SRID = 2100
      HRAIN_CONTOUR_CHART_BOUNDS = (455000, 4192000, 500000, 4220000)

.. data:: HRAIN_EVENT_CLOUD_FONTSIZE_RANGE
          HRAIN_EVENT_CLOUD_FONTSIZE_INCREMENT

   These variables define the appearance of the event cloud. The first
   is a pair of font sizes, lowest and largest, and the second is an
   increment. The event cloud will be automatically adjusted so that
   the largest event receives the largest font size, the smallest
   event receives the smallest font size, and all other events are
   uniformly scaled in between but rounded so that they are in the
   specified increment. The "size' of the event refers to its total
   surface precipitation. Example from http://hoa.ntua.gr/::

      HRAIN_EVENT_CLOUD_FONTSIZE_RANGE = 8, 20
      HRAIN_EVENT_CLOUD_FONTSIZE_INCREMENT = 3

.. data:: HRAIN_IGNORE_ONGOING_EVENT

   If this is set to :const:`True` (the default is :const:`False`),
   then only events that have finished are taken into account; any
   precipitation event that is still ongoing is not calculated.
