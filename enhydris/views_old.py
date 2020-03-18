"""Views with old code that needs to be refactored or rewritten.

See ticket #181.
"""
import calendar
import json
import linecache
import math
import tempfile
from datetime import datetime, timedelta

from django.conf import settings
from django.http import Http404, HttpResponse

import iso8601

from enhydris.models import Timeseries


def add_months_to_datetime(adatetime, months):
    m, y, d = adatetime.month, adatetime.year, adatetime.day
    m += months
    while m > 12:
        m -= 12
        y += 1
    while m < 1:
        m += 12
        y -= 1
    d = min(d, calendar.monthrange(y, m)[1])
    return adatetime.replace(year=y, month=m, day=d)


def bufcount(filename):
    lines = 0
    with open(filename) as f:
        buf_size = 1024 * 1024
        read_f = f.read  # loop optimization
        buf = read_f(buf_size)
        while buf:
            lines += buf.count("\n")
            buf = read_f(buf_size)
    return lines


def timeseries_data(request, *args, **kwargs):
    # Timeseries data used to be stored in a CSV file. This was changed in #301 to use
    # timescaledb. This view used to read the CSV file directly. Since the code is
    # unreadable, until it is fixed (which is the subject of #181), we store the data
    # to a CSV file and give it to the old code to process.
    try:
        object_id = int(request.GET["object_id"])
        timeseries = Timeseries.objects.get(pk=object_id)
    except (ValueError, Timeseries.DoesNotExist):
        raise Http404
    with tempfile.NamedTemporaryFile(mode="w", newline="\n") as f:
        timeseries.get_data().write(f)
        return old_code_for_timeseries_data(
            request, *args, datafilename=f.name, **kwargs
        )


def old_code_for_timeseries_data(request, *args, datafilename, **kwargs):  # NOQA
    def date_at_pos(pos, tz):
        s = linecache.getline(datafilename, pos)
        return iso8601.parse_date(s.split(",")[0], default_timezone=tz)

    def timedeltadivide(a, b):
        """Divide timedelta a by timedelta b."""
        a = a.days * 86400 + a.seconds
        b = b.days * 86400 + b.seconds
        return float(a) / float(b)

    # Return the nearest record number to the specified date
    # The second argument is 0 for exact match, -1 if no
    # exact match and the date is after the record found,
    # 1 if no exact match and the date is before the record.
    def find_line_at_date(adatetime, totlines, tz):
        if totlines < 2:
            return totlines
        i1, i2 = 1, totlines
        d1 = date_at_pos(i1, tz)
        d2 = date_at_pos(i2, tz)
        if adatetime <= d1:
            return (i1, 0 if d1 == adatetime else 1)
        if adatetime >= d2:
            return (i2, 0 if d2 == adatetime else -1)
        while True:
            i = i1 + int(
                round(float(i2 - i1) * timedeltadivide(adatetime - d1, d2 - d1))
            )
            d = date_at_pos(i, tz)
            if d == adatetime:
                return (i, 0)
            if (i == i1) or (i == i2):
                return (i, -1 if i == i1 else 1)
            if d < adatetime:
                d1, i1 = d, i
            if d > adatetime:
                d2, i2 = d, i

    def add_to_stats(date, value):
        if not gstats["max"]:
            gstats["max"] = value
            gstats["min"] = value
            gstats["sum"] = 0
            gstats["vsum"] = [0.0, 0.0]
            gstats["count"] = 0
            gstats["vectors"] = [0] * 8
        if value >= gstats["max"]:
            gstats["max"] = value
            gstats["max_tstmp"] = date
        if value <= gstats["min"]:
            gstats["min"] = value
            gstats["min_tstmp"] = date
        if is_vector:
            value2 = value
            if value2 >= 360:
                value2 -= 360
            if value2 < 0:
                value2 += 360
            if value2 < 0 or value2 > 360:
                return
            # reversed order of x, y since atan2 definition is
            # math.atan2(y, x)
            gstats["vsum"][1] += math.cos(value2 * math.pi / 180)
            gstats["vsum"][0] += math.sin(value2 * math.pi / 180)
            value2 = value2 + 22.5 if value2 < 337.5 else value2 - 337.5
            gstats["vectors"][int(value2 / 45)] += 1
        gstats["sum"] += value
        gstats["last"] = value
        gstats["last_tstmp"] = date
        gstats["count"] += 1

    def inc_datetime(adate, unit, steps):
        if unit == "day":
            return adate + steps * timedelta(days=1)
        elif unit == "week":
            return adate + steps * timedelta(weeks=1)
        elif unit == "month":
            return add_months_to_datetime(adate, steps)
        elif unit == "year":
            return add_months_to_datetime(adate, 12 * steps)
        elif unit == "moment":
            return adate
        elif unit == "hour":
            return adate + steps * timedelta(minutes=60)
        elif unit == "twohour":
            return adate + steps * timedelta(minutes=120)
        else:
            raise Http404

    if (request.method != "GET") or ("object_id" not in request.GET):
        raise Http404

    response = HttpResponse(content_type="application/json")
    response.status_code = 200
    try:
        object_id = int(request.GET["object_id"])
        timeseries = Timeseries.objects.get(pk=object_id)
    except (ValueError, Timeseries.DoesNotExist):
        raise Http404
    tz = timeseries.time_zone.as_tzinfo
    chart_data = []
    if "start_pos" in request.GET and "end_pos" in request.GET:
        start_pos = int(request.GET["start_pos"])
        end_pos = int(request.GET["end_pos"])
    else:
        end_pos = bufcount(datafilename)
        tot_lines = end_pos
        if "last" in request.GET:
            if request.GET.get("date", False):
                datetimestr = request.GET["date"]
                datetimefmt = "%Y-%m-%d"
                if request.GET.get("time", False):
                    datetimestr = datetimestr + " " + request.GET["time"]
                    datetimefmt = datetimefmt + " %H:%M"
                try:
                    first_date = datetime.strptime(datetimestr, datetimefmt)
                    last_date = inc_datetime(first_date, request.GET["last"], 1)
                    (end_pos, is_exact) = find_line_at_date(last_date, tot_lines, tz)
                    if request.GET.get("exact_datetime", False) and (is_exact != 0):
                        raise Http404
                except ValueError:
                    raise Http404
            else:
                last_date = date_at_pos(end_pos, tz)
                first_date = inc_datetime(last_date, request.GET["last"], -1)
                # This is an almost bad workarround to exclude the first
                # record from sums, i.e. when we need the 144 10 minute
                # values from a day.
                if "start_offset" in request.GET:
                    offset = float(request.GET["start_offset"])
                    first_date += timedelta(minutes=offset)
            start_pos = find_line_at_date(first_date, tot_lines, tz)[0]
        else:
            start_pos = 1

    length = end_pos - start_pos + 1
    step = int(length / settings.ENHYDRIS_TS_GRAPH_BIG_STEP_DENOMINATOR) or 1
    fine_step = int(step / settings.ENHYDRIS_TS_GRAPH_FINE_STEP_DENOMINATOR) or 1
    if not step % fine_step == 0:
        step = fine_step * settings.ENHYDRIS_TS_GRAPH_FINE_STEP_DENOMINATOR
    pos = start_pos
    amax = ""
    prev_pos = -1
    tick_pos = -1
    is_vector = request.GET.get("vector", False)
    gstats = {
        "max": None,
        "min": None,
        "count": 0,
        "max_tstmp": None,
        "min_tstmp": None,
        "sum": None,
        "avg": None,
        "vsum": None,
        "vavg": None,
        "last": None,
        "last_tstmp": None,
        "vectors": None,
    }
    afloat = 0.01
    try:
        linecache.checkcache(datafilename)
        while pos < start_pos + length:
            s = linecache.getline(datafilename, pos)
            if s.isspace():
                pos += fine_step
                continue
            t = s.split(",")
            # Use the following exception handling to catch incoplete
            # reads from cache. Tries only one time, next time if
            # the error on the same line persists, it raises.
            try:
                k = iso8601.parse_date(t[0], default_timezone=tz)
                v = t[1]
            except Exception:
                if pos > prev_pos:
                    prev_pos = pos
                    linecache.checkcache(datafilename)
                    continue
                else:
                    raise
            if v != "":
                afloat = float(v)
                add_to_stats(k, afloat)
                if amax == "":
                    amax = afloat
                else:
                    amax = afloat if afloat > amax else amax
            if (pos - start_pos) % step == 0:
                tick_pos = pos
                if amax == "":
                    amax = "null"
                chart_data.append(
                    [calendar.timegm(k.timetuple()) * 1000, str(amax), pos]
                )
                amax = ""
            # Sometimes linecache tries to read a file being written (from
            # timeseries.write_file). So every 5000 lines refresh the
            # cache.
            if (pos - start_pos) % 5000 == 0:
                linecache.checkcache(datafilename)
            pos += fine_step
        if length > 0 and tick_pos < end_pos:
            if amax == "":
                amax = "null"
            chart_data[-1] = [calendar.timegm(k.timetuple()) * 1000, str(amax), end_pos]
    finally:
        linecache.clearcache()
    if chart_data:
        if gstats["count"] > 0:
            gstats["avg"] = gstats["sum"] / gstats["count"]
            if is_vector:
                gstats["vavg"] = math.atan2(*gstats["vsum"]) * 180 / math.pi
                if gstats["vavg"] < 0:
                    gstats["vavg"] += 360
            for item in ("max_tstmp", "min_tstmp", "last_tstmp"):
                gstats[item] = calendar.timegm(gstats[item].timetuple()) * 1000
        response.content = json.dumps({"data": chart_data, "stats": gstats})
    else:
        response.content = json.dumps("")
    callback = request.GET.get("jsoncallback", None)
    if callback:
        response.content = "%s(%s)" % (callback, response.content)
    return response
