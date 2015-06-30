import inspect

# This module uses a strange hack to extend User and Group. It uses
# "class User(MetaObject):" to define a subclass of the original User which is
# then extended. So User and Group must be imported, despite the fact that at
# first glance they are masked.
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q


class MetaClass(type):
    """General metaclass which extends User/Group creators with additional
    methods"""

    def __new__(self, classname, classbases, classdict):
        try:
            frame = inspect.currentframe()
            frame = frame.f_back
            if classname in frame.f_locals:
                old_class = frame.f_locals.get(classname)
                for name, func in classdict.items():
                    if inspect.isfunction(func):
                        setattr(old_class, name, func)
                return old_class
            return type.__new__(self, classname, classbases, classdict)
        finally:
            del frame


class MetaObject(object):
    __metaclass__ = MetaClass


class User(MetaObject):
    """
    Extends class user with permission editing funtions.

    For example, for edit permission:

    $ user.has_row_perm(object, 'edit')
    False
    $ user.add_row_perm(object, 'edit')
    True
    $ user.has_row_perm(object, 'edit')
    True

    """

    def add_row_perm(self, instance, perm):
        """
        Add permission 'perm' to user 'self' for object(s) instance.

        instance variable may be an object or a queryset.
        """
        from enhydris.permissions.models import Permission
        if type(instance).__name__ == 'QuerySet':
            for object in instance:
                if self.has_row_perm(object, perm, True):
                    pass
                permission = Permission()
                permission.content_object = object
                permission.user = self
                permission.name = perm
                permission.save()
        else:

            if self.has_row_perm(instance, perm, True):
                return False
            permission = Permission()
            permission.content_object = instance
            permission.user = self
            permission.name = perm
            permission.save()

        return True

    def del_row_perm(self, instance, perm):
        """
        Remove permission 'perm' to user self for object instance.

        instance variable may be an object or a queryset.
        """
        from .models import Permission
        if type(instance).__name__ == 'QuerySet':
            for object in instance:
                if not self.has_row_perm(object, perm, True):
                    pass
                content_type = ContentType.objects.get_for_model(object)
                perms = Permission.objects.filter(
                    user=self, content_type__pk=content_type.id,
                    object_id=object.id, name=perm)
                perms.delete()
        else:
            if not self.has_row_perm(instance, perm, True):
                return False
            content_type = ContentType.objects.get_for_model(instance)
            objects = Permission.objects.filter(
                user=self, content_type__pk=content_type.id,
                object_id=instance.id, name=perm)
            objects.delete()
        return True

    def has_row_perm(self, instance, perm, only_me=False):
        """
        Check if user has permission 'perm' on object instance.
        """
        from enhydris.permissions.models import Permission
        if self.is_superuser:
            return True
        if not self.is_active:
            return False

        content_type = ContentType.objects.get_for_model(instance)
        objects = Permission.objects.filter(
            user=self, content_type__pk=content_type.id,
            object_id=instance.id, name=perm)
        if objects.count() > 0:
            return True

        # check groups
        if not only_me:
            for group in self.groups.all():
                if group.has_row_perm(instance, perm):
                    return True
        return False

    def get_rows_with_permission(self, instance, perm):
        """
        Get all permission objects for this user on object 'instance' for perm
        'perm'

        NOTE: instance can be a model and then, this method returns all
        permissions for user 'self' on all objects of this model type.

        For example:

        $ from hcore.models import Station
        ...
        $ user.get_rows_with_permission(Station,'edit')

        this will return a list of all the stations the user has 'edit'
        permission.
        """
        from enhydris.permissions.models import Permission
        content_type = ContentType.objects.get_for_model(instance)
        objects = Permission.objects.filter(
            Q(user=self) | Q(group__in=self.groups.all()),
            content_type__pk=content_type.id, name=perm)
        return objects


class Group(MetaObject):
    """Meta class to extend base Group class with permission editing methods"""
    def add_row_perm(self, instance, perm):
        from enhydris.permissions.models import Permission
        if type(instance).__name__ == 'QuerySet':
            for object in instance:
                if self.has_row_perm(object, perm):
                    pass
                permission = Permission()
                permission.content_object = object
                permission.user = self
                permission.name = perm
                permission.save()
        else:
            if self.has_row_perm(instance, perm):
                return False
            permission = Permission()
            permission.content_object = instance
            permission.group = self
            permission.name = perm
            permission.save()
        return True

    def del_row_perm(self, instance, perm):
        from enhydris.permissions.models import Permission
        if type(instance).__name__ == 'QuerySet':
            for object in instance:
                if not self.has_row_perm(object, perm, True):
                    pass
                content_type = ContentType.objects.get_for_model(object)
                perms = Permission.objects.filter(
                    user=self, content_type__pk=content_type.id,
                    object_id=object.id, name=perm)
                perms.delete()
        else:
            if not self.has_row_perm(instance, perm):
                return False
            content_type = ContentType.objects.get_for_model(instance)
            objects = Permission.objects.filter(
                group=self, content_type__pk=content_type.id,
                object_id=instance.id, name=perm)
            objects.delete()
        return True

    def has_row_perm(self, instance, perm):
        from enhydris.permissions.models import Permission
        content_type = ContentType.objects.get_for_model(instance)
        objects = Permission.objects.filter(
            group=self, content_type__pk=content_type.id,
            object_id=instance.id, name=perm)
        if objects.count() > 0:
            return True
        else:
            return False

    def get_rows_with_permission(self, instance, perm):
        from enhydris.permissions.models import Permission
        content_type = ContentType.objects.get_for_model(instance)
        objects = Permission.objects.filter(
            group=self, content_type__pk=content_type.id, name=perm)
        return objects
