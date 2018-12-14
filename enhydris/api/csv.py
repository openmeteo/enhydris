import csv
import os
import tempfile
import textwrap
from zipfile import ZIP_DEFLATED, ZipFile

_station_list_csv_headers = [
    "id",
    "Name",
    "Alternative name",
    "Short name",
    "Alt short name",
    "Type",
    "Owner",
    "Start date",
    "End date",
    "Abscissa",
    "Ordinate",
    "SRID",
    "Approximate",
    "Altitude",
    "SRID",
    "Water basin",
    "Water division",
    "Political division",
    "Automatic",
    "Remarks",
    "Alternative remarks",
    "Last modified",
]


def _station_csv(s):
    return [
        s.id,
        s.name,
        s.name_alt,
        s.short_name,
        s.short_name_alt,
        "+".join([t.descr for t in s.stype.all()]),
        s.owner,
        s.start_date,
        s.end_date,
        s.original_abscissa(),
        s.original_ordinate(),
        s.srid,
        s.approximate,
        s.altitude,
        s.asrid,
        s.water_basin.name if s.water_basin else "",
        s.water_division.name if s.water_division else "",
        s.political_division.name if s.political_division else "",
        s.is_automatic,
        s.remarks,
        s.remarks_alt,
        s.last_modified,
    ]


_instrument_list_csv_headers = [
    "id",
    "Station",
    "Type",
    "Name",
    "Alternative name",
    "Manufacturer",
    "Model",
    "Start date",
    "End date",
    "Remarks",
    "Alternative remarks",
]


def _instrument_csv(i):
    return [
        i.id,
        i.station.id,
        i.type.descr if i.type else "",
        i.name,
        i.name_alt,
        i.manufacturer,
        i.model,
        i.start_date,
        i.end_date,
        i.remarks,
        i.remarks_alt,
    ]


_timeseries_list_csv_headers = [
    "id",
    "Station",
    "Instrument",
    "Variable",
    "Unit",
    "Name",
    "Alternative name",
    "Precision",
    "Time zone",
    "Time step",
    "Nom. Offs. Min.",
    "Nom. Offs. Mon.",
    "Act. Offs. Min.",
    "Act. Offs.  Mon.",
    "Remarks",
    "Alternative Remarks",
]


def _timeseries_csv(t):
    return [
        t.id,
        t.gentity.id,
        t.instrument.id if t.instrument else "",
        t.variable.descr if t.variable else "",
        t.unit_of_measurement.symbol,
        t.name,
        t.name_alt,
        t.precision,
        t.time_zone.code,
        t.time_step.descr if t.time_step else "",
        t.timestamp_rounding_minutes,
        t.timestamp_rounding_months,
        t.timestamp_offset_minutes,
        t.timestamp_offset_months,
    ]


def prepare_csv(queryset):
    tempdir = tempfile.mkdtemp()
    zipfilename = os.path.join(tempdir, "data.zip")
    zipfile = ZipFile(zipfilename, "w", ZIP_DEFLATED)

    stationsfilename = os.path.join(tempdir, "stations.csv")
    stationsfile = open(stationsfilename, "w", encoding="utf-8-sig")
    try:
        csvwriter = csv.writer(stationsfile)
        csvwriter.writerow(_station_list_csv_headers)
        for station in queryset:
            csvwriter.writerow(_station_csv(station))
    finally:
        stationsfile.close()
    zipfile.write(stationsfilename, "stations.csv")

    instrumentsfilename = os.path.join(tempdir, "instruments.csv")
    instrumentsfile = open(instrumentsfilename, "w", encoding="utf-8-sig")
    try:
        csvwriter = csv.writer(instrumentsfile)
        csvwriter.writerow(_instrument_list_csv_headers)
        for station in queryset:
            for instrument in station.instrument_set.all():
                csvwriter.writerow(_instrument_csv(instrument))
    finally:
        instrumentsfile.close()
    zipfile.write(instrumentsfilename, "instruments.csv")

    timeseriesfilename = os.path.join(tempdir, "timeseries.csv")
    timeseriesfile = open(timeseriesfilename, "w", encoding="utf-8-sig")
    try:
        csvwriter = csv.writer(timeseriesfile)
        csvwriter.writerow(_timeseries_list_csv_headers)
        for station in queryset:
            for timeseries in station.timeseries.order_by("instrument__id"):
                csvwriter.writerow(_timeseries_csv(timeseries))
    finally:
        timeseriesfile.close()
    zipfile.write(timeseriesfilename, "timeseries.csv")

    readmefilename = os.path.join(tempdir, "README")
    readmefile = open(readmefilename, "w")
    readmefile.write(
        textwrap.dedent(
            """\
            The functionality which provides you with CSV versions of the station,
            instrument and time series list is a quick way to enable HUMANS to
            examine these lists with tools such as spreadsheets. It is not
            intended to be used by any automation tools: headings, columns, file
            structure and everything is subject to change without notice.

            If you are a developer and need to write automation tools, do not rely
            on the CSV files. Instead, use the web API
            (https://enhydris.readthedocs.io/en/latest/dev/webservice-api.html).
            """
        )
    )
    readmefile.close()
    zipfile.write(readmefilename, "README")

    zipfile.close()
    os.remove(stationsfilename)
    os.remove(instrumentsfilename)
    os.remove(timeseriesfilename)
    os.remove(readmefilename)

    return zipfilename
