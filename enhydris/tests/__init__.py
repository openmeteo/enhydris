import datetime as dt

from django.contrib.gis.geos import Point

import pandas as pd
from htimeseries import HTimeseries
from model_mommy import mommy
from parler.utils.context import switch_language

from enhydris import models


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
            id=20,
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
            id=31,
            gentity=self.station,
            time_zone=self.time_zone,
            precision=2,
            variable=self.variable,
        )
        self.timeseries = mommy.make(
            models.Timeseries,
            id=42,
            type=models.Timeseries.RAW,
            timeseries_group=self.timeseries_group,
        )
        self.timeseries.set_data(self.htimeseries.data)
