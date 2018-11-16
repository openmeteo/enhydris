from django.conf import settings
from rest_framework import permissions


class CanEditOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow allowed users to edit an object.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        type_name = type(obj).__name__.lower()
        return request.user.has_perm("enhydris.change_" + type_name, obj)


class CanCreateStation(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.method != "POST" or not request.user.is_authenticated():
            return False
        if settings.ENHYDRIS_USERS_CAN_ADD_CONTENT or request.user.has_perm(
            "enhydris.add_station"
        ):
            return True
        return False
