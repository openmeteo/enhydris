from django.conf import settings
from django.shortcuts import get_object_or_404

from rest_framework import permissions

from enhydris.hcore import models


class CanEditOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow allowed users to edit an object.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if isinstance(obj, models.Timeseries):
            id = obj.gentity.id
        elif isinstance(obj, models.Gentity):
            id = obj.id
        else:
            return False
        station = get_object_or_404(models.Station, id=id)
        return hasattr(request.user, 'has_row_perm') \
            and request.user.has_row_perm(station, 'edit')


class CanCreateStation(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.method != 'POST' or not request.user.is_authenticated():
            return False
        if settings.ENHYDRIS_USERS_CAN_ADD_CONTENT or request.user.has_perm(
                'hcore.add_station'):
            return True
        return False
