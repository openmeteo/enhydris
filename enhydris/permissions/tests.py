import unittest

from django.contrib.auth.models import Group, User

from enhydris.models import Gentity


class PermissionsTestCase(unittest.TestCase):
    def setUp(self):
        self.object = Gentity.objects.create(name="testgent")
        self.object.save()
        self.user = User.objects.create(username="testuser")
        self.user.save()
        self.group = Group.objects.create(name="testgroup")
        self.group.save()

    def tearDown(self):
        self.object.delete()
        self.user.delete()
        self.group.delete()

    def testUserPerms(self):
        assert self.user.has_row_perm(self.object, "permission") is False
        self.user.add_row_perm(self.object, "permission")
        assert self.user.has_row_perm(self.object, "permission") is True
        self.user.del_row_perm(self.object, "permission")
        assert self.user.has_row_perm(self.object, "permission") is False

    def testGroupPerms(self):
        assert self.user.has_row_perm(self.object, "permission") is False
        assert self.group.has_row_perm(self.object, "permission") is False
        self.group.user_set.add(self.user)
        self.group.add_row_perm(self.object, "permission")
        assert self.group.has_row_perm(self.object, "permission") is True
        assert self.user.has_row_perm(self.object, "permission") is True
        self.group.del_row_perm(self.object, "permission")
        assert self.user.has_row_perm(self.object, "permission") is False
        assert self.group.has_row_perm(self.object, "permission") is False
