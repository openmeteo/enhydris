import csv
from io import BytesIO, StringIO
from zipfile import ZIP_DEFLATED, ZipFile

_station_list_csv_headers = [
    "id",
    "Name",
    "Short name",
    "Type",
    "Owner",
    "Start date",
    "End date",
    "Abscissa",
    "Ordinate",
    "SRID",
    "Altitude",
    "SRID",
    "Remarks",
    "Last modified",
]


def _station_csv(s):
    return [
        s.id,
        s.name,
        s.code,
        s.owner,
        s.start_date,
        s.end_date,
        s.original_abscissa(),
        s.original_ordinate(),
        s.original_srid,
        s.altitude,
        s.remarks,
        s.last_modified,
    ]


_timeseries_list_csv_headers = [
    "id",
    "Station",
    "Variable",
    "Unit",
    "Name",
    "Precision",
    "Time zone",
    "Time step",
    "Remarks",
]


def _timeseries_group_csv(tg):
    time_step = tg.default_timeseries.time_step if tg.default_timeseries else ""
    return [
        tg.id,
        tg.gentity.id,
        tg.variable.descr if tg.variable else "",
        tg.unit_of_measurement.symbol,
        tg.name,
        tg.precision,
        tg.time_zone.code,
        time_step,
    ]


def prepare_csv(queryset):
    with BytesIO() as result:
        with ZipFile(result, "w", ZIP_DEFLATED) as zipfile:
            with StringIO() as stations_csv:
                csvwriter = csv.writer(stations_csv)
                csvwriter.writerow(_station_list_csv_headers)
                for station in queryset:
                    csvwriter.writerow(_station_csv(station))
                zipfile.writestr("stations.csv", stations_csv.getvalue())

            with StringIO() as timeseries_csv:
                csvwriter = csv.writer(timeseries_csv)
                csvwriter.writerow(_timeseries_list_csv_headers)
                for station in queryset:
                    for timeseries_group in station.timeseriesgroup_set.all():
                        csvwriter.writerow(_timeseries_group_csv(timeseries_group))
                zipfile.writestr("timeseries.csv", timeseries_csv.getvalue())

        return result.getvalue()
