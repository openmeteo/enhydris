from django.contrib.auth.models import User
from django.test import TestCase

from model_mommy import mommy

from enhydris import models


class RulesTestCase(TestCase):
    def setUp(self):
        self.alice = mommy.make(User, username="alice")
        self.bob = mommy.make(User, username="bob")
        self.charlie = mommy.make(User, username="charlie")

        self.station = mommy.make(
            models.Station, creator=self.alice, maintainers=[self.bob]
        )
        self.instrument = mommy.make(models.Instrument, station=self.station)
        self.timeseries = mommy.make(models.Timeseries, gentity=self.station)

    def test_creator_can_edit_station(self):
        self.assertTrue(self.alice.has_perm("enhydris.change_station", self.station))

    def test_maintainer_can_edit_station(self):
        self.assertTrue(self.bob.has_perm("enhydris.change_station", self.station))

    def test_irrelevant_user_cannot_edit_station(self):
        self.assertFalse(self.charlie.has_perm("enhydris.change_station", self.station))

    def test_creator_can_delete_station(self):
        self.assertTrue(self.alice.has_perm("enhydris.delete_station", self.station))

    def test_maintainer_cannot_delete_station(self):
        self.assertFalse(self.bob.has_perm("enhydris.delete_station", self.station))

    def test_irrelevant_user_cannot_delete_station(self):
        self.assertFalse(self.charlie.has_perm("enhydris.change_station", self.station))

    def test_creator_can_edit_timeseries(self):
        self.assertTrue(
            self.alice.has_perm("enhydris.change_timeseries", self.timeseries)
        )

    def test_maintainer_can_edit_timeseries(self):
        self.assertTrue(
            self.bob.has_perm("enhydris.change_timeseries", self.timeseries)
        )

    def test_irrelevant_user_cannot_edit_timeseries(self):
        self.assertFalse(
            self.charlie.has_perm("enhydris.change_timeseries", self.timeseries)
        )

    def test_creator_can_delete_timeseries(self):
        self.assertTrue(
            self.alice.has_perm("enhydris.delete_timeseries", self.timeseries)
        )

    def test_maintainer_can_delete_timeseries(self):
        self.assertTrue(
            self.bob.has_perm("enhydris.delete_timeseries", self.timeseries)
        )

    def test_irrelevant_user_cannot_delete_timeseries(self):
        self.assertFalse(
            self.charlie.has_perm("enhydris.change_timeseries", self.timeseries)
        )

    def test_creator_can_edit_instrument(self):
        self.assertTrue(
            self.alice.has_perm("enhydris.change_instrument", self.instrument)
        )

    def test_maintainer_can_edit_instrument(self):
        self.assertTrue(
            self.bob.has_perm("enhydris.change_instrument", self.instrument)
        )

    def test_irrelevant_user_cannot_edit_instrument(self):
        self.assertFalse(
            self.charlie.has_perm("enhydris.change_instrument", self.instrument)
        )

    def test_creator_can_delete_instrument(self):
        self.assertTrue(
            self.alice.has_perm("enhydris.delete_instrument", self.instrument)
        )

    def test_maintainer_can_delete_instrument(self):
        self.assertTrue(
            self.bob.has_perm("enhydris.delete_instrument", self.instrument)
        )

    def test_irrelevant_user_cannot_delete_instrument(self):
        self.assertFalse(
            self.charlie.has_perm("enhydris.change_instrument", self.instrument)
        )
