import datetime as dt

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from bs4 import BeautifulSoup
from model_bakery import baker

import enhydris.models
from enhydris.autoprocess import models
from enhydris.autoprocess.admin import AggregationForm, CurvePeriodForm
from enhydris.tests import ClearCacheMixin
from enhydris.tests.admin import get_formset_parameters

User = get_user_model()


class TestCaseBase(ClearCacheMixin, TestCase):
    @classmethod
    def _create_data(cls):
        cls.user = User.objects.create_user(
            username="alice",
            password="topsecret",
            is_active=True,
            is_staff=True,
            is_superuser=False,
        )
        cls.organization = enhydris.models.Organization.objects.create(
            name="Serial killers SA"
        )
        cls.variable = baker.make(enhydris.models.Variable, descr="myvar")
        cls.unit = baker.make(enhydris.models.UnitOfMeasurement)
        cls.station = baker.make(
            enhydris.models.Station, creator=cls.user, owner=cls.organization
        )

    def setUp(self):
        self.client.login(username="alice", password="topsecret")

    def _post_form(self, data):
        return self.client.post(
            f"/admin/enhydris/station/{self.station.id}/change/", data
        )

    def _get_form(self):
        return self.client.get(f"/admin/enhydris/station/{self.station.id}/change/")


class TimeseriesGroupFormTestCaseBase(TestCaseBase):
    def _get_basic_form_contents(self):
        return {
            "name": "Hobbiton",
            "copyright_years": "2018",
            "copyright_holder": "Bilbo Baggins",
            "owner": self.organization.id,
            "geom_0": "20.94565",
            "geom_1": "39.12102",
            "display_timezone": "Etc/GMT-2",
            **get_formset_parameters(
                self.client, f"/admin/enhydris/station/{self.station.id}/change/"
            ),
            "timeseriesgroup_set-TOTAL_FORMS": "1",
            "timeseriesgroup_set-INITIAL_FORMS": "0",
            "timeseriesgroup_set-0-variable": self.variable.id,
            "timeseriesgroup_set-0-unit_of_measurement": self.unit.id,
            "timeseriesgroup_set-0-precision": 2,
            "timeseriesgroup_set-0-timeseries_set-INITIAL_FORMS": "0",
        }

    @classmethod
    def _ensure_we_have_timeseries_group(cls):
        if not hasattr(cls, "timeseries_group"):
            cls.timeseries_group = baker.make(
                enhydris.models.TimeseriesGroup,
                variable=cls.variable,
                gentity=cls.station,
            )

    @classmethod
    def _ensure_we_have_checks(cls):
        cls._ensure_we_have_timeseries_group()
        if not hasattr(cls, "checks"):
            cls.checks = baker.make(
                models.Checks, timeseries_group=cls.timeseries_group
            )

    @classmethod
    def _create_range_check(cls):
        cls._ensure_we_have_checks()
        cls.range_check = baker.make(
            models.RangeCheck,
            checks=cls.checks,
            lower_bound=1,
            soft_lower_bound=2,
            soft_upper_bound=3,
            upper_bound=4,
        )

    @classmethod
    def _create_roc_check(cls):
        cls._ensure_we_have_checks()
        cls.roc_check = baker.make(
            models.RateOfChangeCheck, checks=cls.checks, symmetric=True
        )
        cls.roc_check.set_thresholds("10min\t25.0\n1h\t35.0\n")


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class TimeseriesGroupFormRangeCheckValidationTestCase(TimeseriesGroupFormTestCaseBase):
    @classmethod
    def setUpTestData(cls):
        cls._create_data()

    def setUp(self):
        super().setUp()
        self.data = self._get_basic_form_contents()

    def test_returns_error_if_only_upper_bound_is_specified(self):
        data = {**self.data, "timeseriesgroup_set-0-upper_bound": 420}
        response = self._post_form(data)
        self.assertContains(response, "lower and upper bound must be specified")

    def test_returns_error_if_only_lower_bound_is_specified(self):
        data = {**self.data, "timeseriesgroup_set-0-lower_bound": 42}
        response = self._post_form(data)
        self.assertContains(response, "lower and upper bound must be specified")

    def test_succeeds_if_no_bounds_are_specified(self):
        data = self.data
        response = self._post_form(data)
        self.assertEqual(response.status_code, 302)

    def test_succeeds_if_both_upper_and_lower_bounds_are_specified(self):
        data = {
            **self.data,
            "timeseriesgroup_set-0-upper_bound": 420,
            "timeseriesgroup_set-0-lower_bound": 0,
        }
        response = self._post_form(data)
        self.assertEqual(response.status_code, 302)


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class TimeseriesGroupFormCreatesRangeCheckTestCase(TimeseriesGroupFormTestCaseBase):
    @classmethod
    def setUpTestData(cls):
        cls._create_data()

    def setUp(self):
        super().setUp()
        self._get_response()
        self.range_check = models.RangeCheck.objects.first()

    def _get_response(self):
        data = {
            **self._get_basic_form_contents(),
            "timeseriesgroup_set-0-lower_bound": 42,
            "timeseriesgroup_set-0-soft_lower_bound": 84,
            "timeseriesgroup_set-0-soft_upper_bound": 168,
            "timeseriesgroup_set-0-upper_bound": 420,
        }
        response = self._post_form(data)
        assert response.status_code == 302

    def test_lower_bound(self):
        self.assertEqual(self.range_check.lower_bound, 42)

    def test_soft_lower_bound(self):
        self.assertEqual(self.range_check.soft_lower_bound, 84)

    def test_soft_upper_bound(self):
        self.assertEqual(self.range_check.soft_upper_bound, 168)

    def test_upper_bound(self):
        self.assertEqual(self.range_check.upper_bound, 420)


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class TimeseriesGroupFormSavesExistingRangeCheckTestCase(
    TimeseriesGroupFormCreatesRangeCheckTestCase
):
    @classmethod
    def setUpTestData(cls):
        cls._create_data()
        cls._create_range_check()

    def setUp(self):
        super().setUp()
        self._get_response()
        range_checks = models.RangeCheck.objects.all()
        assert range_checks.count() == 1
        self.range_check = range_checks[0]

    def _get_response(self):
        data = {
            **self._get_basic_form_contents(),
            "timeseriesgroup_set-0-id": self.timeseries_group.id,
            "timeseriesgroup_set-0-gentity": self.station.id,
            "timeseriesgroup_set-0-lower_bound": 42,
            "timeseriesgroup_set-0-soft_lower_bound": 84,
            "timeseriesgroup_set-0-soft_upper_bound": 168,
            "timeseriesgroup_set-0-upper_bound": 420,
        }
        response = self._post_form(data)
        assert response.status_code == 302


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class TimeseriesGroupFormDeletesRangeCheckTestCase(TimeseriesGroupFormTestCaseBase):
    @classmethod
    def setUpTestData(cls):
        cls._create_data()
        cls._create_range_check()
        cls._create_roc_check()  # This is to ensure it won't be deleted

    def setUp(self):
        super().setUp()
        assert models.RangeCheck.objects.count() == 1
        assert models.Checks.objects.count() == 1
        self._get_response()

    def _get_response(self):
        data = {
            **self._get_basic_form_contents(),
            "timeseriesgroup_set-0-id": self.timeseries_group.id,
            "timeseriesgroup_set-0-gentity": self.station.id,
            "timeseriesgroup_set-0-lower_bound": "",
            "timeseriesgroup_set-0-soft_lower_bound": "",
            "timeseriesgroup_set-0-soft_upper_bound": "",
            "timeseriesgroup_set-0-upper_bound": "",
        }
        response = self._post_form(data)
        assert response.status_code == 302

    def test_range_check_has_been_deleted(self):
        self.assertEqual(models.RangeCheck.objects.count(), 0)


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class TimeseriesGroupFormRangeCheckInitialValuesTestCase(
    TimeseriesGroupFormTestCaseBase
):
    @classmethod
    def setUpTestData(cls):
        cls._create_data()
        cls._create_range_check()

    def setUp(self):
        super().setUp()
        self.response = self._get_form()
        self.soup = BeautifulSoup(self.response.content, "html.parser")

    def test_lower_bound(self):
        value = self.soup.find(id="id_timeseriesgroup_set-0-lower_bound")["value"]
        self.assertEqual(value, "1.0")

    def test_soft_lower_bound(self):
        value = self.soup.find(id="id_timeseriesgroup_set-0-soft_lower_bound")["value"]
        self.assertEqual(value, "2.0")

    def test_soft_upper_bound(self):
        value = self.soup.find(id="id_timeseriesgroup_set-0-soft_upper_bound")["value"]
        self.assertEqual(value, "3.0")

    def test_upper_bound(self):
        value = self.soup.find(id="id_timeseriesgroup_set-0-upper_bound")["value"]
        self.assertEqual(value, "4.0")


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class TimeseriesGroupFormRocCheckValidationTestCase(TimeseriesGroupFormTestCaseBase):
    @classmethod
    def setUpTestData(cls):
        cls._create_data()

    def setUp(self):
        super().setUp()
        self.data = self._get_basic_form_contents()

    def test_returns_error_if_thresholds_is_garbage(self):
        data = {**self.data, "timeseriesgroup_set-0-rocc_thresholds": "garbage"}
        response = self._post_form(data)
        self.assertContains(response, "is not a valid (delta_t, allowed_diff) pair")

    def test_succeeds_if_thresholds_is_ok(self):
        data = {**self.data, "timeseriesgroup_set-0-rocc_thresholds": "10min 25.0"}
        response = self._post_form(data)
        self.assertEqual(response.status_code, 302)

    def test_succeeds_if_thresholds_is_unspecified(self):
        data = {**self.data, "timeseriesgroup_set-0-rocc_thresholds": ""}
        response = self._post_form(data)
        self.assertEqual(response.status_code, 302)


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class TimeseriesGroupFormCreatesRocCheckTestCase(TimeseriesGroupFormTestCaseBase):
    @classmethod
    def setUpTestData(cls):
        cls._create_data()

    def setUp(self):
        super().setUp()
        self._get_response()
        self.roc_check = models.RateOfChangeCheck.objects.first()

    def _get_response(self):
        data = {
            **self._get_basic_form_contents(),
            "timeseriesgroup_set-0-rocc_symmetric": True,
            "timeseriesgroup_set-0-rocc_thresholds": "10min 25.0\n1h 35",
        }
        response = self._post_form(data)
        assert response.status_code == 302

    def test_thresholds(self):
        self.assertEqual(
            self.roc_check.get_thresholds_as_text(),
            "10min\t25.0\n1h\t35.0\n",
        )


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class TimeseriesGroupFormSavesExistingRocCheckTestCase(
    TimeseriesGroupFormCreatesRocCheckTestCase
):
    @classmethod
    def setUpTestData(cls):
        cls._create_data()
        cls._create_roc_check()

    def setUp(self):
        super().setUp()
        self._get_response()
        roc_checks = models.RateOfChangeCheck.objects.all()
        assert roc_checks.count() == 1
        self.roc_check = roc_checks[0]

    def _get_response(self):
        data = {
            **self._get_basic_form_contents(),
            "timeseriesgroup_set-0-id": self.timeseries_group.id,
            "timeseriesgroup_set-0-gentity": self.station.id,
            "timeseriesgroup_set-0-rocc_symmetric": True,
            "timeseriesgroup_set-0-rocc_thresholds": "10min 25.0\n1h 35",
        }
        response = self._post_form(data)
        assert response.status_code == 302


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class TimeseriesGroupFormDeletesRocCheckTestCase(TimeseriesGroupFormTestCaseBase):
    @classmethod
    def setUpTestData(cls):
        cls._create_data()
        cls._create_roc_check()
        cls._create_range_check()  # This is to ensure it's not deleted

    def setUp(self):
        super().setUp()
        assert models.RateOfChangeCheck.objects.count() == 1
        assert models.Checks.objects.count() == 1
        self._get_response()

    def _get_response(self):
        data = {
            **self._get_basic_form_contents(),
            "timeseriesgroup_set-0-id": self.timeseries_group.id,
            "timeseriesgroup_set-0-gentity": self.station.id,
            "timeseriesgroup_set-0-lower_bound": "3",
            "timeseriesgroup_set-0-soft_lower_bound": "4",
            "timeseriesgroup_set-0-soft_upper_bound": "5",
            "timeseriesgroup_set-0-upper_bound": "6",
            "timeseriesgroup_set-0-rocc_symmetric": True,
            "timeseriesgroup_set-0-rocc_thresholds": "",
        }
        response = self._post_form(data)
        assert response.status_code == 302

    def test_roc_check_has_been_deleted(self):
        self.assertEqual(models.RateOfChangeCheck.objects.count(), 0)


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class TimeseriesGroupFormRocCheckInitialValuesTestCase(TimeseriesGroupFormTestCaseBase):
    @classmethod
    def setUpTestData(cls):
        cls._create_data()
        cls._create_roc_check()

    def setUp(self):
        super().setUp()
        self.response = self._get_form()
        self.soup = BeautifulSoup(self.response.content, "html.parser")

    def test_thresholds(self):
        value = self.soup.find(id="id_timeseriesgroup_set-0-rocc_thresholds").text
        self.assertEqual(value.strip(), "10min\t25.0\n1h\t35.0")


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class AggregationFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.station = baker.make(enhydris.models.Station)
        cls.aggregation = baker.make(
            models.Aggregation,
            target_time_step="10min",
            method="sum",
            timeseries_group__gentity=cls.station,
        )

    def test_does_not_validate_when_invalid_time_step(self):
        form = AggregationForm(
            {
                "target_time_step": "1a",
                "method": "sum",
                "max_missing": 0,
                "resulting_timestamp_offset": "",
            },
            instance=self.aggregation,
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["target_time_step"][0], '"1a" is not a valid time step'
        )

    def test_validates(self):
        form = AggregationForm(
            {
                "target_time_step": "1h",
                "method": "sum",
                "max_missing": 0,
                "resulting_timestamp_offset": "",
            },
            instance=self.aggregation,
        )
        self.assertTrue(form.is_valid())


class CurvePeriodFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.station = baker.make(enhydris.models.Station)
        cls.ci = baker.make(
            models.CurveInterpolation,
            timeseries_group__gentity=cls.station,
            target_timeseries_group__gentity=cls.station,
        )
        cls.period = baker.make(
            models.CurvePeriod,
            curve_interpolation=cls.ci,
            start_date=dt.date(1980, 1, 1),
            end_date=dt.date(1985, 6, 30),
        )
        point = models.CurvePoint(curve_period=cls.period, x=2.718, y=3.141)
        point.save()
        point = models.CurvePoint(curve_period=cls.period, x=4, y=5)
        point.save()

    def test_init(self):
        form = CurvePeriodForm(instance=self.period)
        content = form.as_p()
        self.assertTrue("2.718\t3.141\n4.0\t5.0" in content)

    def test_save(self):
        form = CurvePeriodForm(
            {
                "start_date": dt.date(2019, 9, 3),
                "end_date": dt.date(2021, 9, 3),
                "points": "1\t2",
            },
            instance=self.period,
        )
        self.assertTrue(form.is_valid())
        form.save()
        point = models.CurvePoint.objects.get(curve_period=self.period)
        period = models.CurvePeriod.objects.get(curve_interpolation=self.ci)
        self.assertEqual(period.start_date, dt.date(2019, 9, 3))
        self.assertEqual(period.end_date, dt.date(2021, 9, 3))
        self.assertAlmostEqual(point.x, 1)
        self.assertAlmostEqual(point.y, 2)

    def test_validate(self):
        form = CurvePeriodForm(
            {
                "start_date": dt.date(2019, 9, 3),
                "end_date": dt.date(2021, 9, 3),
                "points": "garbage",
            },
            instance=self.period,
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["points"][0],
            'Error in line 1: "garbage" is not a valid pair of numbers',
        )


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class CurvePeriodsPermissionTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice",
            email="alice@alice.com",
            password="topsecret",
            is_active=True,
            is_staff=True,
            is_superuser=False,
        )
        self.station = baker.make(enhydris.models.Station, creator=self.user)

    def test_curve_periods_are_shown(self):
        assert self.client.login(username="alice", password="topsecret") is True
        response = self.client.get(
            "/admin/enhydris/station/{}/change/".format(self.station.id)
        )
        self.assertContains(response, "Curve periods")


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class CurveInterpolationInlineTargetTimeseriesGroupTestCase(TestCaseBase):
    @classmethod
    def setUpTestData(cls):
        cls._create_data()
        cls.station2 = baker.make(
            enhydris.models.Station, creator=cls.user, owner=cls.organization
        )
        cls.timeseries_group = baker.make(
            enhydris.models.TimeseriesGroup,
            gentity=cls.station,
            variable=cls.variable,
        )
        cls.timeseries_group2 = baker.make(
            enhydris.models.TimeseriesGroup,
            gentity=cls.station2,
            variable=cls.variable,
        )

    def test_target_timeseries_group_dropdown_contains_options_from_station1(self):
        response = self._get_form()
        soup = BeautifulSoup(response.content.decode(), "html.parser")
        select_id = (
            "id_timeseriesgroup_set-1-curveinterpolation_set-0-target_timeseries_group"
        )
        self.assertIsNotNone(
            soup.find(id=select_id).find("option", value=f"{self.timeseries_group.id}")
        )

    def test_target_timeseries_group_dropdown_not_contains_options_from_station2(self):
        response = self._get_form()
        soup = BeautifulSoup(response.content.decode(), "html.parser")
        select_id = (
            "id_timeseriesgroup_set-1-curveinterpolation_set-0-target_timeseries_group"
        )
        self.assertIsNone(
            soup.find(id=select_id).find("option", value=f"{self.timeseries_group2.id}")
        )

    def test_target_timeseries_group_dropdown_is_empty_when_adding_station(self):
        response = self.client.get("/admin/enhydris/station/add/")
        soup = BeautifulSoup(response.content.decode(), "html.parser")
        select_id = (
            "id_timeseriesgroup_set-0-curveinterpolation_set-0-target_timeseries_group"
        )
        self.assertIsNotNone(soup.find(id=select_id).find("option", value=""))
        self.assertIsNone(
            soup.find(id=select_id).find("option", value=f"{self.timeseries_group.id}")
        )
        self.assertIsNone(
            soup.find(id=select_id).find("option", value=f"{self.timeseries_group2.id}")
        )
