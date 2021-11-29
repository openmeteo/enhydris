import datetime as dt
from io import StringIO

from django.contrib.gis.geos import Point

import pandas as pd
from htimeseries import HTimeseries
from model_mommy import mommy
from parler.utils.context import switch_language

from enhydris import models


class TestTimeseriesMixin:
    @classmethod
    def _create_test_timeseries(cls, data=""):
        cls.station = mommy.make(
            models.Station,
            name="Celduin",
            original_srid=2100,
            geom=Point(x=21.06071, y=39.09518, srid=4326),
            altitude=219,
        )
        cls.timeseries_group = mommy.make(
            models.TimeseriesGroup,
            name="Daily temperature",
            gentity=cls.station,
            unit_of_measurement__symbol="mm",
            time_zone__code="IST",
            time_zone__utc_offset=330,
            variable__descr="Temperature",
            precision=1,
            remarks="This timeseries group rocks",
        )
        cls.timeseries = mommy.make(
            models.Timeseries,
            timeseries_group=cls.timeseries_group,
            type=models.Timeseries.INITIAL,
            time_step="H",
        )
        cls.timeseries.set_data(StringIO(data))


class TimeseriesDataMixin:
    def create_timeseries(self):
        self.htimeseries = HTimeseries()
        self.htimeseries.data = pd.DataFrame(
            index=[dt.datetime(2017, 11, 23, 17, 23), dt.datetime(2018, 11, 25, 1, 0)],
            data={"value": [1.0, 2.0], "flags": ["", ""]},
            columns=["value", "flags"],
        )
        self.station = mommy.make(
            models.Station,
            name="Komboti",
            geom=Point(x=21.00000, y=39.00000, srid=4326),
            original_srid=4326,
        )
        self.time_zone = mommy.make(models.TimeZone, code="EET", utc_offset=120)
        self.variable = models.Variable()
        with switch_language(self.variable, "en"):
            self.variable.descr = "Beauty"
            self.variable.save()
        self.timeseries_group = mommy.make(
            models.TimeseriesGroup,
            gentity=self.station,
            time_zone=self.time_zone,
            precision=2,
            variable=self.variable,
            unit_of_measurement__symbol="beauton",
        )
        self.timeseries = mommy.make(
            models.Timeseries,
            type=models.Timeseries.INITIAL,
            timeseries_group=self.timeseries_group,
        )
        self.timeseries.set_data(self.htimeseries.data)
