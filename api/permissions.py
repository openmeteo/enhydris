from rest_framework import permissions
from django.shortcuts import get_object_or_404
from enhydris.core import models


class CanEditOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow allowed users to edit a timeseries object.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        station = get_object_or_404(models.Station, id=obj.station.id)
        return hasattr(request.user, 'has_row_perm'
               ) and request.user.has_row_perm(station, 'edit')
