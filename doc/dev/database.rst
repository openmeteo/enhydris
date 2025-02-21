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

   .. attribute:: enhydris.models.Gentity.display_timezone

      Timestamps of time series records are stored in UTC. This
      attribute specifies the time zone to which timestamps are
      converted before displaying or downloading time series. It is a
      string holding a key from the Olson time zone list. Currently only
      time zones starting with ``Etc/GMT`` are supported.

      Although the storage format of the time zone is ``Etc/GMT[±XX]``,
      it is displayed differently on the admin (and elsewhere).
      ``Etc/GMT`` is displayed as ``UTC``; ``Etc/GMT-2`` (2 hours
      **east** of UTC) is displayed as ``UTC+0200``; and so on.

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
           enhydris.models.GentityImage

   These models store files and images for the gentity. The difference
   between :class:`~enhydris.models.GentityFile` and
   :class:`~enhydris.models.GentityImage` is that
   :class:`~enhydris.models.GentityImage` objects are shown in a gallery
   in the station detail page, whereas files are shown in a much less
   prominent list.

   .. attribute:: descr

      A short description or legend of the file/image.

   .. attribute:: remarks

      Remarks of unlimited length.

   .. attribute:: date

      For photos, it should be the date the photo was taken. For other
      kinds of files, it can be any kind of date.

   .. attribute:: content

      The actual content of the file; a Django FileField_ (for
      :class:`~enhydris.models.GentityImage`) or ImageField_ (for
      :class:`~enhydris.models.GentityFile`).

   .. attribute:: featured

      This attribute exists for :class:`~enhydris.models.GentityImage`
      only. In the station detail page, one of the images (the
      "featured" image) is shown in large size (the rest are shown as a
      thumbnail gallery).  This attribute indicates the featured image.
      If there are more than one featured images (or if there is none),
      images are sorted by :attr:`descr`, and the first one is featured.

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

   .. attribute:: enhydris.models.Station.start_date
                  enhydris.models.Station.end_date

      An optional pair of dates indicating was installed and abolished.

   .. attribute:: enhydris.models.Station.overseer

      The overseer is the person responsible for the meteorological
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

.. class:: enhydris.models.TimeseriesGroup

   The time series a station holds are organized in groups. Each group
   contains time series with essentially the same kind of data but in a
   different time step or in a different checking status. For example,
   if you have a temperature sensor that measures temperature every 10
   minutes, then you will have a "temperature" time series group, which
   will contain the initial (raw) time series, and it may also contain
   the checked time series, the regularized time series, the hourly time
   series, etc. (If you have two temperature sensors, you'll have two
   time series groups.)

   We avoid showing the term "time series group" to the user (instead,
   we are being vague, like "Data", or we might sometimes use
   "time series" when we actually mean a time series group). Sometimes
   we can't avoid it though (notably in the admin).

   .. attribute:: enhydris.models.TimeseriesGroup.gentity

      The :class:`~enhydris.models.Gentity` to which the time series
      group refers.

   .. attribute:: enhydris.models.TimeseriesGroup.variable

      The :class:`~enhydris.models.Variable`.

   .. attribute:: enhydris.models.TimeseriesGroup.unit_of_measurement

      The :class:`~enhydris.models.UnitOfMeasurement`.

   .. attribute:: enhydris.models.TimeseriesGroup.name

      A descriptive name for the time series group. If this is blank,
      the name of the variable is used (e.g. "Temperature"), which is
      appropriate in most cases. However, if there are two time series
      groups with the same variable (such as when you have two
      temperature sensors), the user would want to specify a name for
      the time series group.

   .. attribute:: enhydris.models.TimeseriesGroup.precision

      An integer specifying the precision of the values of the time
      series, in number of decimal digits. It can be negative; for
      example, a precision of -2 indicates that the values are accurate
      to the hundred, ex. 100, 200 etc.

   .. attribute:: enhydris.models.TimeseriesGroup.remarks

      A text field of unlimited length.

   .. attribute:: enhydris.models.TimeseriesGroup.hidden

      A boolean field to control the visibility of the time series group
      in related pages.

   .. method:: enhydris.models.TimeseriesGroup.get_name()

      The time series group name; if
      :attr:`~enhydris.models.TimeseriesGroup.name` is empty, it is the
      variable name, otherwise it is
      :attr:`~enhydris.models.TimeseriesGroup.name`.

   .. attribute:: enhydris.models.TimeseriesGroup.default_timeseries

      This property returns the regularized time series of the group, and if
      that does not exist, the checked time series, and if that does not exist,
      the initial time series, and if that does not exist, ``None``.

   .. attribute:: enhydris.models.TimeseriesGroup.start_date
                  enhydris.models.TimeseriesGroup.end_date

      These read-only properties are the start and end date of the
      default time series (see
      :attr:`~enhydris.models.TimeseriesGroup.default_timeseries`).

.. class:: enhydris.models.Timeseries

   This model holds metadata for time series. The time series records
   are stored in :class:`~enhydris.models.TimeseriesRecord`.

   .. attribute:: enhydris.models.Timeseries.timeseries_group

      The :class:`~enhydris.models.TimeseriesGroup` to which the time
      series belongs.

   .. attribute:: enhydris.models.Timeseries.type

      An integer field with numbers that symbolize the time series type:
      initial or checked or regularized or aggregated.

   .. attribute:: enhydris.models.Timeseries.time_step

      The :attr:`~enhydris.models.Timeseries.time_step` is a string.
      Some time series are completely irregular; in that case,
      :attr:`~enhydris.models.Timeseries.time_step` is empty. Otherwise,
      it contains an appropriate time step as a `pandas "frequency"
      string`_, e.g.  "10min", "H", "M", "Y".

   .. attribute:: enhydris.models.Timeseries.name

      A name for the time series. Very often this is not needed and can
      be left empty—the name of the time series group and the
      :attr:`type` and :attr:`time_step` of the time series suffice.
      Sometimes, however, there may be different time series with the
      same :attr:`type` and :attr:`time_step`; for example, an
      aggregated time series with the mean and another one with the max
      value.

   .. attribute:: enhydris.models.Timeseries.publicly_available

      Specifies whether anonymous users can download the time series
      data.

      .. _pandas "frequency" string: https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#dateoffset-objects

   .. method:: enhydris.models.Timeseries.get_data(start_date=None, end_date=None, timezone=None)

      Return the data of the time series in a HTimeseries_ object. If
      *start_date* or *end_date* are specified, only this part of the
      data is returned.

      The timestamps are converted to the specified timezone.  If
      unspecified, :attr:`~enhydris.models.Gentity.display_timezone` is
      used.

   .. method:: enhydris.models.Timeseries.set_data(data, default_timezone=None)

      Replace all of the time series with *data*, which must be one of
      the following:

       * A Pandas DataFrame
       * A HTimeseries_ object
       * A filelike object containing time series data in `text format`_
         or `file format`_.

       *default_timezone* is a string from the Olson time zone database. It
       specifies the time zone of the timestamps. If it is const:`None`, then
       *data* must specify a time zone; either it must be a HTimeseries_
       object or it must be a filelike object with time series data in
       `file format`_ containing a ``timezone`` header.

       If *default_timezone* is specified and *data* also specifies the time
       zone in one of these ways, *default_timezone* is ignored.

   .. method:: enhydris.models.Timeseries.append_data(data, default_timezone=None)

      Same as :meth:`~enhydris.models.Timeseries.set_data`, except that
      the data is appended to the already existing data. Raises
      ``ValueError`` if the new data is not more recent than the old
      data.

   .. method:: enhydris.models.Timeseries.get_last_record_as_string(timezone=None)

      Return the last record of the data file in CSV format, or an empty
      string if the time series contains no records. If ``timezone`` is
      specified, the date in the file is in that time zone, otherwise in the
      :attr:`enhydris.models.Station.default_timezone`.

.. class:: enhydris.models.TimeseriesRecord

   Stores time series records.

   .. attribute:: timeseries
      :type: ForeignKey

      A foreign key to :class:`~enhydris.models.Timeseries`.

   .. attribute:: timestamp
      :type: DateTimeField

      The time stamp of the record.

   .. attribute:: value
      :type: FloatField

      The value of the record.

   .. attribute:: flags
      :type: CharField

      Flags for the record.

   .. method:: bulk_insert(timeseries: object, htimeseries: object) -> int
      :classmethod:

      Inserts all records of ``htimeseries`` (a HTimeseries_ object) in
      :class:`~enhydris.models.TimeseriesRecord`. ``timeseries`` is the
      :class:`~enhydris.models.Timeseries` to which these records refer.

      Returns the number of records inserted (which should be the same
      as the number of records in of ``htimeseries``).

Autoprocess
-----------

``enhydris.autoprocess`` is an app that automatically processes time
series to produce new time series. For example, it performs range
checking, saving a new time series that is range checked.  The app is
installed by default. If you don't need it, remove it from
``INSTALLED_APPS``.  When it is installed, in the station page in the
admin, under "Timeseries Groups", there are some additional options,
like Range Check, Time Consistency Check, Curve Interpolations and
Aggregations.

You have a meteorological station called "Hobbiton". It measures
temperature. Because of sensor, transmission, or other errors,
sometimes the temperature is wrong—for example, 280 °C. What you want
to do (and what this app does, among other things) is delete these
measurements automatically as they come in. In this case, assuming
that the low and high all-time temperature records in Hobbiton are -18
and +38 °C, you might decide that anything below -25 or above +50 °C
(the "hard" limits) is an error, whereas anything below -20 or above
+40 °C (the "soft" limits) is a suspect value. In that case, you
configure ``enhydris.autoprocess`` with the soft and hard limits. Each
time data is uploaded, an event is triggered, resulting in an
asynchronous process processing the initial uploaded data, deleting the
values outside the hard limits, flagging as suspect the values outside
the soft limits, and saving the result to the "checked" time series of
the time series group.

(More specifically, ``enhydris.autoprocess`` uses the ``post_save``
Django signal for :class:`enhydris.Timeseries` to trigger a Celery task
that does the auto processing—see ``apps.py`` and ``tasks.py``.)

Range checking is only one of the ways in which a time series can be
auto-processed—there's also aggregation (e.g. deriving hourly from
ten-minute time series) and curve interpolation (e.g. deriving discharge
from stage, or estimating the air speed at a height of 2 m above ground
when the wind sensor is at a different height). The name we use for all
these together (i.e. checking, aggregation, interpolation) is "auto
process". Technically, :class:`AutoProcess` is the super class and it
has some subclasses such as :class:`Checks`, :class:`Aggregation` and
:class:`CurveInterpolation`. These are implemented using Django's
multi-table inheritance. (The checking subclass is called
:class:`Checks` because there can be many checks—range checking, time
consistency checking, etc; these are performed one after the other and
they result in the "checked" time series.)

.. class:: AutoProcess

   .. attribute:: timeseries_group

      The time series group to which this auto-process applies.

   .. method:: execute()

      Performs the auto-processing. It retrieves the new part of the
      source time series (i.e. the part that starts after the last date
      of the target time series) and calls the
      :meth:`process_timeseries` method.

   .. attribute:: source_timeseries

      This is a property; the source time series of the time series
      group for this auto-process. It depends on the kind of
      auto-process: for :class:`Checks` it is the initial time series;
      for :class:`Aggregation` and :class:`CurveInterpolation` it is the
      checked time series if it exists, or the initial otherwise.  If no
      suitable time series exists, it is created.

   .. attribute:: target_timeseries

      This is a property; the target time series of the time series
      group for this auto-process. It depends on the kind of
      auto-process: for :class:`Checks` it is the checked time series;
      for :class:`Aggregation` it is the aggregated time series with the
      target time step; for :class:`CurveInterpolation` it is the
      initial time series of the target time series group
      (:class:`CurveInterpolation` has an additional
      :attr:`target_timeseries_group` attribute). The target time series
      is created if it does not exist.

   .. method:: process_timeseries()

      Performs the actual processing.

.. _htimeseries: https://github.com/openmeteo/htimeseries
.. _text format: https://github.com/openmeteo/htimeseries#text-format
.. _file format: https://github.com/openmeteo/htimeseries#file-format
.. _multi-table inheritance: http://docs.djangoproject.com/en/dev/topics/db/models/#id6
.. _abstract base class: http://docs.djangoproject.com/en/dev/topics/db/models/#id5
.. _filefield: http://docs.djangoproject.com/en/dev/ref/models/fields/#filefield
.. _imagefield: http://docs.djangoproject.com/en/dev/ref/models/fields/#imagefield
