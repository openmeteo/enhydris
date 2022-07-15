.. _telemetry:

=========
Telemetry
=========

Models
------

.. class:: enhydris.telemetry.models.Telemetry

   Information about how to automatically fetch data.

   :class:`~enhydris.telemetry.models.Telemetry` has a OneToOneField to
   :class:`~enhydris.models.Station`. Every minute Celery Beat runs a
   task that iterates through the records of
   :class:`~enhydris.telemetry.models.Telemetry`; for each record, if
   the time for fetching data has arrived, it fetches the data by
   calling the :meth:`~enhydris.telemetry.models.Telemetry.fetch`
   method.

   :class:`~enhydris.telemetry.models.Telemetry` objects have the
   following attributes, properties and methods:

   .. attribute:: station
      :type: OneToOneField

      The :class:`~enhydris.models.Station` to which the record refers.

   .. attribute:: type
      :type: CharField

      The type of the API, such as ``Adcon AddUPI`` or ``Metrica
      MeteoView2``.  See :ref:`telemetry_api_types` for more
      information.

   .. attribute:: data_time_zone
      :type: CharField

      Enhydris has the requirement that all time stamps in
      :class:`~enhydris.models.TimeseriesRecord` must be stored in the
      same offset from UTC, i.e. without switching to Daylight Saving
      Time (DST). This offset is specified by
      :attr:`enhydris.models.TimeseriesGroup.time_zone`.

      It is recommended that data loggers also do not switch to DST.
      However, if they do, Enhydris can convert their time stamps as
      needed. If, for example,
      :attr:`~enhydris.telemetry.models.Telemetry.data_time_zone` is set
      to ``Europe/Athens``, then any DST offset will be removed before
      storing in :class:`~enhydris.models.TimeseriesRecord`.

      :attr:`~enhydris.telemetry.models.Telemetry.data_time_zone` is
      used only in order to know when the DST switches occur. The
      timestamp, after removing any DST, is entered as is. There is no
      conversion from
      :attr:`~enhydris.telemetry.models.Telemetry.data_time_zone` to
      :attr:`enhydris.models.TimeseriesGroup.time_zone`. Therefore,
      whether
      :attr:`~enhydris.telemetry.models.Telemetry.data_time_zone` is
      ``Europe/Athens`` or ``Europe/Berlin``, the effect will be exactly
      the same, since Athens and Berlin (as of 2021) switch to DST in
      exactly the same dates.

      Enhydris assumes that the time change occurs exactly when it is
      supposed to occur, not a few hours earlier or later. For the
      switch towards DST, things are simple. For the switch from DST to
      winter time, things are more complicated, because there's an hour
      that appears twice.  If the ambiguous hour occurs twice, Enhydris
      will usually do the correct thing; it will consider that the
      second occurence is after the switch and the first is before the
      switch. If according to the system's clock the switch hasn't
      occurred yet, any references to the ambiguous hour are considered
      to have occurred before the switch.

   .. attribute:: fetch_interval_minutes
      :type: PositiveSmallIntegerField

      This can be, e.g., 60 to fetch data every 60 minutes, 1440 to
      fetch data once a day, etc.

   .. attribute:: fetch_offset_minutes
      :type: PositiveSmallIntegerField

      If
      :attr:`~enhydris.telemetry.models.Telemetry.fetch_interval_minutes`
      is 10 and
      :attr:`~enhydris.telemetry.models.Telemetry.fetch_offset_minutes`
      is 2, then data will be fetched at :02, :12, :22, etc.  If
      :attr:`~enhydris.telemetry.models.Telemetry.fetch_interval_minutes`
      is 1440 and
      :attr:`~enhydris.telemetry.models.Telemetry.fetch_offset_minutes`
      is 125, then data will be fetched every day at 02:05 in the
      morning. Generally
      :attr:`~enhydris.telemetry.models.Telemetry.fetch_offset_minutes`
      counts from midnight.

   .. attribute:: fetch_offset_time_zone
      :type: CharField

      The time zone to which
      :attr:`~enhydris.telemetry.models.Telemetry.fetch_offset_minutes`
      refers; a `tz database name`_ such as ``Europe/Athens``.

      .. _tz database name: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

   .. attribute:: configuration
      :type: JSONField

      Any additional configuration. The exact contents depend on the API
      :attr:`~enhydris.telemetry.models.Telemetry.type`. However,
      :attr:`configuration` contains (among other things) a
      ``timeseries`` key, which is a list. See
      :attr:`Telemetry.wizard_steps` for more information.

   .. property:: is_due
      :type: Boolean

      :const:`True` if according to
      :attr:`~enhydris.telemetry.models.Telemetry.fetch_interval_minutes`,
      :attr:`~enhydris.telemetry.models.Telemetry.fetch_offset_minutes`,
      :attr:`~enhydris.telemetry.models.Telemetry.fetch_offset_time_zone`
      and the current system time it's time to fetch data.

   .. method:: fetch() -> None

      Connects to the API, fetches the data, and inserts them to
      :class:`~enhydris.models.TimeseriesRecord`. Essentially this
      merely calls :meth:`Telemetry.fetch`.

.. _telemetry_api_types:

Telemetry API types
-------------------

Each API type is one Python file in the
:file:`enhydris/telemetry/types` directory.  The Python file must
contain a :class:`Telemetry` class with all required functionality to
retrieve data from the API.

When it starts, Enhydris scans the :file:`enhydris/telemetry/types`
directory and imports all Python files it contains.  The result of this
scanning goes to :data:`enhydris.telemetry.drivers`.

.. data:: enhydris.telemetry.drivers

   A dictionary that contains all :class:`Telemetry` classes imported
   from the :file:`enhydris/telemetry/types` directory. Each dictionary
   item maps the telemetry type's slug (the base name of the Python
   file) to the :class:`Telemetry` class.

.. class:: Telemetry(telemetry_model)

   Should inherit from :class:`enhydris.telemetry.TelemetryBase`. The
   base class :func:`__init__` method initializes the object with a
   :class:`enhydris.telemetry.models.Telemetry` object, which becomes
   the :attr:`telemetry_model` attribute.

   :class:`Telemetry` classes must define the following attributes,
   methods and properties:

   .. attribute:: name
      :type: string

      The name of the API, such as ``Adcon AddUPI`` or ``Metrica
      MeteoView2``. This is what is stored in
      :attr:`enhydris.telemetry.models.Telemetry.type`.

   .. attribute:: wizard_steps
      :type: list

      When the user wants to configure telemetry for a station, we show
      him a wizard. The first step essentially asks what type of
      telemetric system there is for the station at hand, i.e. asks the
      user to select a value for
      :attr:`enhydris.telemetry.models.Telemetry.type`.  The wizard then
      continues with steps that are specific to the chosen telemetry
      type.  :attr:`wizard_steps`, a class attribute, is a list of
      :class:`django.forms.Form` subclasses, containing the forms for
      these steps. These forms are instantiated with the configuration
      specified so far as their ``initial`` parameter, and the
      configuration is updated with the ``cleaned_data`` once the form
      is posted.

   .. method:: fetch() -> None

      Connects to the API, fetches the data, and inserts them to
      :class:`~enhydris.models.TimeseriesRecord`.
