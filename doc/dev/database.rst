.. _database:

The database
============

Main principles
---------------

Enhydris supports PostgreSQL (with PostGIS).

In Django parlance, a *model* is a type of entity, which usually maps to
a single database table. Therefore, in Django, we usually talk of models
rather than of database tables, and we design models, which is close to
conceptual database design, leaving it to Django's object-relational
mapper to translate to the physical. In this text, we also speak more of
models than of tables. Since a model is a Python class, we describe it
as a Python class rather than as a relational database table. If,
however, you feel more comfortable with tables, you can generally read
the text understanding that a model is a table.

If you are interested in the physical structure of the database, you
need to know the model translation rules, which are quite simple:

* The name of the table is the lower case name of the model, with a
  prefix. The prefix for the core of the database is ``enhydris_``.
  (More on the prefix below).
* Tables normally have an implicit integer id field, which is the
  primary key of the table.
* Table fields have the same name as model attributes, except for
  foreign keys.
* Foreign keys have the name of the model attribute suffixed with
  ``_id``.
* When using `multi-table inheritance`_, the primary key of the child
  table is also a foreign key to the id field of the parent table. The
  name of the database column for the key of the child table is the
  lower cased parent model name suffixed with ``_ptr_id``.

The core of the Enhydris database is a list of measuring stations, with
additional information such as photos, videos, and the hydrological and
meteorological time series stored for each measuring station. This can
be used in or assisted by many more applications, which may or may not
be needed in each setup. A billing system is needed for agencies that
charge for their data, but not for those who offer them freely or only
internally. Some organisations may need to develop additional software
for managing aqueducts, and some may not. Therefore, the core is kept as
simple as possible. The core database tables use the ``enhydris_``
prefix.  Other applications use another prefix.  The name of a table is
the lowercased model name preceded by the prefix.  For example, the
table that corresponds to the :class:`~enhydris.models.Gentity` model is
``enhydris_gentity``.

Lookup tables
-------------

Lookup tables are those that are used for enumerated values. For
example, the list of variables is a lookup table. Most lookup tables
in the Enhydris database have three fields: *id*, *descr*, and
*short_descr*, and they all inherit the following `abstract base
class`_:

.. class:: enhydris.models.Lookup

   This class contains the common attribute of the lookup tables:

   .. attribute:: descr

   A character field with a descriptive name.

Most lookup tables are described in a relevant section of this
document, where their description fits better.

Lentities
---------

The Lentity is the superclass of people and groups. For example, a
measuring station can belong either to an organisation or an
individual. Lawyers use the word "entity" to refer to individuals and
organisations together, but this would create confusion because of the
more generic meaning of "entity" in computing; therefore, we use
"lentity", which is something like a legal entity. The lentity
hierarchy is implemented by using Django's `multi-table inheritance`_.

.. class:: enhydris.models.Lentity

   .. attribute:: remarks

      A text field of unlimited length.

.. class:: enhydris.models.Person

   .. attribute:: last_name
                  first_name
                  middle_names
                  initials

      The above four are all character fields. The :attr:`initials`
      contain the initials without the last name. For example, for
      Antonis Michael Christofides, :attr:`initials` would contain the
      value "A. M.".

.. class:: enhydris.models.Organization

   .. attribute:: enhydris.models.Organization.name
                  enhydris.models.Organization.acronym

      :attr:`~enhydris.models.Organization.name` and
      :attr:`~enhydris.models.Organization.acronym` are both character
      fields.

Gentity and its direct descendants: Gpoint, Gline, Garea
--------------------------------------------------------

A Gentity is a geographical entity. Examples of gentities (short for
geographical entities) are measuring stations, cities, boreholes and
watersheds. A gentity can be a point (e.g. stations and boreholes), a
surface (e.g. lakes and watersheds), a line (e.g. aqueducts), or a
network (e.g. a river). The gentities implemented in the core are
measuring stations and generic gareas. The gentity hierarchy is
implemented by using Django's `multi-table inheritance`_.

.. class:: enhydris.models.Gentity

   .. attribute:: enhydris.models.Gentity.name

      A field with the name of the gentity, such as the name of a
      measuring station. Up to 200 characters.

   .. attribute:: enhydris.models.Gentity.code

      An optional field with a code for the gentity. Up to 50
      characters. It can be useful for entities that have a code, e.g.
      watersheds are codified by the EU, and the watershed of Nestos
      River has code EL07.

   .. attribute:: enhydris.models.Gentity.remarks

      A field with general remarks about the gentity. Unlimited length.

   .. attribute:: enhydris.models.Gentity.geom

      This is a GeoDjango GeometryField_ that stores the geometry of the
      gentity.

      .. _geometryfield: https://docs.djangoproject.com/en/2.1/ref/contrib/gis/model-api/#geometryfield

.. class:: enhydris.models.Gpoint(Gentity)

   .. attribute:: enhydris.models.Gpoint.original_srid

      Specifies the reference system in which the user originally
      entered the co-ordinates of the point.  Valid *srid*'s are
      registered at http://www.epsg-registry.org/.  See also
      https://medium.com/@aptiko/introduction-to-geographical-co-ordinate-systems-4e143c5b21bc.

   .. attribute:: enhydris.models.Gpoint.altitude

      The altitude in metres above mean sea level.

.. class:: enhydris.models.Garea(Gentity)

   .. attribute:: enhydris.models.Garea.category

      A Garea belongs to a category, such as "water basin" or "country".
      Foreign key to ``GareaCategory``.

Additional information for generic gentities
--------------------------------------------

This section describes models that provide additional information
about gentities.

.. class:: enhydris.models.GentityFile

   This model stores general files for the gentity. For examples, for
   measuring stations, it can be photos, videos, sensor manuals, etc.

   .. attribute:: descr

      A short description or legend of the file.

   .. attribute:: remarks

      Remarks of unlimited length.

   .. attribute:: date

      For photos, it should be the date the photo was taken. For other
      kinds of files, it can be any kind of date.

   .. attribute:: content

      The actual content of the file; a Django FileField_. Note that,
      for generality, images are also stored in this attribute, and
      therefore they don't use an ImageField_, which means that the few
      facilities that ImageField offers are not available.

.. class:: enhydris.models.EventType(Lookup)

   Stores types of events.

.. class:: enhydris.models.GentityEvent

   An event is something that happens during the lifetime of a gentity
   and needs to be recorded. For example, for measuring stations, events
   such as malfunctions, maintenance sessions, and extreme weather
   phenomena observations can be recorded and provide a kind of log.

   .. attribute:: enhydris.models.GentityEvent.gentity

      The :class:`~enhydris.models.Gentity` to which the event refers.

   .. attribute:: enhydris.models.GentityEvent.date

      The date of the event.

   .. attribute:: enhydris.models.GentityEvent.type

      The :class:`~enhydris.models.EventType`.

   .. attribute:: enhydris.models.GentityEvent.user

      The username of the user who entered the event to the database.

   .. attribute:: enhydris.models.GentityEvent.report

      A report about the event; a text field of unlimited length.

.. _station:

Station and its related models
------------------------------

.. class:: enhydris.models.Station(Gpoint)

   .. attribute:: enhydris.models.Station.owner

      The :class:`~enhydris.models.Lentity` that owns the station.

   .. attribute:: enhydris.models.Station.is_automatic

      A boolean field showing whether the station is automatic.

   .. attribute:: enhydris.models.Station.start_date
                  enhydris.models.Station.end_date

      An optional pair of dates indicating was installed and abolished.

   .. attribute:: enhydris.models.Station.overseer

      The overseers is the person responsible for the meteorological
      station in the past. In the case of manual (not automatic)
      stations, this means the weather observers.  This is a simple text
      field.

Time series and related models
------------------------------

.. class:: enhydris.models.Variable(Lookup)

   This model stores a variable, such as "precipitation",
   "evaporation", "temperature" etc.

.. class:: enhydris.models.UnitOfMeasurement(Lookup)

   This model stores a unit of measurement. In addition to
   :class:`~enhydris.models.Lookup` fields, it has the following
   additional fields:

   .. attribute:: enhydris.models.UnitOfMeasurement.symbol

      The symbol used for the unit, in UTF-8 plain text.

   .. attribute:: enhydris.models.UnitOfMeasurement.variables

      A many-to-many relationship to :class:`~enhydris.models.Variable`.

.. class:: enhydris.models.TimeZone

   This model stores time zones.

   .. attribute:: enhydris.models.TimeZone.code

      The code name of the time zone, such as CET or UTC.

   .. attribute:: enhydris.models.TimeZone.utc_offset

      A number, in minutes, with the offset of the time zone from UTC.
      For example, CET has a utc_offset of 60, whereas CDT is -300.
      This model only stores time zones with a constant utc offset, and
      not time zones with variable offsets. For example, we don't store
      CT (North American Central Time), because this is different in
      summer and in winter; instead, we store CST (Central Standard
      Time) and CDT (Central Daylight Time), which are the two
      occurrences of CT. The time stamps of a given time series may not
      observe summer time; they must always have the same utc offset
      throught the time series.

.. class:: enhydris.models.Timeseries

   Holds time series.

   .. attribute:: enhydris.models.Timeseries.gentity

      The :class:`~enhydris.models.Gentity` to which the time series
      refers.

   .. attribute:: enhydris.models.Timeseries.variable

      The :class:`~enhydris.models.Variable` of the time series.

   .. attribute:: enhydris.models.Timeseries.unit_of_measurement

      The :class:`~enhydris.models.UnitOfMeasurement`.

   .. attribute:: enhydris.models.Timeseries.name

      A descriptive name for the time series.

   .. attribute:: enhydris.models.Timeseries.precision

      An integer specifying the precision of the values of the time
      series, in number of decimal digits. It can be negative; for
      example, a precision of -2 indicates that the values are accurate
      to the hundred, ex. 100, 200 etc.

   .. attribute:: enhydris.models.Timeseries.time_zone

      The :class:`~enhydris.models.TimeZone` in which the time series'
      timestamps are.

   .. attribute:: enhydris.models.Timeseries.remarks

      A text field of unlimited length.

   .. attribute:: enhydris.models.Timeseries.hidden

      A boolean field to control the visibility of timeseries in related
      pages.

   .. attribute:: enhydris.models.Timeseries.time_step

      The :attr:`~enhydris.models.Timeseries.time_step` is a string.
      Some time series are completely irregular; in that case,
      :attr:`~enhydris.models.Timeseries.time_step` is empty. Otherwise,
      it contains an appropriate time step as a `pandas "frequency"
      string`_, e.g.  "10min", "H", "M", "Y".

      .. _pandas "frequency" string: https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#dateoffset-objects

   .. attribute:: enhydris.models.Timeseries.datafile

      The file where the time series data are stored. The attribute is a
      Django FileField_. The format of this file is documented in
      htimeseries as `text format`_.

      Usually you don't need to access this file directly; instead, use
      methods :meth:`~enhydris.models.Timeseries.get_data`,
      :meth:`~enhydris.models.Timeseries.set_data`,
      :meth:`~enhydris.models.Timeseries.append_data`,
      :meth:`~enhydris.models.Timeseries.get_first_line` and
      :meth:`~enhydris.models.Timeseries.get_last_line`.

   .. attribute:: enhydris.models.Timeseries.start_date
                  enhydris.models.Timeseries.end_date

      The start and end date of the time series, or ``None`` if the time
      series is empty. These are redundant; the start and end date of
      the time series could be found with
      :meth:`~enhydris.models.get_first_line` and
      :meth:`~enhydris.models.get_last_line`. However, these attributes
      can easily be used in database queries. Normally you don't need to
      set them; they are set automatically when the time series is
      saved. If you write to the
      :attr:`~enhydris.models.Timeseries.datafile`, you must
      subsequently call :meth:`save()` to update these fields.

   .. method:: enhydris.models.Timeseries.get_data(start_date=None, end_date=None)

      Return the data of the file in a HTimeseries_ object. If
      *start_date* or *end_date* are specified, only this part of the
      data is returned.

   .. method:: enhydris.models.Timeseries.set_data(data)

      Replace all of the time series with *data*, which must be one of
      the following:

       * A Pandas DataFrame
       * A HTimeseries_ object
       * A filelike object containing time series data in `text format`_
         or `file format`_. If it is in file format, the header is
         ignored.

   .. method:: enhydris.models.Timeseries.append_data(data)

      Same as :meth:`~enhydris.models.Timeseries.set_data`, except that
      the data is appended to the already existing data. Raises
      ``ValueError`` if the new data is not more recent than the old
      data.

   .. method:: enhydris.models.Timeseries.get_first_line()
               enhydris.models.Timeseries.get_last_line()

      Return the first or last line of the data file (i.e. the first or
      last record of the time series in text format), or an empty string
      if the time series contains no records.


.. _htimeseries: https://github.com/openmeteo/htimeseries
.. _text format: https://github.com/openmeteo/htimeseries#text-format
.. _file format: https://github.com/openmeteo/htimeseries#file-format
.. _multi-table inheritance: http://docs.djangoproject.com/en/dev/topics/db/models/#id6
.. _abstract base class: http://docs.djangoproject.com/en/dev/topics/db/models/#id5
.. _filefield: http://docs.djangoproject.com/en/dev/ref/models/fields/#filefield
.. _imagefield: http://docs.djangoproject.com/en/dev/ref/models/fields/#imagefield
