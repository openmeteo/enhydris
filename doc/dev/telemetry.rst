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

   .. attribute:: device_locator
      :type: string

      The address of the remote API. Depending on the API, this may be
      the IP address, host name, or URL of the data collection device.
      Some APIs don't have it at all, as the API is served by a given
      location regardless of which station it is (e.g.
      TheThingsNetwork). In such cases the attribute is left blank.

   .. attribute:: username
                  password
      :type: string

      The username and password with which Enhydris will log on to the
      remote API. The password might actually be an API key, and the
      username might be an email, or it could be absent.

   .. attribute:: remote_station_id
      :type: string

      If the API supports a single station (for that user), this should
      be blank. Some APIs provide access to many different stations;
      in that case, this is the id with which the station can be
      identified on the API (i.e. the :attr:`remote_station_id` on the
      API corresponds to the :attr:`station` of Enhydris).

   .. attribute:: additional_config
      :type: JSONField

      If the specific telemetry type needs any additional configuration
      (e.g. serial interface parameters), it is stored in this
      attribute.

   .. property:: is_due
      :type: Boolean

      :const:`True` if according to
      :attr:`~enhydris.telemetry.models.Telemetry.fetch_interval_minutes`,
      :attr:`~enhydris.telemetry.models.Telemetry.fetch_offset_minutes`,
      :attr:`~enhydris.telemetry.models.Telemetry.fetch_offset_time_zone`
      and the current system time it's time to fetch data.

   .. method:: fetch() -> None

      Connects to the API, fetches the data, and inserts them to
      :class:`~enhydris.models.TimeseriesRecord`.

.. class:: enhydris.telemetry.models.Sensor

   Each record in that model represents a sensor in the API, and also
   holds the time series group to which the sensor corresponds, i.e. the
   time series group to which the data from the sensor are to be
   uploaded. If a sensor is to be ignored, then no row must exist in
   this table.

   .. attribute:: telemetry
      :type: ForeignKey

      A foreign key to :class:`~enhydris.telemetry.models.Telemetry`.

   .. attribute:: sensor_id
      :type: string

      An id with which the sensor can be identified in the API.

   .. attribute:: timeseries_group_id
      :type: string

      A foreign key to :class:`~enhydris.models.TimeseriesGroup`.


.. _telemetry_api_types:

Telemetry API types
-------------------

Each API type is one Python file in the
:file:`enhydris/telemetry/types` directory.  The Python file must
contain a :class:`TelemetryAPIClient` class with all required
functionality to retrieve data from the API.

When it starts, Enhydris scans the :file:`enhydris/telemetry/types`
directory and imports all Python files it contains.  The result of this
scanning goes to :data:`enhydris.telemetry.drivers`.

.. data:: enhydris.telemetry.drivers

   A dictionary that contains all :class:`TelemetryAPIClient` classes
   imported from the :file:`enhydris/telemetry/types` directory. Each
   dictionary item maps the telemetry type's slug (the base name of the
   Python file) to the :class:`TelemetryAPIClient` class.

.. class:: TelemetryAPIClient(telemetry)

   Should inherit from
   :class:`enhydris.telemetry.TelemetryAPIClientBase`. The base class
   :func:`__init__` method initializes the object with a
   :class:`~enhydris.telemetry.models.Telemetry` object, which becomes
   the :attr:`telemetry` attribute.

   :class:`TelemetryAPIClient` classes must define the following attributes,
   methods and properties:

   .. attribute:: name
      :type: string

      The name of the API, such as ``Adcon AddUPI`` or ``Metrica
      MeteoView2``. This is what is stored in
      :attr:`enhydris.telemetry.models.Telemetry.type`.

   .. attribute:: device_locator_label
                  device_locator_help_text
      :type: string

      The label and help that appears in the wizard for
      :attr:`~enhydris.telemetry.models.Telemetry.device_locator` when
      the user is configuring telemetry; if absent, "Device URL" is
      used for the label and nothing is shown as help.

   .. attribute:: username_label
      :type: string

      The label that appears in the wizard for
      :attr:`~enhydris.telemetry.models.Telemetry.username` when the
      user is configuring telemetry; if absent, "Username" is used. For
      example, it can be "Email".

   .. attribute:: password_label
      :type: string

      The string that appears in the wizard for
      :attr:`~enhydris.telemetry.models.Telemetry.password` when the
      user is configuring telemetry; if absent, "Password" is used. For
      example, it can be "API key".

   .. attribute:: hide_device_locator
      :type: boolean

      The default is :const:`False`. Set it to :const:`True` if that
      particular driver shouldn't show the device locator (i.e. the URL
      or hostname or IP address of the device) in the connection data
      form. This is useful for APIs that are served from a well-known
      location for all stations, such as Metrica MeteoView2 or
      TheThingsNetwork.

   .. method:: connect() -> None

      Initiates connection to the API and logs on. Should raise
      :class:`TelemetryError` if something goes wrong.

   .. method:: get_stations() -> dict

      Retrieves and returns pairs of station ids and station names from
      the API.  When the telemetry configuration wizard is shown to the
      user, at some point the user is asked which of the stations
      offered by the API corresponds to the Enhydris station; the
      stations offered by the API is what is returned by this method. If
      the API offers a single station, this method can be omitted (the
      base method returns :const:`None`).

      The station id is what is stored in
      :attr:`~enhydris.telemetry.models.Telemetry.remote_station_id`;
      the station name is what is shown to the user in the wizard.

      The method must raise :class:`TelemetryError` if something goes
      wrong.

   .. method:: get_sensors() -> dict

      Retrieves and returns pairs of sensor ids and sensor names from
      the API.  When the telemetry configuration wizard is shown to the
      user, at some point the user is asked which Enhydris time series
      group corresponds to each sensor of the API; the sensors available
      on the API is what is returned by this method.

      The sensor id is what is stored in
      :attr:`~enhydris.telemetry.models.Sensor.sensor_id`; the sensor
      name is what is shown to the user in the wizard.

      The method must raise :class:`TelemetryError` if something goes
      wrong.

   .. method:: get_measurements(sensor_id, enhydris_timeseries_end_date) -> StringIO

      Reads data records for the sensor specified, starting with the
      first record whose timestamp is greater than
      ``enhydris_timeseries_end_date``, and returns them in `text
      format`_.

      ``enhydris_timeseries_end_date`` is either None (meaning get all
      measurements since the beginning) or a naive datetime.

      In order to avoid loading the server too much, this should not
      return more than a reasonable number of records, such as half a
      year or 20000 records. In the initial uploading of a backlog of
      records, it will thus take a few successive data fetches to bring
      the Enhydris time series up to date, but this is usually not a
      problem.

      Enhydris can't currently handle more than one records with
      timestamps within the same minute. However it's OK for this method
      to return such records; the caller will ignore all except for the
      first one.

      The method must raise :class:`TelemetryError` if something goes
      wrong.

      .. _text format: https://github.com/openmeteo/htimeseries/#text-format

Exceptions
----------

.. class:: enhydris.telemetry.TelemetryError

   Telemetry API clients raise this exception if something goes wrong when
   connecting to the API. It derives from :class:`OSError`.
