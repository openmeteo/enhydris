from __future__ import annotations

from django.conf import settings
from django.db.models import Model
from django.http import HttpRequest
from django.views import View
from rest_framework import permissions

from enhydris import models


class SatisfiesAuthenticationRequiredSetting(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, view: View):
        return (
            not settings.ENHYDRIS_AUTHENTICATION_REQUIRED
        ) or request.user.is_authenticated


class CanEditOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow allowed users to edit an object.
    """

    def has_object_permission(
        self, request: HttpRequest, view: View, obj: Model | None
    ) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        type_name = type(obj).__name__.lower()
        return request.user.has_perm("enhydris.change_" + type_name, obj)  # type: ignore


class CanCreateStation(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, view: View) -> bool:
        return request.user.has_perm("enhydris.add_station")  # type: ignore


class CanAccessTimeseriesData(permissions.BasePermission):
    def has_object_permission(
        self, request: HttpRequest, view: View, obj: models.Timeseries | None
    ) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return request.user.has_perm("enhydris.view_timeseries_data", obj)  # type: ignore
        else:
            return request.user.has_perm(  # type: ignore
                "enhydris.change_station", obj.timeseries_group.gentity.gpoint.station  # type: ignore
            )
