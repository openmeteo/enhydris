import datetime as dt
import textwrap
from io import StringIO

from django.conf import settings
from django.contrib.gis.geos import Point
from django.contrib.sites.models import Site

from model_bakery import baker

from enhydris.models import Station, Timeseries, TimeseriesGroup, Variable
from enhydris.synoptic.models import (
    SynopticGroup,
    SynopticGroupStation,
    SynopticTimeseriesGroup,
)


class TestData:
    def __init__(self):
        self._create_stations()
        self._create_synoptic_group()
        self._create_synoptic_group_stations()
        self._create_variables()
        self._create_timeseries_groups()
        self._create_synoptic_timeseries_groups()
        self._create_timeseries_data()

    def _create_stations(self):
        site_id = settings.SITE_ID
        if not Site.objects.filter(id=site_id).exists():
            baker.make(Site, id=site_id, domain="example.com", name="example.com")
        self.station_komboti = baker.make(
            Station,
            name="Komboti",
            geom=Point(x=21.06071, y=39.09518, srid=4326),
            display_timezone="Etc/GMT-2",
        )
        self.station_agios = baker.make(
            Station,
            name="Άγιος Αθανάσιος",
            geom=Point(x=20.87591, y=39.14904, srid=4326),
            display_timezone="Etc/GMT-2",
        )
        self.station_arta = baker.make(
            Station,
            name="Arta",
            geom=Point(x=20.97527, y=39.15104, srid=4326),
            display_timezone="Etc/GMT-2",
        )

    def _create_synoptic_group(self):
        self.sg1 = baker.make(
            SynopticGroup,
            slug="mygroup",
            fresh_time_limit=dt.timedelta(minutes=60),
            timezone="Etc/GMT-1",
        )

    def _create_synoptic_group_stations(self):
        self.sgs_komboti = baker.make(
            SynopticGroupStation,
            synoptic_group=self.sg1,
            station=self.station_komboti,
            order=1,
        )
        self.sgs_agios = baker.make(
            SynopticGroupStation,
            synoptic_group=self.sg1,
            station=self.station_agios,
            order=2,
        )

        # We fail to create synoptic time series for the following station, but we
        # have it in the group, to verify it will be ignored.
        self.sgs_arta = baker.make(
            SynopticGroupStation,
            synoptic_group=self.sg1,
            station=self.station_arta,
            order=3,
        )

    def _create_variables(self):
        self.var_rain = baker.make(Variable, descr="Rain")
        self.var_temperature = baker.make(Variable, descr="Temperature")
        self.var_wind_speed = baker.make(Variable, descr="Wind speed")
        self.var_wind_gust = baker.make(Variable, descr="Wind gust")

    def _create_timeseries_groups(self):
        self._create_timeseries_groups_for_komboti()
        self._create_timeseries_groups_for_agios()

    def _create_timeseries_groups_for_komboti(self):
        self.tsg_komboti_rain = baker.make(
            TimeseriesGroup,
            gentity=self.station_komboti,
            variable=self.var_rain,
            name="Rain",
            precision=0,
            unit_of_measurement__symbol="mm",
        )
        self.tsg_komboti_temperature = baker.make(
            TimeseriesGroup,
            gentity=self.station_komboti,
            variable=self.var_temperature,
            name="Air temperature",
            precision=0,
            unit_of_measurement__symbol="°C",
        )
        self.tsg_komboti_wind_speed = baker.make(
            TimeseriesGroup,
            gentity=self.station_komboti,
            variable=self.var_wind_speed,
            name="Wind speed",
            precision=1,
            unit_of_measurement__symbol="m/s",
        )
        self.tsg_komboti_wind_gust = baker.make(
            TimeseriesGroup,
            gentity=self.station_komboti,
            variable=self.var_wind_gust,
            name="Wind gust",
            precision=1,
            unit_of_measurement__symbol="m/s",
        )

    def _create_timeseries_groups_for_agios(self):
        self.tsg_agios_rain = baker.make(
            TimeseriesGroup,
            gentity=self.station_agios,
            variable=self.var_rain,
            name="Rain",
            precision=1,
            unit_of_measurement__symbol="mm",
        )
        self.tsg_agios_temperature = baker.make(
            TimeseriesGroup,
            gentity=self.station_agios,
            variable=self.var_temperature,
            name="Air temperature",
            precision=1,
            unit_of_measurement__symbol="°C",
        )
        self.tsg_agios_wind_speed = baker.make(
            TimeseriesGroup,
            gentity=self.station_agios,
            variable=self.var_wind_speed,
            name="Wind speed",
            precision=1,
            unit_of_measurement__symbol="m/s",
        )

    def _create_synoptic_timeseries_groups(self):
        self._create_synoptic_timeseries_groups_for_komboti()
        self._create_synoptic_timeseries_groups_for_agios()

    def _create_synoptic_timeseries_groups_for_komboti(self):
        self.stsg1_1 = baker.make(
            SynopticTimeseriesGroup,
            synoptic_group_station=self.sgs_komboti,
            timeseries_group=self.tsg_komboti_rain,
            order=1,
        )
        self.stsg1_2 = baker.make(
            SynopticTimeseriesGroup,
            synoptic_group_station=self.sgs_komboti,
            timeseries_group=self.tsg_komboti_temperature,
            order=2,
        )
        self.stsg1_3 = baker.make(
            SynopticTimeseriesGroup,
            synoptic_group_station=self.sgs_komboti,
            timeseries_group=self.tsg_komboti_wind_speed,
            title="Wind",
            subtitle="speed",
            order=3,
        )
        self.stsg1_4 = baker.make(
            SynopticTimeseriesGroup,
            synoptic_group_station=self.sgs_komboti,
            timeseries_group=self.tsg_komboti_wind_gust,
            title="Wind",
            subtitle="gust",
            group_with=self.stsg1_3,
            order=4,
        )

    def _create_synoptic_timeseries_groups_for_agios(self):
        self.stsg2_1 = baker.make(
            SynopticTimeseriesGroup,
            synoptic_group_station=self.sgs_agios,
            timeseries_group=self.tsg_agios_rain,
            order=1,
        )
        self.stsg2_2 = baker.make(
            SynopticTimeseriesGroup,
            synoptic_group_station=self.sgs_agios,
            timeseries_group=self.tsg_agios_temperature,
            order=2,
        )
        self.stsg2_3 = baker.make(
            SynopticTimeseriesGroup,
            synoptic_group_station=self.sgs_agios,
            timeseries_group=self.tsg_agios_wind_speed,
            order=3,
        )

    def _create_timeseries_data(self):
        self._create_timeseries_for_komboti_rain()
        self._create_timeseries_for_komboti_temperature()
        self._create_timeseries_for_komboti_wind_speed()
        self._create_timeseries_for_komboti_wind_gust()
        self._create_timeseries_for_agios_rain()
        self._create_timeseries_for_agios_temperature()
        self._create_timeseries_for_agios_wind_speed()

    def _create_timeseries_object(self, timeseries_group):
        baker.make(
            Timeseries, timeseries_group=timeseries_group, type=Timeseries.INITIAL
        )

    def _create_timeseries_for_komboti_rain(self):
        self._create_timeseries_object(self.tsg_komboti_rain)
        self.tsg_komboti_rain.default_timeseries.set_data(
            StringIO(
                textwrap.dedent(
                    """\
                    2015-10-22 15:00,0,
                    2015-10-22 15:10,0,
                    2015-10-22 15:20,0,
                    """
                )
            ),
            default_timezone="Etc/GMT-2",
        )

    def _create_timeseries_for_komboti_temperature(self):
        self._create_timeseries_object(self.tsg_komboti_temperature)
        self.tsg_komboti_temperature.default_timeseries.set_data(
            StringIO(
                textwrap.dedent(
                    """\
                    2015-10-22 15:00,15,
                    2015-10-22 15:10,16,
                    2015-10-22 15:20,17,
                    """
                )
            ),
            default_timezone="Etc/GMT-2",
        )

    def _create_timeseries_for_komboti_wind_speed(self):
        self._create_timeseries_object(self.tsg_komboti_wind_speed)
        self.tsg_komboti_wind_speed.default_timeseries.set_data(
            StringIO(
                textwrap.dedent(
                    """\
                    2015-10-22 15:00,2.9,
                    2015-10-22 15:10,3.2,
                    2015-10-22 15:20,3,
                    """
                )
            ),
            default_timezone="Etc/GMT-2",
        )

    def _create_timeseries_for_komboti_wind_gust(self):
        self._create_timeseries_object(self.tsg_komboti_wind_gust)
        self.tsg_komboti_wind_gust.default_timeseries.set_data(
            StringIO(
                textwrap.dedent(
                    """\
                    2015-10-22 15:00,3.7,
                    2015-10-22 15:10,4.5,
                    2015-10-22 15:20,4.1,
                    """
                )
            ),
            default_timezone="Etc/GMT-2",
        )

    def _create_timeseries_for_agios_rain(self):
        self._create_timeseries_object(self.tsg_agios_rain)
        self.tsg_agios_rain.default_timeseries.set_data(
            StringIO(
                textwrap.dedent(
                    """\
                    2015-10-22 15:00,0,
                    2015-10-23 15:10,0,
                    2015-10-23 15:20,0.2,
                    2015-10-23 15:30,1.4,
                    """
                )
            ),
            default_timezone="Etc/GMT-2",
        )

    def _create_timeseries_for_agios_temperature(self):
        self._create_timeseries_object(self.tsg_agios_temperature)
        self.tsg_agios_temperature.default_timeseries.set_data(
            StringIO(
                textwrap.dedent(
                    """\
                    2015-10-23 15:00,40,
                    2015-10-23 15:10,39,
                    2015-10-23 15:20,38.5,
                    """
                )
            ),
            default_timezone="Etc/GMT-2",
        )

    def _create_timeseries_for_agios_wind_speed(self):
        # We had this problem where a station was sending too many null values and was
        # resulting in a RuntimeError. The reason was that we were not running
        # set_xlim() to explicitly set the range of the horizontal axis of the chart.
        # If set_xlim() is not used, matplotlib sets it automatically, but if there are
        # null values at the beginning or end of the time series it doesn't set it as
        # we need, and later it had trouble when setting the ticks (the error was too
        # many ticks). So we add a time series full of nulls to test this case. It still
        # has the problem that in the report it shows "nan m/s" instead of something
        # more elegant, but we'll fix this another time.
        self._create_timeseries_object(self.tsg_agios_wind_speed)
        self.tsg_agios_wind_speed.default_timeseries.set_data(
            StringIO(
                textwrap.dedent(
                    """\
                    2015-10-23 15:00,,
                    2015-10-23 15:10,,
                    2015-10-23 15:20,,
                    """
                )
            ),
            default_timezone="Etc/GMT-2",
        )
