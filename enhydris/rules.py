from django.conf import settings
from django.contrib.auth.backends import ModelBackend

import rules


@rules.predicate
def is_station_creator(user, station):
    return (station is not None) and station.creator == user


@rules.predicate
def is_station_maintainer(user, station):
    return (station is not None) and user in station.maintainers.all()


def get_object_station(obj):
    try:
        return obj.station
    except AttributeError:
        return obj.gentity.gpoint.station


@rules.predicate
def is_object_station_creator(user, obj):
    if obj is None:
        return False
    return get_object_station(obj).creator == user


@rules.predicate
def is_object_station_maintainer(user, obj):
    if obj is None:
        return False
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
    users_can_add_content & (is_station_creator | is_station_maintainer)
)
can_delete_station = (
    users_can_add_content & is_station_creator
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

rules.add_perm(
    "enhydris.change_station_creator",
    users_can_add_content & model_backend_can_edit_station,
)
rules.add_perm(
    "enhydris.change_station_maintainers",
    users_can_add_content
    & (model_backend_can_edit_station | is_station_creator | is_new_object),
)
