"""How the Enhydris object-level permissions system works.

django.contrib.auth has some provisions (but not actual support) for object-level
permissions. You can use either ``user.has_perm("enhydris.change_station")`` or
``user.has_perm("enhydris.change_station", some_station_object)``; the first version is
for model-level permission and the second one is for object-level permission.
django.contrib.auth only has support for model-level permissions; the second version
would always return False. The only built-in Django app that uses permissions is
django.contrib.admin, and it also uses only model-level permissions.

When we want to extend the system to use object-level permissions, Django provides us
with the above API but it does not provide us with guidelines or documentation on how to
use that API. Should the user have both model-level permissions AND object-level
permissions to be able to change a station? Or only one of the two? It's up to us to
specify how things are going to work. The choice we've made here is that the user needs
to have either model-level or object-level permissions. If the user has a model-level
"enhydris.change_station" permission, he's a privileged user with permission to change
all stations. If he doesn't have the system-wide permission, he might still have
permission to change a subset of the stations (namely those for which he's the creator
or maintainer, provided ENHYDRIS_USERS_CAN_ADD_CONTENT=True).

We use django-rules to implement this. StationAdmin (and possibly other ModelAdmin
subclasses) inherits from rules.contrib.admin.ObjectPermissionsModelAdmin rather than
django.contrib.admin.ModelAdmin so that they make use of these permissions.
"""
from django.conf import settings
from django.contrib.auth.backends import ModelBackend

import rules


@rules.predicate
def is_station_creator(user, station):
    return station.creator == user


@rules.predicate
def is_station_maintainer(user, station):
    return user in station.maintainers.all()


def get_object_station(obj):
    try:
        return obj.station
    except AttributeError:
        return obj.gentity.gpoint.station


@rules.predicate
def is_object_station_creator(user, obj):
    return get_object_station(obj).creator == user


@rules.predicate
def is_object_station_maintainer(user, obj):
    return user in get_object_station(obj).maintainers.all()


@rules.predicate
def is_superuser(user, obj):
    return user.is_superuser


@rules.predicate
def is_active(user, obj):
    return user.is_active


@rules.predicate
def is_new_object(user, obj):
    return obj is None


@rules.predicate
def users_can_add_content(user, obj):
    return settings.ENHYDRIS_USERS_CAN_ADD_CONTENT


@rules.predicate
def model_backend_can_add_station(user, obj):
    return ModelBackend().has_perm(user, "enhydris.add_station")


@rules.predicate
def model_backend_can_edit_station(user, obj):
    return ModelBackend().has_perm(user, "enhydris.change_station")


@rules.predicate
def model_backend_can_delete_station(user, obj):
    return ModelBackend().has_perm(user, "enhydris.delete_station")


@rules.predicate
def model_backend_can_edit_instrument(user, obj):
    return ModelBackend().has_perm(user, "enhydris.change_instrument")


@rules.predicate
def model_backend_can_edit_timeseries(user, obj):
    return ModelBackend().has_perm(user, "enhydris.change_timeseries")


can_add_station = (users_can_add_content & is_active) | model_backend_can_add_station
can_edit_station = model_backend_can_edit_station | (
    users_can_add_content
    & ~is_new_object
    & (is_station_creator | is_station_maintainer)
)
can_delete_station = (
    users_can_add_content & ~is_new_object & is_station_creator
) | model_backend_can_delete_station
can_touch_instrument = (
    users_can_add_content & (is_object_station_creator | is_object_station_maintainer)
) | model_backend_can_edit_instrument
can_touch_timeseries = (
    users_can_add_content & (is_object_station_creator | is_object_station_maintainer)
) | model_backend_can_edit_timeseries

rules.add_perm("enhydris", rules.always_allow)
rules.add_perm("enhydris.add_station", can_add_station)
rules.add_perm("enhydris.view_station", rules.always_allow)
rules.add_perm("enhydris.change_station", can_edit_station)
rules.add_perm("enhydris.delete_station", can_delete_station)

rules.add_perm("enhydris.add_timeseries", can_touch_timeseries)
rules.add_perm("enhydris.change_timeseries", can_touch_timeseries)
rules.add_perm("enhydris.delete_timeseries", can_touch_timeseries)
rules.add_perm("enhydris.change_instrument", can_touch_instrument)
rules.add_perm("enhydris.delete_instrument", can_touch_instrument)

rules.add_perm("enhydris.change_station_creator", is_superuser)
rules.add_perm(
    "enhydris.change_station_maintainers",
    users_can_add_content
    & (model_backend_can_edit_station | is_new_object | is_station_creator),
)
