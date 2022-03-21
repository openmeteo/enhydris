from django.contrib.auth.models import AnonymousUser, Permission, User
from django.test import TestCase, override_settings

from model_mommy import mommy

from enhydris import models
from enhydris.tests import TestTimeseriesMixin


class RulesTestCaseBase(TestCase, TestTimeseriesMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.alice = User.objects.create_user(username="alice")
        cls.bob = User.objects.create_user(username="bob")
        cls.charlie = User.objects.create_user(username="charlie")
        cls.david = User.objects.create_user(username="david")

        cls._create_test_timeseries()
        cls.station.creator = cls.alice
        cls.station.maintainers.set([cls.bob])
        cls.station.save()

        po = Permission.objects
        cls.charlie.user_permissions.add(
            po.get(content_type__app_label="enhydris", codename="view_station")
        )
        cls.charlie.user_permissions.add(
            po.get(content_type__app_label="enhydris", codename="change_station")
        )
        cls.charlie.user_permissions.add(
            po.get(content_type__app_label="enhydris", codename="delete_station")
        )
        cls.charlie.user_permissions.add(
            po.get(content_type__app_label="enhydris", codename="change_timeseries")
        )
        cls.charlie.user_permissions.add(
            po.get(content_type__app_label="enhydris", codename="delete_timeseries")
        )


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

    def test_user_with_model_permissions_can_change_timeseries_group(self):
        self.assertTrue(
            self.charlie.has_perm(
                "enhydris.change_timeseries_group", self.timeseries_group
            )
        )

    def test_user_with_model_permissions_can_delete_timeseries_group(self):
        self.assertTrue(
            self.charlie.has_perm(
                "enhydris.change_timeseries_group", self.timeseries_group
            )
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

    def test_user_without_permissions_cannot_change_timeseries_group(self):
        self.assertFalse(
            self.david.has_perm(
                "enhydris.change_timeseries_group", self.timeseries_group
            )
        )

    def test_user_without_permissions_cannot_delete_timeseries_group(self):
        self.assertFalse(
            self.david.has_perm(
                "enhydris.change_timeseries_group", self.timeseries_group
            )
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

    def test_creator_can_change_timeseries_group(self):
        self.assertTrue(
            self.alice.has_perm(
                "enhydris.change_timeseries_group", self.timeseries_group
            )
        )

    def test_creator_can_delete_timeseries_group(self):
        self.assertTrue(
            self.alice.has_perm(
                "enhydris.delete_timeseries_group", self.timeseries_group
            )
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

    def test_maintainer_can_change_timeseries_group(self):
        self.assertTrue(
            self.bob.has_perm("enhydris.change_timeseries_group", self.timeseries_group)
        )

    def test_maintainer_can_delete_timeseries_group(self):
        self.assertTrue(
            self.bob.has_perm("enhydris.delete_timeseries_group", self.timeseries_group)
        )

    def test_maintainer_can_change_timeseries(self):
        self.assertTrue(
            self.bob.has_perm("enhydris.change_timeseries", self.timeseries)
        )

    def test_maintainer_can_delete_timeseries(self):
        self.assertTrue(
            self.bob.has_perm("enhydris.delete_timeseries", self.timeseries)
        )


@override_settings(ENHYDRIS_USERS_CAN_ADD_CONTENT=False)
class RulesTestCaseWhenUsersCannotAddContent(RulesTestCaseBase, CommonTests):
    def test_creator_is_irrelevant_for_change_station(self):
        self.assertFalse(self.alice.has_perm("enhydris.change_station", self.station))

    def test_creator_is_irrelevant_for_delete_station(self):
        self.assertFalse(self.alice.has_perm("enhydris.delete_station", self.station))

    def test_creator_is_irrelevant_for_change_timeseries_group(self):
        self.assertFalse(
            self.alice.has_perm(
                "enhydris.change_timeseries_group", self.timeseries_group
            )
        )

    def test_creator_is_irrelevant_for_delete_timeseries_group(self):
        self.assertFalse(
            self.alice.has_perm(
                "enhydris.delete_timeseries_group", self.timeseries_group
            )
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

    def test_maintainer_is_irrelevant_for_change_timeseries_group(self):
        self.assertFalse(
            self.bob.has_perm("enhydris.change_timeseries_group", self.timeseries_group)
        )

    def test_maintainer_is_irrelevant_for_delete_timeseries_group(self):
        self.assertFalse(
            self.bob.has_perm("enhydris.delete_timeseries_group", self.timeseries_group)
        )

    def test_maintainer_is_irrelevant_for_change_timeseries(self):
        self.assertFalse(
            self.bob.has_perm("enhydris.change_timeseries", self.timeseries)
        )

    def test_maintainer_is_irrelevant_for_delete_timeseries(self):
        self.assertFalse(
            self.bob.has_perm("enhydris.delete_timeseries", self.timeseries)
        )


class ContentRulesTestCaseBase(TestCase, TestTimeseriesMixin):
    """Test case base for time series data and file content."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.alice = User.objects.create_user(username="alice")
        cls.bob = User.objects.create_user(username="bob")
        cls.charlie = User.objects.create_user(username="charlie")
        cls.david = User.objects.create_user(username="david")
        cls.anonymous = AnonymousUser()

        cls._create_test_timeseries()
        cls.gentityfile = mommy.make(models.GentityFile, gentity=cls.station)

        po = Permission.objects
        cls.charlie.user_permissions.add(
            po.get(content_type__app_label="enhydris", codename="view_station")
        )
        cls.charlie.user_permissions.add(
            po.get(content_type__app_label="enhydris", codename="change_station")
        )
        cls.charlie.user_permissions.add(
            po.get(content_type__app_label="enhydris", codename="delete_station")
        )
        cls.charlie.user_permissions.add(
            po.get(content_type__app_label="enhydris", codename="change_timeseries")
        )
        cls.charlie.user_permissions.add(
            po.get(content_type__app_label="enhydris", codename="delete_timeseries")
        )


@override_settings(ENHYDRIS_OPEN_CONTENT=True)
class ContentRulesWhenContentIsOpenTestCase(ContentRulesTestCaseBase):
    def test_anonymous_can_download_timeseries(self):
        self.assertTrue(
            self.anonymous.has_perm("enhydris.view_timeseries_data", self.timeseries)
        )

    def test_anonymous_can_download_gentity_file(self):
        self.assertTrue(
            self.anonymous.has_perm(
                "enhydris.view_gentityfile_content", self.timeseries
            )
        )


@override_settings(ENHYDRIS_OPEN_CONTENT=False)
class ContentRulesWhenContentIsNotOpen(ContentRulesTestCaseBase):
    def test_anonymous_cannot_download_timeseries(self):
        self.assertFalse(
            self.anonymous.has_perm("enhydris.view_timeseries_data", self.timeseries)
        )

    def test_anonymous_cannot_download_gentity_file(self):
        self.assertFalse(
            self.anonymous.has_perm(
                "enhydris.view_gentityfile_content", self.timeseries
            )
        )

    def test_logged_on_can_download_timeseries(self):
        self.assertTrue(
            self.david.has_perm("enhydris.view_timeseries_data", self.timeseries)
        )

    def test_logged_on_can_download_gentity_file(self):
        self.assertTrue(
            self.david.has_perm("enhydris.view_gentityfile_content", self.timeseries)
        )
