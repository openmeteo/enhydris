import datetime as dt
import textwrap

from django.test import TestCase

import numpy as np
import pandas as pd
from htimeseries import HTimeseries
from model_bakery import baker

from enhydris.autoprocess.models import CurveInterpolation, CurvePeriod, CurvePoint
from enhydris.models import Station, Timeseries, TimeseriesGroup
from enhydris.tests.test_models.test_timeseries import get_tzinfo


class CurveInterpolationTestCase(TestCase):
    def setUp(self):
        self.station = baker.make(Station)
        self.timeseries_group1 = baker.make(TimeseriesGroup, gentity=self.station)
        self.timeseries_group2 = baker.make(
            TimeseriesGroup, gentity=self.station, name="Group 2"
        )

    def test_create(self):
        curve_interpolation = CurveInterpolation(
            timeseries_group=self.timeseries_group1,
            target_timeseries_group=self.timeseries_group2,
        )
        curve_interpolation.save()
        self.assertEqual(CurveInterpolation.objects.count(), 1)

    def test_update(self):
        baker.make(CurveInterpolation, timeseries_group=self.timeseries_group1)
        curve_interpolation = CurveInterpolation.objects.first()
        curve_interpolation.timeseries_group = self.timeseries_group2
        curve_interpolation.save()
        self.assertEqual(
            curve_interpolation.timeseries_group.id, self.timeseries_group2.id
        )

    def test_delete(self):
        baker.make(CurveInterpolation, timeseries_group=self.timeseries_group1)
        curve_interpolation = CurveInterpolation.objects.first()
        curve_interpolation.delete()
        self.assertEqual(CurveInterpolation.objects.count(), 0)

    def test_str(self):
        curve_interpolation = baker.make(
            CurveInterpolation,
            timeseries_group=self.timeseries_group1,
            target_timeseries_group=self.timeseries_group2,
        )
        self.assertEqual(str(curve_interpolation), "=> Group 2")

    def test_no_extra_queries_for_str(self):
        baker.make(
            CurveInterpolation,
            timeseries_group=self.timeseries_group1,
            target_timeseries_group=self.timeseries_group2,
        )
        with self.assertNumQueries(1):
            str(CurveInterpolation.objects.first())

    def test_source_timeseries(self):
        self._make_timeseries(id=42, timeseries_group_num=1, type=Timeseries.INITIAL)
        self._make_timeseries(id=41, timeseries_group_num=2, type=Timeseries.INITIAL)
        ci = baker.make(
            CurveInterpolation,
            timeseries_group=self.timeseries_group1,
            target_timeseries_group=self.timeseries_group2,
        )
        self.assertEqual(ci.source_timeseries.id, 42)

    def _make_timeseries(self, id, timeseries_group_num, type):
        timeseries_group = getattr(self, f"timeseries_group{timeseries_group_num}")
        return baker.make(
            Timeseries, id=id, timeseries_group=timeseries_group, type=type
        )

    def test_automatically_creates_source_timeseries(self):
        ci = baker.make(
            CurveInterpolation,
            timeseries_group=self.timeseries_group1,
            target_timeseries_group=self.timeseries_group2,
        )
        self.assertFalse(Timeseries.objects.exists())
        ci.source_timeseries.id
        self.assertTrue(Timeseries.objects.exists())

    def test_target_timeseries(self):
        self._make_timeseries(id=42, timeseries_group_num=1, type=Timeseries.INITIAL)
        self._make_timeseries(id=41, timeseries_group_num=2, type=Timeseries.INITIAL)
        ci = baker.make(
            CurveInterpolation,
            timeseries_group=self.timeseries_group1,
            target_timeseries_group=self.timeseries_group2,
        )
        self.assertEqual(ci.target_timeseries.id, 41)

    def test_automatically_creates_target_timeseries(self):
        ci = baker.make(
            CurveInterpolation,
            timeseries_group=self.timeseries_group1,
            target_timeseries_group=self.timeseries_group2,
        )
        self.assertFalse(Timeseries.objects.exists())
        ci.target_timeseries.id
        self.assertTrue(Timeseries.objects.exists())


class CurvePeriodTestCase(TestCase):
    def test_create(self):
        curve_interpolation = baker.make(CurveInterpolation)
        curve_period = CurvePeriod(
            curve_interpolation=curve_interpolation,
            start_date=dt.date(2019, 9, 3),
            end_date=dt.date(2021, 9, 4),
        )
        curve_period.save()
        self.assertEqual(CurvePeriod.objects.count(), 1)

    def test_update(self):
        baker.make(CurvePeriod)
        curve_period = CurvePeriod.objects.first()
        curve_period.start_date = dt.date(1963, 1, 1)
        curve_period.end_date = dt.date(1963, 12, 1)
        curve_period.save()
        curve_period = CurvePeriod.objects.first()
        self.assertEqual(curve_period.start_date, dt.date(1963, 1, 1))

    def test_delete(self):
        baker.make(CurvePeriod)
        curve_period = CurvePeriod.objects.first()
        curve_period.delete()
        self.assertEqual(CurvePeriod.objects.count(), 0)

    def test_str(self):
        curve_period = baker.make(
            CurvePeriod,
            curve_interpolation__target_timeseries_group__name="Discharge",
            start_date=dt.date(2019, 9, 3),
            end_date=dt.date(2021, 9, 4),
        )
        self.assertEqual(str(curve_period), "=> Discharge: 2019-09-03 - 2021-09-04")

    def test_no_extra_queries_for_str(self):
        baker.make(
            CurvePeriod,
            curve_interpolation__target_timeseries_group__name="Discharge",
        )
        with self.assertNumQueries(1):
            str(CurvePeriod.objects.first())


class CurvePointTestCase(TestCase):
    def test_create(self):
        curve_period = baker.make(CurvePeriod)
        point = CurvePoint(curve_period=curve_period, x=2.718, y=3.141)
        point.save()
        self.assertEqual(CurvePoint.objects.count(), 1)

    def test_update(self):
        baker.make(CurvePoint)
        point = CurvePoint.objects.first()
        point.x = 2.718
        point.save()
        point = CurvePoint.objects.first()
        self.assertAlmostEqual(point.x, 2.718)

    def test_delete(self):
        baker.make(CurvePoint)
        point = CurvePoint.objects.first()
        point.delete()
        self.assertEqual(CurvePoint.objects.count(), 0)

    def test_str(self):
        point = baker.make(
            CurvePoint,
            curve_period__start_date=dt.date(2019, 9, 3),
            curve_period__end_date=dt.date(2021, 9, 4),
            curve_period__curve_interpolation__target_timeseries_group__name="pH",
            x=2.178,
            y=3.141,
        )
        self.assertEqual(
            str(point), "=> pH: 2019-09-03 - 2021-09-04: Point (2.178, 3.141)"
        )

    def test_no_extra_queries_for_str(self):
        baker.make(
            CurvePoint,
            curve_period__curve_interpolation__target_timeseries_group__name="pH",
        )
        with self.assertNumQueries(1):
            str(CurvePoint.objects.first())


class CurvePeriodSetCurveTestCase(TestCase):
    def setUp(self):
        self.period = baker.make(
            CurvePeriod, start_date=dt.date(2019, 9, 3), end_date=dt.date(2021, 9, 4)
        )
        point = CurvePoint(curve_period=self.period, x=2.718, y=3.141)
        point.save()

    def test_set_curve(self):
        csv = textwrap.dedent(
            """\
            5,6
            7\t8
            9,10
            """
        )
        self.period.set_curve(csv)
        points = CurvePoint.objects.filter(curve_period=self.period).order_by("x")
        self.assertAlmostEqual(points[0].x, 5)
        self.assertAlmostEqual(points[0].y, 6)
        self.assertAlmostEqual(points[1].x, 7)
        self.assertAlmostEqual(points[1].y, 8)
        self.assertAlmostEqual(points[2].x, 9)
        self.assertAlmostEqual(points[2].y, 10)


class CurveInterpolationProcessTimeseriesTestCase(TestCase):
    _index = [
        dt.datetime(2019, 4, 30, 12, 10, tzinfo=get_tzinfo("Etc/GMT-2")),
        dt.datetime(2019, 5, 21, 10, 20, tzinfo=get_tzinfo("Etc/GMT-2")),
        dt.datetime(2019, 5, 21, 10, 30, tzinfo=get_tzinfo("Etc/GMT-2")),
        dt.datetime(2019, 5, 21, 10, 40, tzinfo=get_tzinfo("Etc/GMT-2")),
        dt.datetime(2019, 6, 21, 10, 50, tzinfo=get_tzinfo("Etc/GMT-2")),
        dt.datetime(2019, 6, 21, 11, 00, tzinfo=get_tzinfo("Etc/GMT-2")),
        dt.datetime(2019, 6, 21, 11, 10, tzinfo=get_tzinfo("Etc/GMT-2")),
        dt.datetime(2019, 7, 21, 12, 10, tzinfo=get_tzinfo("Etc/GMT-2")),
    ]

    source_timeseries = pd.DataFrame(
        data={
            "value": [3.1, 2.9, 3.1, np.nan, 3.1, 4.9, 7.2, 3.1],
            "flags": ["", "", "", "", "", "FLAG1", "FLAG2", ""],
        },
        columns=["value", "flags"],
        index=_index,
    )

    expected_result = pd.DataFrame(
        data={
            "value": [
                np.nan,  # Because date < startdate (2019-04-30 < 2019-05-01)
                np.nan,  # Because x < x0 (2.9 < 3)
                105,
                np.nan,  # Because x = nan
                210,
                345,
                np.nan,  # Because x > xn (7.2 > 5)
                np.nan,  # Because date > enddate (2019-07-21 > 2019-06-30)
            ],
            "flags": ["", "", "", "", "", "", "", ""],
        },
        columns=["value", "flags"],
        index=_index,
    )

    def test_execute(self):
        station = baker.make(Station)
        self.curve_interpolation = baker.make(
            CurveInterpolation,
            timeseries_group__gentity=station,
            target_timeseries_group__gentity=station,
        )
        self._setup_period1()
        self._setup_period2()
        self.curve_interpolation._htimeseries = HTimeseries(self.source_timeseries)
        result = self.curve_interpolation.process_timeseries()
        pd.testing.assert_frame_equal(result, self.expected_result)

    def _setup_period1(self):
        period1 = self._make_period(dt.date(2019, 5, 1), dt.date(2019, 5, 31))
        baker.make(CurvePoint, curve_period=period1, x=3, y=100)
        baker.make(CurvePoint, curve_period=period1, x=4, y=150)
        baker.make(CurvePoint, curve_period=period1, x=5, y=175)

    def _setup_period2(self):
        period1 = self._make_period(dt.date(2019, 6, 1), dt.date(2019, 6, 30))
        baker.make(CurvePoint, curve_period=period1, x=3, y=200)
        baker.make(CurvePoint, curve_period=period1, x=4, y=300)
        baker.make(CurvePoint, curve_period=period1, x=5, y=350)

    def _make_period(self, start_date, end_date):
        return baker.make(
            CurvePeriod,
            curve_interpolation=self.curve_interpolation,
            start_date=start_date,
            end_date=end_date,
        )
