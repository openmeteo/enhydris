from django.contrib.auth.models import Permission, User
from django.test import TestCase, override_settings

from model_mommy import mommy

from enhydris import models


class RulesTestCaseBase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.alice = User.objects.create_user(username="alice")
        cls.bob = User.objects.create_user(username="bob")
        cls.charlie = User.objects.create_user(username="charlie")
        cls.david = User.objects.create_user(username="david")

        cls.station = mommy.make(
            models.Station, creator=cls.alice, maintainers=[cls.bob]
        )
        cls.instrument = mommy.make(models.Instrument, station=cls.station)
        cls.timeseries = mommy.make(models.Timeseries, gentity=cls.station)

        po = Permission.objects
        cls.charlie.user_permissions.add(po.get(codename="view_station"))
        cls.charlie.user_permissions.add(po.get(codename="change_station"))
        cls.charlie.user_permissions.add(po.get(codename="delete_station"))
        cls.charlie.user_permissions.add(po.get(codename="change_timeseries"))
        cls.charlie.user_permissions.add(po.get(codename="delete_timeseries"))
        cls.charlie.user_permissions.add(po.get(codename="change_instrument"))
        cls.charlie.user_permissions.add(po.get(codename="delete_instrument"))


class CommonTests:
    """Tests that will run both for ENHYDRIS_USERS_CAN_ADD_CONTENT=True and False.

    Below we have two TestCase subclasses (actually RulesTestCaseBase subclasses); one
    of them overrides setting ENHYDRIS_USERS_CAN_ADD_CONTENT to True, and the other one
    to False. This is a mixin containing tests that should have the same results in
    both cases.
    """

    def test_user_with_model_permissions_can_change_station(self):
        self.assertTrue(self.charlie.has_perm("enhydris.change_station", self.station))

    def test_user_with_model_permissions_can_delete_station(self):
        self.assertTrue(self.charlie.has_perm("enhydris.change_station", self.station))

    def test_user_with_model_permissions_can_change_instrument(self):
        self.assertTrue(
            self.charlie.has_perm("enhydris.change_instrument", self.instrument)
        )

    def test_user_with_model_permissions_can_delete_instrument(self):
        self.assertTrue(
            self.charlie.has_perm("enhydris.delete_instrument", self.instrument)
        )

    def test_user_with_model_permissions_can_change_timeseries(self):
        self.assertTrue(
            self.charlie.has_perm("enhydris.change_timeseries", self.timeseries)
        )

    def test_user_with_model_permissions_can_delete_timeseries(self):
        self.assertTrue(
            self.charlie.has_perm("enhydris.change_timeseries", self.timeseries)
        )

    def test_user_without_permissions_cannot_change_station(self):
        self.assertFalse(self.david.has_perm("enhydris.change_station", self.station))

    def test_user_without_permissions_cannot_delete_station(self):
        self.assertFalse(self.david.has_perm("enhydris.change_station", self.station))

    def test_user_without_permissions_cannot_change_instrument(self):
        self.assertFalse(
            self.david.has_perm("enhydris.change_instrument", self.instrument)
        )

    def test_user_without_permissions_cannot_delete_instrument(self):
        self.assertFalse(
            self.david.has_perm("enhydris.delete_instrument", self.instrument)
        )

    def test_user_without_permissions_cannot_change_timeseries(self):
        self.assertFalse(
            self.david.has_perm("enhydris.change_timeseries", self.timeseries)
        )

    def test_user_without_permissions_cannot_delete_timeseries(self):
        self.assertFalse(
            self.david.has_perm("enhydris.change_timeseries", self.timeseries)
        )


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=True)
class RulesTestCaseWhenUsersCanAddContent(RulesTestCaseBase, CommonTests):
    def test_creator_can_change_station(self):
        self.assertTrue(self.alice.has_perm("enhydris.change_station", self.station))

    def test_creator_can_delete_station(self):
        self.assertTrue(self.alice.has_perm("enhydris.delete_station", self.station))

    def test_creator_can_change_instrument(self):
        self.assertTrue(
            self.alice.has_perm("enhydris.change_instrument", self.instrument)
        )

    def test_creator_can_delete_instrument(self):
        self.assertTrue(
            self.alice.has_perm("enhydris.delete_instrument", self.instrument)
        )

    def test_creator_can_change_timeseries(self):
        self.assertTrue(
            self.alice.has_perm("enhydris.change_timeseries", self.timeseries)
        )

    def test_creator_can_delete_timeseries(self):
        self.assertTrue(
            self.alice.has_perm("enhydris.delete_timeseries", self.timeseries)
        )

    def test_maintainer_can_change_station(self):
        self.assertTrue(self.bob.has_perm("enhydris.change_station", self.station))

    def test_maintainer_cannot_delete_station(self):
        self.assertFalse(self.bob.has_perm("enhydris.delete_station", self.station))

    def test_maintainer_can_change_timeseries(self):
        self.assertTrue(
            self.bob.has_perm("enhydris.change_timeseries", self.timeseries)
        )

    def test_maintainer_can_delete_timeseries(self):
        self.assertTrue(
            self.bob.has_perm("enhydris.delete_timeseries", self.timeseries)
        )

    def test_maintainer_can_change_instrument(self):
        self.assertTrue(
            self.bob.has_perm("enhydris.change_instrument", self.instrument)
        )

    def test_maintainer_can_delete_instrument(self):
        self.assertTrue(
            self.bob.has_perm("enhydris.delete_instrument", self.instrument)
        )


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=False)
class RulesTestCaseWhenUsersCannotAddContent(RulesTestCaseBase, CommonTests):
    def test_creator_is_irrelevant_for_change_station(self):
        self.assertFalse(self.alice.has_perm("enhydris.change_station", self.station))

    def test_creator_is_irrelevant_for_delete_station(self):
        self.assertFalse(self.alice.has_perm("enhydris.delete_station", self.station))

    def test_creator_is_irrelevant_for_change_instrument(self):
        self.assertFalse(
            self.alice.has_perm("enhydris.change_instrument", self.instrument)
        )

    def test_creator_is_irrelevant_for_delete_instrument(self):
        self.assertFalse(
            self.alice.has_perm("enhydris.delete_instrument", self.instrument)
        )

    def test_creator_is_irrelevant_for_change_timeseries(self):
        self.assertFalse(
            self.alice.has_perm("enhydris.change_timeseries", self.timeseries)
        )

    def test_creator_is_irrelevant_for_delete_timeseries(self):
        self.assertFalse(
            self.alice.has_perm("enhydris.delete_timeseries", self.timeseries)
        )

    def test_maintainer_is_irrelevant_for_change_station(self):
        self.assertFalse(self.bob.has_perm("enhydris.change_station", self.station))

    def test_maintainer_is_irrelevant_for_delete_station(self):
        self.assertFalse(self.bob.has_perm("enhydris.delete_station", self.station))

    def test_maintainer_is_irrelevant_for_change_instrument(self):
        self.assertFalse(
            self.bob.has_perm("enhydris.change_instrument", self.instrument)
        )

    def test_maintainer_is_irrelevant_for_delete_instrument(self):
        self.assertFalse(
            self.bob.has_perm("enhydris.delete_instrument", self.instrument)
        )

    def test_maintainer_is_irrelevant_for_change_timeseries(self):
        self.assertFalse(
            self.bob.has_perm("enhydris.change_timeseries", self.timeseries)
        )

    def test_maintainer_is_irrelevant_for_delete_timeseries(self):
        self.assertFalse(
            self.bob.has_perm("enhydris.delete_timeseries", self.timeseries)
        )
