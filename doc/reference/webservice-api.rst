.. _webservice-api:

==============
Webservice API
==============

Overview
========

Normally the web pages of Enhydris are good if you are a human; but if
you are a computer (a script that creates stations, for example), then
you need a different interface. For that purpose, Enydris offers an
API through HTTP, through which applications can communicate. For
example, http://openmeteo.org/db/stations/d/1334/ shows you a weather
station in human-readable format;
http://openmeteo.org/db/api/Station/1334/ provides you data on the
same station in machine-readable format.

.. admonition:: Important

   The Webservice API might change heavily in the future. If you make
   any use of the API, it is very important that you stay in touch
   with us so that we take into account your backwards compatibility
   needs. Otherwise your applications might stop working one day.

The Webservice API is a work in progress: it was originally designed
in order to provide the ability to replicate the data from one
instance to another over the network. It was later extended to provide
the possibility to create timeseries through a script. New functions
are added to it as needed.

Client authentication
=====================

Some of the API functions are provided freely, while others require
authentication. An example of the latter are functions which alter
data; another example is data which are protected and need, for
example, a subscription in order to be accessed. In such cases of
restricted access, HTTP Basic authentication is performed.

.. Note:: 

   Using HTTP Basic Authentication with apache and
   mod_wsgi requires you to add the ``WSGIPassAuthorization On``
   directive to the server or vhost config, otherwise the application
   cannot read the authentication data from HTTP_AUTHORIZATION in
   request.META.  See: `WSGI+BASIC_AUTH`_.  

   .. _WSGI+BASIC_AUTH: http://code.google.com/p/modwsgi/wiki/ConfigurationDirectives#WSGIPassAuthorization.

Generic API calls 
=================

API calls are accessible under the ``/api/`` url after which you just fill in
the model name of the model you want to request. For example, to request all
the stations you must provide the url ``http://base-address/api/Station/``; the
format in which the data will be returned depends on the HTTP ``Accept``
header. The same goes for the rest of the enhydris models (e.g.
``/api/Garea/``, ``/api/Gentity/`` etc). There is also the ability to request
only one object of a specific type by appending its ``id`` in the url like
this: ``http://base-address/api/Station/1000/``. 

See the :ref:`data model reference <database>` for information on the
models.

Creating new time series
========================

To create a new time series, you POST ``/api/Timeseries/``; you must
pass an appropriate csrf_token and a session id (you must be logged on
as a user who has permission to do this), and pass the data in an
appropriate format, such as JSON. This is an example::

    from urllib2 import build_opener, HTTPCookieProcessor, Request
    import cookielib
    import json

    BASE_URL = 'http://openmeteo.org/db/'
    USERNAME = 'my_username'
    PASSWORD = 'my_password'
    EXISTING_TIMESERIES_ID = 42

    # Get a csrf token and login
    cookiejar = cookielib.CookieJar()
    opener = build_opener(HTTPCookieProcessor(cookiejar))
    s = opener.open(BASE_URL + 'accounts/login/').read()
    opener.addheaders = [('X-CSRFToken', cookie.value)
                        for cookie in cookiejar if cookie.name == 'csrftoken']
    data = 'username={0}&password={1}'.format(USERNAME, PASSWORD)
    opener.open(BASE_URL + 'accounts/login/', data)

    # Read an existing time series, and create a new one that has
    # different remarks.
    fp = opener.open('{0}api/Timeseries/{1}/'.format(BASE_URL,
                                                    EXISTING_TIMESERIES_ID))
    j = json.load(fp)
    j[0]['fields']['remarks'] += "This time series rocks!"
    fp = opener.open(Request('{0}api/Timeseries/'.format(BASE_URL),
                             data = json.dumps(j),
                             headers = { 'Content-type': 'application/json' }))
    response_text = fp.read()
    new_id = int(response_text)

    print "The time series was created; its id is {0}".format(new_id,)


Appending data to a time series
===============================

To append data to a time series, you PUT ``api/tsdata``. See the code
of loggertodb_ for an example of how to do this.

.. _loggertodb: ../../pthelma/loggertodb

Timeseries data and GentityFile
===============================

At ``http://base-address/api/tsdata/id/`` (where ``id`` is the actual
id of the timeseries object) you can get the timeseries data in
:ref:`text format <textformat>`.

.. admonition:: Backwards-compatibility

   The API implementation was changed in several changesets, starting
   with 639e4c810457. Before that, django-piston_ was being used for
   the api; it was changed to django-rest-framework_.

   Not all API features have been reimplemented.  Notably, piston's
   output could be used with Django's loaddata management command to
   load data to an empty instance; this is no longer possible, because
   the returned objects do not contain a "model" attribute.

   .. _django-piston: https://bitbucket.org/jespern/django-piston/
   .. _django-rest-framework: http://django-rest-framework.org/

   Furthermore, there was a feature in which only recently changed
   items would be returned. This has not been implemented, which means
   the :ref:`dbsync application <dbsync>` does not work.
   There was also the possibility to get gentity files at
   `http://base-address/api/gfdata/id`` (where ``id`` was the actual
   id of the GentityFile object). Finally, there was the "station
   information and lists" feature, documented below:

   **(Temporarily?) obsolete documentation on station information and lists**

   There are also some more calls which provide station details in a more
   human readable format, including a station's geodata which may be used
   by 3rd party application to incorporate the displaying of enhydris
   stations in their maps. These API calls reside under the
   ``/api/Station/info/`` url and are similar to the ones above. If you
   do not specify any additional parameters, you get information for all
   Stations hosted in Enhydris and if you want the details for a specific
   station, you just need to append its id to the end of the url like
   above (eg ``/api/Station/info/1000``).  See :class:`models.Gentity`
   and :class:`models.Station` for a description of the meaning of the
   fields.

   There is also another feature which enables users to request a sublist
   of stations by providing the station ids in a comma separated list by
   using the ``/api/Station/info/list`` url. This call supports only the
   POST method and the comma separated list must be given under the
   varible name ``station_list``.  For example::
           
       curl -X POST -d "station_list=10001,10002,10003" http://openmeteo.org/db/api/Station/info/list/


Cached time series data
=======================

At ``http://base-address/timeseries/data/?object_id=id`` (where ``id``
is the actual id of the time series object) you can get some time
series data from specific positions (timestamps) as well as statistics
and chart data. Data is cached so no need to read the entire time
series and usually information is delivered fast. 

Cached time series data are being used to display time series
previews in time series detail pages. Also there are used for
charting like in:

  http://openmeteo.org/db/chart/ntuastation/

The response is a JSON object. An
example is the following::

  {
    "stats": {"min_tstmp": 1353316200000, 
              "max": 6.0, 
              "max_tstmp": 979495200000, 
              "avg": 0.0094982613015400109, 
              "vavg": null,
              "count": 10065,
              "last_tstmp": 1353316200000,
              "last": 0.0,
              "min": 0.0,
              "sum": 95.600000000000207,
              "vectors": [0, 0, 0, 0, 0, 0, 0, 0],
              "vsum": [0.0, 0.0]}, 
    "data": [[911218200000, "0.0", 1],
             [913349400000, "4.8", 3551], 
             ..., 
             [1350248400000, "0.0", 710001], 
             [1353316200000, "0.0", 715149]]
  }

"stats"
  An object holding statistics for the given interval (see bellow)

"last"
  Last value observed for the given interval

"last_tstmp"
  The timestamp for the last value

"max"
  Is the maximum value observed for the given interval (see bellow)

"max_tstmp"
  The timestamp where the maximum value is observed

"min"
  The minimum value for the given interval

"min_tstmp"
  The timestamp where minimum value is observed

"avg"
  The average value for the given interval

"vavg"
  A vector average in decimal degrees for vector variables such as
  wind direction etc.

"count"
  The actual number of records used for statistics

"sum"
  The sum of values for the given interval

"vsum"
  Two components of sum (vector sum) Sx, Sy, computed by the cosines,
  sinus.

"vectors"
  The percentage of vector variable for eight distinct directions (N,
  NE, E, SE, S, SW, W and NW).

"data"
  An object holding an array of charting values. Each item of the array
  holds [timestamp, value, index]. Timestamp is a javascript timestamp,
  value if a floating point number or null, index is the actual index
  of the value in the whole time series records. 

You have to specify at least the object_id GET parameter in order to
obtain some data. The default time interval is the whole time series.
In the case of the whole time series a rough image of the time series
is displayed which is not precise. Statistics also can be no precise.

In example for 10-minute time step time series, chart and statistics
can be precise for intervals of one month the most.

Besides ``object_id`` some other parameters can be given as GET
parameters to specify the desired interval etc:

*start_pos*
  an index number specifying the begining of an interval. Index can
  be zero (0) for the begining of the time series or at most last
  record number minus one.

*end_pos*
  an index number specifying the end of an interval.

*last*
  A string defining an interval from a pre-defined set:
    * day
    * week
    * month
    * year
    * moment (returns one value only for the last moment)
    * hour
    * twohour

  By default the end of the interval is the end of the time series. If
  time-series is auto-updated it shows the last measurements.

*date*
  Can be used in conjuction with the *last* parameter to display in
  interval beginning at the specified date. Date format: yyyy-mm-dd

*time*
  Can be used in conjuction with *last* and *date* parameters to
  specify the beginning time of the interval. Accepted format: HH:MM 

*exact_datetime*
  A boolean parameter (set to true to activate). Specifies that
  date times should be existing in time series record or else it
  returns null. If not activated, it returns the closest periods
  with data to the specified interval.

*start_offset*
  An offset in minutes for the beginning of the interval. It can
  be used i.e. to exclude the first value of a daily interval, so
  the statistics are computed correct i.e. from 144 10-min values
  rather than 145 values (e.g. from 00:10 to 24:00 rather than
  00:00 to 24:00). Suggested value for a ten minute time series is
  10

*vector*
  A boolean parameter. Set to 'true' to activate. Then vector
  statistics are being calculated.

*jsoncallback=?*
  If you're running into the Same Origin Policy, which doesn't 
  (normally) allow ajax requests to cross origins you should add
  the GET parameter above to obtain the cached time series data
  set.

A full example to get some daily values for a time series:

  https://openmeteo.org/db/timeseries/data/?object_id=230&last=day&exact_datetime=true&date=2012-11-01&time=00:00
