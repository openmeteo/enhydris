.. _database:

The database
============

Main principles
---------------

The Enhydris database is implemented in PostgreSQL. While the
implementation of the database is through Django's object-relational
mapper, which is more or less RDBMS-independent, Enhydris uses
PostgreSQL's geographic features, so it is not portable. It also uses
some custom PostgreSQL code for storing timeseries (however this is
likely to change in the future).

In Django parlance, a *model* is a type of entity, which usually maps
to a single database table. Therefore, in Django, we usually talk of
models rather than of database tables, and we design models, which is
close to a conceptual database design, leaving it to Django's
object-relational mapper to translate to the physical. In this text,
we also speak more of models than of tables. Since a model is a Python
class, we describe it as a Python class rather than as a relational
database table. If, however, you feel more comfortable with tables,
you can generally read the text understanding that a model is a table.

If you are interested in the physical structure of the database, you
need to know the model translation rules, which are quite simple:

* The name of the table is the lower case name of the model, with a
  prefix. The prefix for the core of the database is ``hcore_``. (More
  on the prefix below).
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

There are two drawings that accompany this text: the drawing for the
:download:`conceptual data model <hcore-cdm.pdf>`, and the drawing for
the :download:`physical data model <hcore-pdm.pdf>`.  You should avoid
looking at the physical data model; it is cluttered and confusing,
since it is machine-generated. It is only provided for the benefit of
those who are not comfortable with Django's object-relational mapping.
However, it is best to learn to read the conceptual data model; if you
become acquainted with the Django's object-relational mapping rules
listed above, you will be able to write SQL commands effortlessly, by
using these rules in your head.  The drawing of the physical data
model is also far more likely to contain errors or to be outdated than
the drawing and documentation for the conceptual data model.

The core of the Enhydris database is a list of measuring stations,
with additional information such as instruments, photos, videos, and
so on, and the hydrological and meteorological time series stored for
each measuring station. This can be used in or assisted by many more
applications, which may or may not be needed in each setup. A billing
system is needed for agencies that charge for their data, but not for
those who offer them freely or only internally. Some organisations may
need to develop additional software for managing aqueducts, and some
may not. Therefore, the core is kept as simple as possible. The core
database tables use the ``hcore_`` prefix.  Other applications use
another prefix. The name of a table is the lowercased model name
preceeded by the prefix.  For example, the table that corresponds to
the :class:`~enhydris.hcore.models.Gentity` model is ``hcore_gentity``.

.. _multilingual:

.. admonition:: Multilinguality

   Originally, the database was designed in order to be multilingual,
   that is, so that the content could be stored in an unlimited number of
   languages. The `django-multilingual`_ framework was used for this
   purpose. However, django-multilingual bugs slowed development too
   much, and it was decided to go for a more modest solution: texts
   are simply stored in two languages: the local language and the
   alternative language. For example, for a description, there are the
   "descr" field and the "descr_alt" field. Which languages are "descr"
   and "descr_alt" depends on the installation. For example, we use Greek
   as the local language and English as the alternative language.

   We hope to get rid of this, but this will involve fixing
   django-multilingual or using another multilingual framework.

   When any field in the API is marked as being multilingual, it means
   that it is accompanied by an additional identical field that has
   "_alt" appended to its name. (It also means that, instead, it should
   be defined in a :class:`Translation` class nested in the model
   class, as would be the case if `django-multilingual`_ were used.)

Lookup tables
-------------

Lookup tables are those that are used for enumerated values. For
example, the list of variables is a lookup table. Most lookup tables
in the Enhydris database have three fields: *id*, *descr*, and
*short_descr*, and they all inherit the following `abstract base
class`_:

.. class:: enhydris.hcore.models.Lookup

   This class contains the common attribute of the lookup tables:

   .. attribute:: descr

   A :ref:`multilingual <multilingual>` character field with a
   descriptive name.

Most lookup tables are described in a relevant section of this
document, where their description fits better; for example,
:class:`~enhydris.hcore.models.StationType` is described at Section
:ref:`station`.

Lentities
---------

The Lentity is the superclass of people and groups. For example, a
measuring station can belong either to an organisation or an
individual. Lawyers use the word "entity" to refer to individuals and
organisations together, but this would create confusion because of the
more generic meaning of "entity" in computing; therefore, we use
"lentity", which is something like a legal entity. The lentity
hierarchy is implemented by using Django's `multi-table inheritance`_.

.. class:: enhydris.hcore.models.Lentity

   .. attribute:: remarks

      A :ref:`multilingual <multilingual>` text field of unlimited
      length.

.. class:: enhydris.hcore.models.Person

   .. attribute:: last_name

   .. attribute:: first_name

   .. attribute:: middle_names

   .. attribute:: initials

      The above four are all :ref:`multilingual <multilingual>`
      character fields. The :attr:`initials` contain the initials without
      the last name. For example, for Antonis Michael Christofides,
      :attr:`initials` would contain the value "A. M.".

.. class:: enhydris.hcore.models.Organization

   .. attribute:: enhydris.hcore.models.Organization.name

   .. attribute:: enhydris.hcore.models.Organization.acronym

      :attr:`~enhydris.hcore.models.Organization.name` and
      :attr:`~enhydris.hcore.models.Organization.acronym` are both
      :ref:`multilingual <multilingual>` character fields.

Gentity and its direct descendants: Gpoint, Gline, Garea
--------------------------------------------------------

A Gentity is a geographical entity. Examples of gentities (short for
geographical entities) are measuring stations, cities, boreholes and
watersheds. A gentity can be a point (e.g. stations and boreholes), a
surface (e.g. lakes and watersheds), a line (e.g. aqueducts), or a
network (e.g. a river). The gentities implemented in the core are
measuring stations and water basins. The gentity hierarchy is
implemented by using Django's `multi-table inheritance`_.

.. class:: enhydris.hcore.models.Gentity

   .. attribute:: enhydris.hcore.models.Gentity.name

      A :ref:`multilingual <multilingual>` field with the name of the
      gentity, such as the name of a measuring station. Up to 200
      characters.

   .. attribute:: enhydris.hcore.models.Gentity.short_name

      A :ref:`multilingual <multilingual>` field with a short name of
      the gentity. Up to 50 characters.

   .. attribute:: enhydris.hcore.models.Gentity.remarks

      A :ref:`multilingual <multilingual>` field with general remarks
      about the gentity. Unlimited length.

   .. attribute:: enhydris.hcore.models.Gentity.water_basin

      The :class:`water basin <models.WaterBasin>` where the gentity is.

   .. attribute:: enhydris.hcore.models.Gentity.water_division

      The water division in which the gentity is.  Foreign key to
      :class:`~enhydris.hcore.models.WaterDivision`.

   .. attribute:: enhydris.hcore.models.Gentity.political_division

      The country or other political division in which the gentity is.
      Foreign key to :class:`~enhydris.hcore.models.PoliticalDivision`.

.. class:: enhydris.hcore.models.Gpoint(Gentity)

   .. attribute:: enhydris.hcore.models.Gpoint.point

      This is a GeoDjango PointField_ that stores the 2-d location of
      the point.

      .. _pointfield: http://docs.djangoproject.com/en/1.2/ref/contrib/gis/model-api/

   .. attribute:: enhydris.hcore.models.Gpoint.srid

      Specifies the reference system in which the user originally
      entered the co-ordinates of the point.  Valid *srid*'s are
      registered at http://www.epsg-registry.org/.  See also
      http://itia.ntua.gr/antonis/technical/coordinate-systems/.

   .. attribute:: enhydris.hcore.models.Gpoint.approximate

      This boolean field has the value ``True`` if the horizontal
      co-ordinates are approximate. This normally means that the user
      who specified the co-ordinates did not really know the location
      of the point, but for convenience placed it somewhere visually
      so that the GIS system can have a rough idea of where to show it
      and e.g. in which basin it is.

   .. attribute:: enhydris.hcore.models.Gpoint.altitude

   .. attribute:: enhydris.hcore.models.Gpoint.asrid

      These attributes store the altitude. *asrid* specifies the
      reference system, which defines how *altitude* is to be
      understood. *asrid* can be empty, in which case, *altitude* is
      given in metres above mean sea level.

.. class:: enhydris.hcore.models.Gline(Gentity)

   .. attribute:: enhydris.hcore.models.Gline.gpoint1

   .. attribute:: enhydris.hcore.models.Gline.gpoint2

      The starting and ending points of the line; foreign keys to
      :class:`~enhydris.hcore.models.Gpoint`.

   .. attribute:: enhydris.hcore.models.Gline.length

      The length of the line in meters.

.. class:: enhydris.hcore.models.Garea(Gentity)

   .. attribute:: enhydris.hcore.models.Garea.area

      The size of the area in square meters.

Additional information for generic gentities
--------------------------------------------

This section describes models that provide additional information
about gentities.

.. class:: enhydris.hcore.models.PoliticalDivision(Garea)

      From an administrative point of view, the world is divided into
      countries. Each country is then divided into further divisions,
      which may be called states, districts, counties, provinces,
      prefectures, and so on, which may be further subdivided. Greece,
      for example, is divided in districts, which are subdivided in
      prefectures. How these divisions and subdivisions are named, and
      the way and depth of subdividing, differs from country to
      country.

      :class:`~enhydris.hcore.models.PoliticalDivision` is a recursive
      model that represents such political divisions. The top-level
      political division is a country, and lower levels differ from
      country to country.

      .. attribute:: enhydris.hcore.models.PoliticalDivision.parent

         For top-level political divisions, that is, countries, this
         attribute is null; otherwise, it points to the containing
         political division.

      .. attribute:: enhydris.hcore.models.PoliticalDivision.code

         For top-level political divisions, that is, countries, this
         is the two-character ISO 3166 country code. For lower level
         political divisions, it can be a country-specific division
         code; for example, for US states, it can be the
         two-character state code. Up to five characters.

.. class:: enhydris.hcore.models.WaterDivision(Garea)

   A water division is a collection of basins. Water divisions may be
   used for administrative purposes, each water division being under
   the authority of one organisation or organisational division.
   Usually a water division consists of adjacent basins or of nearby
   islands or both.

.. class:: enhydris.hcore.models.WaterBasin(Garea)

      A water basin.

      .. attribute:: enhydris.hcore.models.WaterBasin.parent

         If this is a subbasin, this field points to the containing
         water basin.

      .. attribute:: enhydris.hcore.models.WaterBasin.water_division

         The :class:`water district <models.WaterDivision>` in which
         the water basin is.

.. class:: enhydris.hcore.models.GentityAltCodeType(Lookup)

   The different kinds of codes that a gentity may have; see
   :class:`~enhydris.hcore.models.GentityAltCode` for more information.

.. class:: enhydris.hcore.models.GentityAltCode

      While each gentity is automatically given an id by the system,
      some stations may also have alternative codes. For example, in
      Greece, if a database contains a measuring station that is owned
      by a specific organisation, the station has the id given to it
      by the database, but in addition it may have a code assigned by
      the organisation; some also have a code created by older
      inter-organisational efforts to create a unique list of stations
      in Greece; and some also have a WMO code. This model therefore
      stores alternative codes.

      .. attribute:: enhydris.hcore.models.GentityAltCode.gentity

         A foreign key to :class:`~enhydris.hcore.models.Gentity`.

      .. attribute:: enhydris.hcore.models.GentityAltCode.type

         The type of alternative code; one of those listed in
         :class:`~enhydris.hcore.models.GentityAltCodeType`.

      .. attribute:: enhydris.hcore.models.GentityAltCode.value

         A character field with the actual code.

.. class:: enhydris.hcore.models.FileType(Lookup)

   A lookup that contains one additional field:

   .. attribute:: enhydris.hcore.models.FileType.mime_type

      The mime type, like ``image/jpeg``.


.. class:: enhydris.hcore.models.GentityFile

   This model stores general files for the gentity. For examples, for
   measuring stations, it can be photos, videos, sensor manuals, etc.

   .. attribute:: descr

      A :ref:`multilingual <multilingual>` short description or legend of
      the file.

   .. attribute:: remarks

      :ref:`Multilingual <multilingual>` remarks of unlimited length.

   .. attribute:: date

      For photos, it should be the date the photo was taken. For other
      kinds of files, it can be any kind of date.

   .. attribute:: file_type

      The type of the file; a foreign key to
      :class:`~enhydris.hcore.models.FileType`.

   .. attribute:: content

      The actual content of the file; a Django FileField_. Note that,
      for generality, images are also stored in this attribute, and
      therefore they don't use an ImageField_, which means that the
      few facilities that ImageField offers are not available.

.. class:: enhydris.hcore.models.EventType(Lookup)

   Stores types of events.

.. class:: enhydris.hcore.models.GentityEvent

   An event is something that happens during the lifetime of a gentity
   and needs to be recorded. For example, for measuring stations,
   events such as malfunctions, maintenance sessions, and extreme
   weather phenomena observations can be recorded and provide a kind
   of log.

   .. attribute:: enhydris.hcore.models.GentityEvent.gentity

      The :class:`~enhydris.hcore.models.Gentity` to which the event refers.

   .. attribute:: enhydris.hcore.models.GentityEvent.date

      The date of the event.

   .. attribute:: enhydris.hcore.models.GentityEvent.type

      The :class:`~enhydris.hcore.models.EventType`.

   .. attribute:: enhydris.hcore.models.GentityEvent.user

      The username of the user who entered the event to the database.

   .. attribute:: enhydris.hcore.models.GentityEvent.report

      A report about the event; a text field of unlimited length.

.. _station:

Station and its related models
------------------------------

.. class:: enhydris.hcore.models.StationType(Lookup)

   The station type, such as "meteorological" or "stage measuring".

.. class:: enhydris.hcore.models.Station(Gpoint)

   .. attribute:: enhydris.hcore.models.Station.owner

      The :class:`~enhydris.hcore.models.Lentity` that owns the station.

   .. attribute:: enhydris.hcore.models.Station.type

      The :class:`~enhydris.hcore.models.StationType`.

   .. attribute:: enhydris.hcore.models.Station.is_automatic

      A boolean field showing whether the station is automatic.

   .. attribute:: enhydris.hcore.models.Station.start_date

   .. attribute:: enhydris.hcore.models.Station.end_date

      An optional pair of dates indicating when the station started and
      stopped working.

   .. attribute:: enhydris.hcore.models.Station.overseers

      The overseers are the persons who are or have been responsible
      for each meteorological station in the past. In the case of
      traditional (not automatic) stations, this means the weather
      observers. At a given time, each station has only one observer.
      This is a many-to-many field, through model
      :class:`~enhydris.hcore.models.Overseer`.

.. class:: enhydris.hcore.models.Overseer

      .. attribute:: enhydris.hcore.models.Overseer.station

         A foreign key to :class:`~enhydris.hcore.models.Station`.

      .. attribute:: enhydris.hcore.models.Overseer.person

         A foreign key to :class:`~enhydris.hcore.models.Person`.

      .. attribute:: enhydris.hcore.models.Overseer.is_current

         A boolean value indicating whether this person is the current
         observer. For current overseers, the
         :attr:`~enhydris.hcore.models.Overseer.end_date` below must
         be null;
         however, a null end_date could also mean that the end_date is
         unknown, not necessarily that the overseer is the current
         overseer.

      .. attribute:: enhydris.hcore.models.Overseer.start_date

      .. attribute:: enhydris.hcore.models.Overseer.end_date

.. class:: enhydris.hcore.models.InstrumentType(Lookup)

   The instrument type, such as "Thermometer".

.. class:: enhydris.hcore.models.Instrument

   A measuring instrument or sensor that belongs to a station.

   .. attribute:: enhydris.hcore.models.Instrument.station

      The :class:`~enhydris.hcore.models.Station` to which the instrument belongs.

   .. attribute:: enhydris.hcore.models.Instrument.type

      The :class:`~enhydris.hcore.models.InstrumentType`.

   .. attribute:: enhydris.hcore.models.Instrument.name

      A :ref:`multilingual <multilingual>` field with a descriptive
      name.

   .. attribute:: enhydris.hcore.models.Instrument.remarks

      A :ref:`multilingual <multilingual>` field with remarks of
      unlimited length.

   .. attribute:: enhydris.hcore.models.Instrument.manufacturer

      The name of the manufacturer. For simplicity, this is not a
      foreign key to :class:`~enhydris.hcore.models.Organization`;
      this would be overkill.

   .. attribute:: enhydris.hcore.models.Instrument.model

      The model name.

   .. attribute:: enhydris.hcore.models.Instrument.start_date

   .. attribute:: enhydris.hcore.models.Instrument.end_date

      The dates of start and end of operation.

Time series and related models
------------------------------

.. class:: enhydris.hcore.models.Variable(Lookup)

   This model stores a variable, such as "precipitation",
   "evaporation", "temperature" etc.

.. class:: enhydris.hcore.models.UnitOfMeasurement(Lookup)

   This model stores a unit of measurement. In addition to
   :class:`~enhydris.hcore.models.Lookup` fields, it has the following
   additional fields:

   .. attribute:: enhydris.hcore.models.UnitOfMeasurement.symbol

      The symbol used for the unit, in UTF-8 plain text.

   .. attribute:: enhydris.hcore.models.UnitOfMeasurement.variables

      A many-to-many relationship to
      :class:`~enhydris.hcore.models.Variable`.

.. class:: enhydris.hcore.models.TimeZone

   This model stores time zones.

   .. attribute:: enhydris.hcore.models.TimeZone.code

      The code name of the time zone, such as CET or UTC.

   .. attribute:: enhydris.hcore.models.TimeZone.utc_offset

      A number, in minutes, with the offset of the time zone from UTC.
      For example, CET has a utc_offset of 60, whereas CDT is -300.
      This model only stores time zones with a constant utc offset,
      and not time zones with variable offsets. For example, we don't
      store CT (North American Central Time), because this is
      different in summer and in winter; instead, we store CST
      (Central Standard Time) and CDT (Central Daylight Time), which
      are the two occurrences of CT. The time stamps of a given time
      series may not observe summer time; they must always have the
      same utc offset throught the time series.

.. class:: enhydris.hcore.models.TimeStep(Lookup)

   This model holds time steps. The
   :attr:`~enhydris.hcore.models.Lookup.descr` attribute inherited by
   :class:`~enhydris.hcore.models.Lookup` holds a descriptive
   name for the time step, such as "daily" or "monthly". The model has
   two additional attributes:

   .. attribute:: length_minutes

   .. attribute:: length_months

      One of these two attributes must be zero. For example, a daily
      time step has length_minutes=1440 and length_months=0; an
      annual time step has length_minutes=0 and length_months=12.

.. class:: enhydris.hcore.models.Timeseries

   Hold time series.

   .. attribute:: enhydris.hcore.models.Timeseries.gentity

      The :class:`~enhydris.hcore.models.Gentity` to which the time
      series refers.

   .. attribute:: enhydris.hcore.models.Timeseries.variable

      The :class:`~enhydris.hcore.models.Variable` of the time series.

   .. attribute:: enhydris.hcore.models.Timeseries.unit_of_measurement

      The :class:`~enhydris.hcore.models.UnitOfMeasurement`.

   .. attribute:: enhydris.hcore.models.Timeseries.name

      A descriptive name for the time series.

   .. attribute:: enhydris.hcore.models.Timeseries.precision

      An integer specifying the precision of the values of the time
      series, in number of decimal digits. It can be negative; for
      example, a precision of -2 indicates that the values are
      accurate to the hundred, ex. 100, 200 etc.

   .. attribute:: enhydris.hcore.models.Timeseries.time_zone

      The :class:`~enhydris.hcore.models.TimeZone` in which the time
      series' timestamps are.

   .. attribute:: enhydris.hcore.models.Timeseries.remarks

      A text field of unlimited length.

   .. attribute:: enhydris.hcore.models.Timeseries.instrument

      The instrument that measured the time series; a foreign key to
      :class:`~enhydris.hcore.models.Instrument`. This can be null, as
      there are time series that are not measured by instruments, as
      are, for example, time series resulting from processing of other
      time series.

   .. attribute:: enhydris.hcore.models.Timeseries.hidden

      A boolean field to control the visibility of timeseries in related pages.

   .. attribute:: enhydris.hcore.models.Timeseries.time_step
                  enhydris.hcore.models.Timeseries.timestamp_rounding_minutes
                  enhydris.hcore.models.Timeseries.timestamp_rounding_months
                  enhydris.hcore.models.Timeseries.timestamp_offset_minutes
                  enhydris.hcore.models.Timeseries.timestamp_offset_months

      The :attr:`~enhydris.hcore.models.Timeseries.time_step` is a
      foreign key to :class:`~enhydris.hcore.models.TimeStep`. Some
      time series are completely irregular; in that case,
      :attr:`~enhydris.hcore.models.Timeseries.time_step` (and all
      other time step related attributes) is null. Otherwise, it
      contains an appropriate time step. For an explanation of the
      other four attributes, see the :class:`timeseries.TimeStep`
      class.
      :attr:`~enhydris.hcore.models.Timeseries.timestamp_offset_minutes`
      and
      :attr:`~enhydris.hcore.models.Timeseries.timestamp_offset_months`
      must always be present if the time step is not null.  The
      rounding attributes may, however, be null, if the time
      series is not strict, that is, if it does have a time step, but
      that time step contains irregularities. As an example, a time
      series measured by an automatic meteorological station every ten
      minutes will usually have a rounding of 0 minutes, which
      means the timestamps will end in :10, :20, :30, etc; but a clock
      error or a setup error could result in the timestamps ending in
      :11, :21, :31 for a brief period of time. In that case, we say
      that the time series has a nonstrict time step of 10 minutes,
      which means it has no specific rounding.

   .. attribute:: enhydris.hcore.models.Timeseries.datafile

      The file where the time series data are stored. The attribute is a
      Django FileField_. The format of this file is documented in
      pthelma as `text format`_.

      Usually you don't need to access this file directly; instead, use
      methods :meth:`~enhydris.hcore.models.Timeseries.get_all_data`,
      :meth:`~enhydris.hcore.models.Timeseries.set_data`,
      :meth:`~enhydris.hcore.models.Timeseries.append_data`,
      :meth:`~enhydris.hcore.models.Timeseries.get_first_line` and
      :meth:`~enhydris.hcore.models.Timeseries.get_last_line`.

   .. attribute:: enhydris.hcore.models.Timeseries.start_date
                  enhydris.hcore.models.Timeseries.end_date

      The start and end date of the time series, or ``None`` if the time
      series is empty. These are redundant; the start and end date of
      the time series could be found with
      :meth:`~enhydris.hcore.models.get_first_line` and
      :meth:`~enhydris.hcore.models.get_last_line`. However, these
      attributes can easily be used in database queries. Normally you
      don't need to set them; they are set automatically when the time
      series is saved. If you write to the
      :attr:`~enhydris.hcore.models.Timeseries.datafile`, you must
      subsequently call :meth:`save()` to update these fields.

   .. method:: enhydris.hcore.models.Timeseries.get_all_data()

      Return all data of the file in a `pthelma Timeseries object`_.

   .. method:: enhydris.hcore.models.Timeseries.set_data(data)

      Replace all of the time series with *data*, which must be a
      filelike object containing time series data in `text format`_ or
      `file format`_. If it is in text format, the header is ignored.

   .. method:: enhydris.hcore.models.Timeseries.append_data(data)

      Same as :meth:`~enhydris.hcore.models.Timeseries.set_data`, except
      that the data is appended to the already existing data. Raises
      ``ValueError`` if the new data is not more recent than the old
      data.

   .. method:: enhydris.hcore.models.Timeseries.get_first_line()
               enhydris.hcore.models.Timeseries.get_last_line()

      Return the first or last line of the data file (i.e. the first or
      last record of the time series in text format), or an empty string
      if the time series contains no records.


.. _text format: http://pthelma.readthedocs.io/en/latest/dev/timeseries.html#text-format
.. _file format: http://pthelma.readthedocs.io/en/latest/dev/timeseries.html#file-format
.. _multi-table inheritance: http://docs.djangoproject.com/en/dev/topics/db/models/#id6
.. _django-multilingual: http://code.google.com/p/django-multilingual/
.. _abstract base class: http://docs.djangoproject.com/en/dev/topics/db/models/#id5
.. _filefield: http://docs.djangoproject.com/en/dev/ref/models/fields/#filefield
.. _imagefield: http://docs.djangoproject.com/en/dev/ref/models/fields/#imagefield
.. _pthelma timeseries object: http://pthelma.readthedocs.io/en/latest/dev/timeseries.html#timeseries-objects
