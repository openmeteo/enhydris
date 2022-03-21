.. _webservice-api:

==============
Webservice API
==============

Quick start
===========

Get list of stations with a simple unauthenticated request::

    $ curl https://openmeteo.org/api/stations/

Response::

    {
      "count": 109,
      "next": "http://openmeteo.org/api/stations/?page=2",
      "previous": null,
      "bounding_box": [
        7.58748007,
        34.9857333,
        32.9850667,
        53.85553
      ],
      "results": [
        {
          "id": 1386,
          "last_update": "2013-12-12T10:22:30Z",
          "last_modified": "2013-10-10T05:04:42.478447Z",
          "name": "ΡΕΜΑ ΠΙΚΡΟΔΑΦΝΗΣ",
          "code": "ΠΙΚΡΟΔΑΦΝΗ",
          "remarks": "ΕΛΛΗΝΙΚΟ ΚΕΝΤΡΟ ΘΑΛΑΣΣΙΩΝ ΕΡΕΥΝΩΝ",
          "original_srid": 2100,
          "altitude": 2,
          "geom": "SRID=4326;POINT (23.7025252977241 37.91860884428689)",
          "start_date": "2012-09-20",
          "end_date": null,
          "owner": 11,
          "overseer": "",
          "maintainers": []
        },
        ...
      ],
    }

Some requests need authentication. First, you need to get a token::

   curl -X POST -d "username=alice" -d "password=topsecret" \
       https://openmeteo.org/api/auth/login/

Response::

   {"key": "24122a7ad9cfec48eb536f5ca12fe06116ba3593"}

Subsequently, you can make authenticated requests to the API; for example, the
following will update a time series, modifying its ``variable`` field::

    curl -H "Authorization: token 24122a7ad9cfec48eb536f5ca12fe06116ba3593" \
        -X PATCH -d "variable=1" \
        https://openmeteo.org/api/stations/1334/timeseries/10657/

The response will be 200 with the following content::

    {
      "id": 10657,
      "last_modified": "2011-06-22T06:54:17.064484Z",
      "name": "Wind gust (2000-2006)",
      "hidden": false,
      "precision": 1,
      "remarks": "Type: Raw data",
      "gentity": 1334,
      "variable": 1,
      "unit_of_measurement": 7,
      "time_zone": 1,
      "time_step": "10min"
    }

Authentication and user management
==================================

Client authentication
---------------------

Use OAuth2 token authentication::

   curl -H "Authorization: token OAUTH-TOKEN" https://openmeteo.org/api/

To **get a token**, POST to ``/auth/login/``::

   curl -X POST -d "username=alice" -d "password=topsecret" \
       https://openmeteo.org/api/auth/login/

This will result in something like this::

   {"key": "24122a7ad9cfec48eb536f5ca12fe06116ba3593"}

You can **invalidate a token** by POST to ``/auth/logout/``::

   curl -X POST -H "Authorization: token OAUTH-TOKEN" \
       https://openmeteo.org/api/auth/logout/

The response is 200 with this content::

    {"detail":"Successfully logged out."}

Password management
-------------------

To **change password**, POST to ``/auth/password/change/``::

    curl -X POST -H "Authorization: token OAUTH-TOKEN" \
       -d "old_password=topsecret1" \
       -d "new_password1=topsecret2" -d "new_password2=topsecret2" \
       https://openmeteo.org/api/auth/password/change/

If all goes well, the response is a 200 with the following content::

    {"detail": "New password has been saved."}

If there is an error, the response is a 400 with a standard `error response`_.

To **reset the password**, POST to ``/auth/password/reset/``::

   curl -X POST -d "email=myself@example.com" \
       https://openmeteo.org/api/auth/password/reset/

This will respond with 200 and the following content::

    {"detail":"Password reset e-mail has been sent."}

The response will be 200 even if there is no record of this email
address (but in this case the response will be ignored); this is in
order to avoid disclosing which email addresses are registered. However,
the response will be 400 with a standard `error response`_ if the email
address is invalid.

The user will subsequently be sent an email with a link (under
``/api/auth/password/reset/confirm/``) that provides a page where the
user can specify a new password. After succeeding in specifying a new
password, he is redirected to ``/api/auth/password/reset/complete/``,
which is a page that says "your password has been set". However these
two aren't API endpoints (they're just the convenient defaults of
``dj-rest-auth``).

User profile management
-----------------------

To **get the user data**, GET ``/auth/user``::

    curl -H "Authorization: token OAUTH-TOKEN" \
       https://openmeteo.org/api/auth/user/

This will normally result in a 200 response with content like this::

    {
        "pk": 166,
        "username": "alice",
        "email": "alice@example.com",
        "first_name": "Alice",
        "last_name": "Burton"
    }

You can **modify these attributes** except for ``pk`` and ``email`` by
PUT or PATCH to the same endpoint::

    curl -X PATCH -H "Authorization: token OAUTH-TOKEN" \
       -d "username=joe" https://openmeteo.org/api/auth/user/

The response is a 200 with a similar content as the GET response (with
the updated data), unless there is a problem, in which case there's a
standard `error response`_.

Lookups
=======

GET a single object for ``stationtypes``::

    curl https://openmeteo.org/api/stationtypes/1/

Response::

    {
      "id": 1,
      "last_modified": "2011-06-22T05:21:05.436765Z",
      "descr": "Meteorological",
    }

GET the list of objects for ``stationtypes``::

    curl https://openmeteo.org/api/stationtypes/

The result is a `paginated list`_ of station types::

    {
        "count": 8,
        "next": null,
        "previous": null,
        "results": [
            {...},
            {...},
            ...
        ]
    }

Exactly the same applies to ``eventtypes`` and ``variables``.

Besides these there are several other lookups for which the response is
similar but may have additional information. These are
``organizations``, ``persons``, ``timezones``, ``filetypes`` and
``units``.

Response format for ``organizations``::

    {
      "id": 5,
      "last_modified": "2011-06-30T03:03:47.392265Z",
      "remarks": "",
      "name": "National Technical University of Athens - Dept. of Water Resources and Env. Engineering",
      "acronym": "N.T.U.A. - D.W.R.E.",
    }

Response format for ``persons``::

    {
        "id": 17,
        "last_modified": null,
        "remarks": "",
        "last_name": "Christofides",
        "first_name": "Antonis",
        "middle_names": "Michael",
        "initials": "A. C.",
    }

Response format for ``timezones``::

    {
        "id": 9,
        "last_modified": "2011-06-28T16:42:34.760676Z",
        "code": "EST",
        "utc_offset": -300
    }

Response format for ``filetypes``::

  {
    "id": 7,
    "last_modified": "2011-06-22T05:04:03.461401Z",
    "descr": "png Picture",
    "mime_type": "image/png"
  }

Response format for ``units``::

  {
    "id": 614,
    "last_modified": null,
    "descr": "Square metres",
    "symbol": "m²",
    "variables": []
  }

Stations
========

Station detail
--------------

You can GET the detail of a single station at ``/api/stations/ID/``::

    curl https://openmeteo.org/api/stations/1334/

Response::

    {
      "id": 1386,
      "last_update": "2013-12-12T10:22:30Z",
      "last_modified": "2013-10-10T05:04:42.478447Z",
      "name": "ΡΕΜΑ ΠΙΚΡΟΔΑΦΝΗΣ",
      "code": "ΠΙΚΡΟΔΑΦΝΗ",
      "remarks": "ΕΛΛΗΝΙΚΟ ΚΕΝΤΡΟ ΘΑΛΑΣΣΙΩΝ ΕΡΕΥΝΩΝ",
      "original_srid": 2100,
      "altitude": 2,
      "geom": "SRID=4326;POINT (23.7025252977241 37.91860884428689)",
      "start_date": "2012-09-20",
      "end_date": null,
      "owner": 11,
      "overseer": "",
      "maintainers": []
    }

List stations
-------------

GET the list of stations at ``/stations/``::

    curl https://openmeteo.org/api/stations/

The result is a `paginated list`_ of stations::

    {
        "count": 109,
        "next": "http://openmeteo.org/api/stations/?page=2",
        "previous": null,
        "bounding_box": [7.58748, 37.03330, 26.88787, 53.85553]
        "results": [
            {...},
            {...},
            ...
        ]
    }

Except for the standard `paginated list`_ attributes ``count``,
``next``, ``previous`` and ``results``, the returned object also
contains ``bounding_box``: this is the rectangle that encloses all
stations this query returns (not only of this page): longitude and
latitude of lower left corner, longitude and latitude of top right
corner.

Search stations
---------------

Limit the returned stations with the ``q`` parameter. The following will
return all stations where **the specified words appear anywhere** in the
name, remarks, owner name, or timeseries remarks. The match is case
insensitive, and the words are actually substrings (i.e. they can match
part of a word)::

    curl 'https://openmeteo.org/api/stations/?q=athens+research'

The search string specified by ``q`` consists of space-delimited search
terms.  The result set is the "and" of all search terms. If a search
term does not contain a colon (``:``), it is searched mostly everywhere,
as explained above.  If it does contain a colon, then the form of the
search term is :samp:`{search_type}:{words}`. The ``words`` cannot
contain a space (this is rarely a problem; instead of searching for
"ionian islands", searching for "ionian" is usually fine). Search terms
where the ``search_type`` isn't recognized are ignored.

You can search specifically **by owner**::

    curl 'https://openmeteo.org/api/stations/?q=owner:ntua'

Or **by type**::

    curl 'https://openmeteo.org/api/stations/?q=type:meteorological'

Or **by variable** (i.e. one of the timeseries of the station refers to that
variable)::

    curl 'https://openmeteo.org/api/stations/?q=variable:temperature'

You can also search **by bounding box**. The following will find
stations that are enclosed in the specified rectangle (the numbers are
longitude and latitude of lower-left and top-right corner)::

    curl 'https://openmeteo.org/api/stations/?q=bbox:22.5,37.0,24.3,39.1'

You can include **only stations that have time series** by specifying
the search term ``ts_only:``, without a search word::

    curl 'https://openmeteo.org/api/stations/?q=ts_only:'

Finally, ``ts_has_years`` can limit to stations based on **the range of
their time series**. The following will find stations that have at least
one time series containing records in 1988, at least one time series
containing records in 1989, and at least one time series containing
records in 2004::

    curl 'https://openmeteo.org/api/stations/?q=ts_has_years:1988,1989,2004'

Sort the list of stations
-------------------------

Sort the returned stations with the ``sort`` parameter, which can be
specified many times. This will sort by start date, then by name::

    curl 'https://openmeteo.org/api/stations/?sort=start_date&sort=name'

Export stations in a CSV
------------------------

Sometimes users want to get the list of stations and process it in a
spreadsheet. This does this::

    curl https://openmeteo.org/api/stations/csv/ >data.zip

The list can be sorted and filtered with the ``q`` and ``sort``
parameters as explained above. The result is a zip file that contains a
CSV with the stations and a CSV with all the time series (their metadata
only) of these stations. These lists contain all the columns, so users
can do whatever they want with them.

Create, update or delete stations
---------------------------------

DELETE a station::

    curl -X DELETE -H "Authorization: token OAUTH-TOKEN" \
        https://openmeteo.org/api/stations/1334/

The response is normally 204 (no content) or 404.

POST to create a station::

    curl -X POST -H "Authorization: token OAUTH-TOKEN" \
        -d "name=My station" -d "geom=POINT(20.94565 39.12102)" \
        -d "owner=11" https://openmeteo.org/api/stations/

The response is a 201 with a similar content as the GET detail response
(with the new data), unless there is a problem, in which case there's a
standard `error response`_.

When specifying nested objects, these objects are not created or
updated—only the id is used and a reference to the nested object with
that id is created.

PUT or PATCH a station::

    curl -X PATCH -H "Authorization: token OAUTH-TOKEN" \
        -d "name=Your station" https://openmeteo.org/api/stations/1334/

The response is a 200 with a similar content as the GET detail response
(with the updated data), unless there is a problem, in which case
there's a standard `error response`_. Nested objects are handled in the same
way as for POST (see above).

Time series groups
==================

Time series group detail
------------------------

You can GET the detail of a single time series group at
``/api/stations/XXX/timeseriesgroups/YYY/``::

   curl https://openmeteo.org/api/stations/1403/timeseriesgroups/483/

Response::

   {
       "id": 522,
       "last_modified": "2015-04-05T05:33:41.140506-05:00",
       "name": "Temperature",
       "hidden": false,
       "precision": 2,
       "remarks": "",
       "gentity": 1403,
       "variable": 5683,
       "unit_of_measurement": 14,
       "time_zone": 1
   }

List time series groups
-----------------------

GET the list of time series groups for a station at
``/api/stations/XXX/timeseriesgroups/``::

   curl https://openmeteo.org/api/stations/1403/timeseriesgroups/

The result is a `paginated list`_ of time series groups::

    {
        "count": 13,
        "next": null,
        "previous": null,
        "results": [
            {...},
            {...},
            ...
        ]
    }

Time series
===========

Time series detail
------------------

You can GET the detail of a single time series at
``/api/stations/XXX/timeseriesgroups/YYY/timeseries/ZZZ/``::

    curl https://openmeteo.org/api/stations/1403/timeseriesgroups/483/timeseries/9511/

Response::

    {
        "id": 9511,
        "last_modified": "2015-04-05T05:33:41.140506-05:00",
        "type": "Initial",
        "time_step": "10min",
        "timeseries_group": 483
    }

The ``type`` is one of Initial, Checked, Regularized, and Aggregated.

List time series
----------------

GET the list of time series for a group at
``/api/stations/XXX/timeseriesgroups/YYY/timeseries/``::

    curl https://openmeteo.org/api/stations/1403/timeseriesgroups/483/timeseries/

The result is a `paginated list`_ of time series::

    {
        "count": 5,
        "next": null,
        "previous": null,
        "results": [
            {...},
            {...},
            ...
        ]
    }

Create time series
------------------

POST to create a time series::

    curl -X POST -H "Authorization: token OAUTH-TOKEN" \
        -d "timeseries_group=42" -d "type=Initial"-d "time_step=H" \
        https://openmeteo.org/api/stations/5/timeseriesgroups/42/timeseries/

The response is a 201 with a similar content as the GET detail response
(with the new data), unless there is a problem, in which case there's a
standard `error response`_.

When specifying nested objects, these objects are not created or
updated—only the id is used and a reference to the nested object with
that id is created.

Time series data
----------------

**GET the data** of a time series in CSV by appending ``data/`` to the
URL::

    curl https://openmeteo.org/api/stations/1334/timeseriesgroup/232/timeseries/10659/data/

Example of response::

    1998-12-10 16:40,6.3,
    1998-12-10 16:50,6.1,
    1998-12-10 17:00,6.0,
    1998-12-10 17:10,5.6,
    ...

Instead of CSV, you can **get HTS** by specifying the parameter
``fmt=hts``::

    curl 'https://openmeteo.org/api/stations/1334/timeseriesgroup/235/timeseries/10659/data/?fmt=hts`

Response::

    Count=926108
    Title=Temperature (from 1998)
    Comment=NTUA University Campus of Zografou
    Comment=
    Comment=Type: Raw data
    Timezone=EET (UTC+0200)
    Time_step=10,0
    Variable=Mean temperature
    Precision=1
    Location=23.787430 37.973850 4326
    Altitude=219.00

    1998-12-10 16:40,6.3,
    1998-12-10 16:50,6.1,
    1998-12-10 17:00,6.0,
    1998-12-10 17:10,5.6,
    ...

**Get only the last record** of the time series (in CSV) with ``bottom/``::

    curl https://openmeteo.org/api/stations/1334/timeseriesgroup/235/timeseries/10659/bottom/

Response::

    2018-07-09 11:19,0.000000,

**Append data** to the time series::

    curl -X POST -H "Authorization: token OAUTH-TOKEN" \
        -d $'timeseries_records=2018-12-19T11:50,25.0,\n2018-12-19T12:00,25.1,\n' \
        https://openmeteo.org/api/stations/1334/timeseriesgroups/235/timeseries/10659/data/

(The ``$'...'`` is a bash idiom that does nothing more than escape the
``\n`` in the string.)

The response is normally 204 (no content).

Time series chart data
----------------------

GET statistics for timeseries data in intervals by appending ``chart/``::

    curl https://openmeteo.org/api/stations/1334/timeseries/232/chart/

Example of response::

    [
      {
        "timestamp": 1579292086,
        "min": "1.00",
        "max": "18.00",
        "mean": 14.00"
      },
      {
        "timestamp": 1580079590,
        "min": "4.00",
        "max": "22.00",
        "mean": "18.53"
      },
      ...
    ]


You can provide time limits using the following query parameters
``start_date=<TIME>&end_date=<TIME>``.  For instance, to request data prior to
2015 only, we can make the following request::

    curl 'https://openmeteo.org/api/stations/1334/timeseries/232/chart/?end_date=2015-01-01T00:00`

The purpose of this endpoint is to be used when creating a chart for the
time series. When the user pans or zooms the chart, a new request with
different ``start_date`` and/or ``end_date`` is made. While transferring
the entire time series to the client would be simpler, it can be too
large. This endpoint only provides 200 points, so the transfer is
instant.

What the endpoint does is divide the time between ``start_date`` and
``end_date`` (or the entire time series time range) in 200 intervals.
For each interval it returns the interval's statistics and the middle of
the interval as the timestamp.

Other items of stations
=======================

Media and other station files
-----------------------------

List station files::

    curl https://openmeteo.org/api/stations/1334/files/

Response::

    {
      "count": 8,
      "next": null,
      "previous": null,
      "results": [
        {
          "id": 39,
          "last_modified": "2011-06-22T07:53:01.349877Z",
          "date": "1998-01-05",
          "content": "https://openmeteo.org/media/gentityfile/imported_hydria_gentityfile_1334-4.jpg",
          "descr": "West view",
          "remarks": "",
          "gentity": 1334
        },
        ...
      ]
    }

Or you can get the detail of a single one::

    curl https://openmeteo.org/api/stations/1334/files/39/

Response::

    {
      "id": 39,
      "last_modified": "2011-06-22T07:53:01.349877Z",
      "date": "1998-01-05",
      "content": "https://openmeteo.org/media/gentityfile/imported_hydria_gentityfile_1334-4.jpg",
      "descr": "West view",
      "remarks": "",
      "gentity": 1334
    },

Get content of such files::

    curl https://openmeteo.org/api/stations/1334/files/39/content/

The response is the contents of the file (usually binary data). The
response headers contain the appropriate ``Content-Type`` (derived from
the file's extension).

Events
------

List or get detail of station events::

    curl https://openmeteo.org/api/stations/1334/events/
    curl https://openmeteo.org/api/stations/1334/events/524/

Response example for the detail request::

    {
      "id": 524,
      "last_modified": null,
      "date": "1998-12-10",
      "user": "",
      "report": "Added air temperature and humidity sensor.",
      "gentity": 1334,
      "type": 2
    },

For the list request, the result is a `paginated list`_ of items.


.. _paginated list:

Pagination
==========

Some responses contain a paginated list. This has the following format::

    {
      "count": 109,
      "next": "http://openmeteo.org/api/stations/?page=2",
      "previous": null,
      "results": [
          {...},
          {...},
          {...},
          ...
        ]
    }

The returned object contains the following attributes:

**results**
   A list of items. Up to 20 items are returned (but this is
   configurable by specifying ``REST_FRAMEWORK["PAGE_SIZE"]`` in the
   settings).

**count**
   The total number of items this request returns.  If they are 20 or
   fewer, there is no other page.

**next**, **previous**
   The URLs for the next and previous page of results.


.. _error response:

Error responses
===============

When there is an error with the data of a POST, PATCH or PUT request,
the response code is 400 and the content has an error message for each
problematic field. For example::

    curl -v -X POST -H "Authorization: token OAUTH-TOKEN" \
    -d "gentity=1334" -d "variable=1234" -d "unit_of_measurement=1" \
    https://openmeteo.org/api/stations/1334/timeseries/

Response::

    {
      "time_zone": [
        "This field is required."
      ],
      "variable": [
        "Invalid pk \"1234\" - object does not exist."
      ]
    }

If there is an error that does not apply to a specific field but to the
data as a whole, the error message goes into ``non_field_errors``::

   {
     "non_field_errors": [
       "A time series with timeseries_group_id=2 and type=Initial already exists"
     ]
   }
