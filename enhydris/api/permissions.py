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
        return request.user.has_perm("enhydris.add_station")


class CanAccessTimeseriesData(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return request.user.has_perm("enhydris.view_timeseries_data", obj)
        else:
            return request.user.has_perm(
                "enhydris.change_station", obj.timeseries_group.gentity.gpoint.station
            )


class CanAccessGentityFileContent(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return request.user.has_perm("enhydris.view_gentityfile_content", obj)
        else:
            return request.user.has_perm(
                "enhydris.change_station", obj.gentity.gpoint.station
            )
