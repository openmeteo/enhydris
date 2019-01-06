import rules


@rules.predicate
def is_station_creator(user, station):
    return station.creator == user


@rules.predicate
def is_station_maintainer(user, station):
    return user in station.maintainers.all()


@rules.predicate
def is_timeseries_station_creator(user, timeseries):
    return timeseries.gentity.gpoint.station.creator == user


@rules.predicate
def is_timeseries_station_maintainer(user, timeseries):
    return user in timeseries.gentity.gpoint.station.maintainers.all()


@rules.predicate
def is_instrument_station_creator(user, instrument):
    return instrument.station.creator == user


@rules.predicate
def is_instrument_station_maintainer(user, instrument):
    return user in instrument.station.maintainers.all()


rules.add_perm("enhydris.change_station", is_station_creator | is_station_maintainer)
rules.add_perm("enhydris.delete_station", is_station_creator)

rules.add_perm(
    "enhydris.change_timeseries",
    is_timeseries_station_creator | is_timeseries_station_maintainer,
)
rules.add_perm(
    "enhydris.delete_timeseries",
    is_timeseries_station_creator | is_timeseries_station_maintainer,
)

rules.add_perm(
    "enhydris.change_instrument",
    is_instrument_station_creator | is_instrument_station_maintainer,
)
rules.add_perm(
    "enhydris.delete_instrument",
    is_instrument_station_creator | is_instrument_station_maintainer,
)
