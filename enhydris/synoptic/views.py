"""Quasi-views.

Many (maybe all) of the "views" in this file are not exactly django views, as this app
uses celery to render its output to static files. So this file contains functionality
to do such offline rendering. It doesn't know about requests and responses, and it
doesn't know about HTTP. But logically it's the "views" part of a Django app.
"""

import math
import os
from io import BytesIO

from django.conf import settings
from django.contrib.gis.db.models import Extent
from django.http import HttpRequest
from django.template.loader import render_to_string

import matplotlib

# We have to execute matplotlib.use() after the matplotlib import and before the rest of
# the matplotlib imports, and isort doesn't like that. I'm afraid we need to tell isort
# to just skip this file.
# isort:skip_file
matplotlib.use("AGG")  # NOQA

import enhydris.context_processors  # NOQA
import matplotlib.pyplot as plt  # NOQA
import pandas.plotting  # NOQA
from enhydris.views_common import ensure_extent_is_large_enough  # NOQA
from matplotlib.dates import DateFormatter, DayLocator, HourLocator  # NOQA

pandas.plotting.register_matplotlib_converters()


class File:
    """Write string (or bytes) to a file.

    File(relative_filename).write(s) writes string s to the specified file.  The
    resulting output file name is the concatenation of ENHYDRIS_SYNOPTIC_ROOT plus
    relative_filename. Directories are automatically created. The file is written
    atomically; so if many processes attempt to write to it at the same time, only one
    will win (i.e. the file will not be corrupt).
    """

    def __init__(self, relative_filename):
        self.relative_filename = relative_filename
        self.full_pathname = os.path.join(
            settings.ENHYDRIS_SYNOPTIC_ROOT, relative_filename
        )

    def write(self, s):
        self._ensure_directory_exists()
        self._write_to_temporary_file(s)
        self._atomically_replace_final_file()

    def _ensure_directory_exists(self):
        dirname = os.path.dirname(self.full_pathname)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    def _write_to_temporary_file(self, s):
        self.temporary_full_pathname = self.full_pathname + ".1"
        mode = "wb" if isinstance(s, bytes) else "w"
        encoding = None if isinstance(s, bytes) else "utf-8"
        with open(self.temporary_full_pathname, mode, encoding=encoding) as f:
            f.write(s)

    def _atomically_replace_final_file(self):
        os.replace(self.temporary_full_pathname, self.full_pathname)


def render_synoptic_station(synstation):
    _check_for_null_values(synstation)
    _render_station_page(synstation)
    _render_station_charts(synstation)


def _check_for_null_values(synstation):
    for syntsg in synstation.synoptic_timeseries_groups:
        syntsg.value_is_null = math.isnan(getattr(syntsg, "value", float("NaN")))


def _render_station_page(synstation):
    output = render_to_string(
        "enhydris/synoptic/groupstation.html", context={"object": synstation}
    )
    filename = os.path.join(
        synstation.synoptic_group.slug,
        "station",
        str(synstation.station.id),
        "index.html",
    )
    File(filename).write(output)


def _render_station_charts(synstation):
    for t in synstation.synoptic_timeseries_groups:
        Chart(t, synstation.synoptic_timeseries_groups).render()


def render_synoptic_group(synoptic_group):
    _render_only_group(synoptic_group)
    _render_group_stations(synoptic_group)
    synoptic_group.send_early_warning_emails()


def _render_only_group(synoptic_group):
    context = {"object": synoptic_group, **_get_map_context(synoptic_group)}
    output = render_to_string("enhydris/synoptic/group.html", context=context)
    filename = os.path.join(synoptic_group.slug, "index.html")
    File(filename).write(output)


def _get_map_context(sgroup):
    dummy_request = HttpRequest()
    dummy_request.map_viewport = _get_bounding_box(sgroup)
    return enhydris.context_processors.map(dummy_request)


def _get_bounding_box(sgroup):
    extent = sgroup.synopticgroupstation_set.aggregate(Extent("station__geom"))[
        "station__geom__extent"
    ]
    extent = list(extent)
    ensure_extent_is_large_enough(extent)
    return extent


def _render_group_stations(synoptic_group):
    for synstation in synoptic_group.synopticgroupstation_set.all():
        render_synoptic_station(synstation)


class Chart:
    def __init__(self, current_syn_timeseries_group, all_synoptic_timeseries_groups):
        self.current_synoptic_timeseries_group = current_syn_timeseries_group
        self.all_synoptic_timeseries_groups = all_synoptic_timeseries_groups

    def render(self):
        self._get_all_groupped_timeseries_groups()
        self._reorder_groupped_timeseries_groups()
        self._setup_plot()
        self._draw_lines()
        if len(self.xdata):
            self._change_plot_limits()
            self._fill()
            self._set_x_ticks_and_labels()
            self._set_gridlines_and_legend()
        self._create_and_save_plot()
        self._write_data_to_file_for_unit_testing()

    def _get_all_groupped_timeseries_groups(self):
        self._synoptic_timeseries_groups = [
            x
            for x in self.all_synoptic_timeseries_groups
            if (x.id == self.current_synoptic_timeseries_group.id)
            or (
                x.group_with
                and x.group_with.id == self.current_synoptic_timeseries_group.id
            )
        ]

    def _reorder_groupped_timeseries_groups(self):
        self._synoptic_timeseries_groups.sort(
            key=lambda x: float(x.data.value.sum()), reverse=True
        )

    def _setup_plot(self):
        self.fig = plt.figure()
        self.fig.set_dpi(100)
        self.fig.set_size_inches(3.2, 2)
        self.fig.subplots_adjust(left=0.10, right=0.99, bottom=0.15, top=0.97)
        matplotlib.rcParams.update({"font.size": 7})
        self.ax = self.fig.add_subplot(1, 1, 1)

    def _draw_lines(self):
        for i, s in enumerate(self._synoptic_timeseries_groups):
            if len(s.data) <= 1:
                self._set_chart_empty()
            else:
                self._plot_line(i, s)
            if i == 0:
                # We will later need the data of the first time series, in
                # order to fill the chart
                self.gydata = self.ydata

    def _set_chart_empty(self):
        self.xdata = self.ydata = []

    def _plot_line(self, i, synts):
        # We use matplotlib's plot() instead of pandas's wrapper, because otherwise
        # there is trouble modifying the x axis labels (see
        # http://stackoverflow.com/questions/12945971/).
        self.xdata = synts.data.index.to_pydatetime()
        self.ydata = synts.data["value"]
        self.ax.plot(
            self.xdata, self.ydata, color=self._get_color(i), label=synts.get_subtitle()
        )

    def _change_plot_limits(self):
        self.ax.set_xlim(self.xdata[0], self.xdata[-1])
        self.xmin, self.xmax, self.ymin, self.ymax = self.ax.axis()
        if self.current_synoptic_timeseries_group.default_chart_min:
            self.ymin = min(
                self.current_synoptic_timeseries_group.default_chart_min, self.ymin
            )
        if self.current_synoptic_timeseries_group.default_chart_max:
            self.ymax = max(
                self.current_synoptic_timeseries_group.default_chart_max, self.ymax
            )
        self.ax.set_ylim([self.ymin, self.ymax])

    def _fill(self):
        self.ax.fill_between(self.xdata, self.gydata, self.ymin, color="#ffff00")

    def _set_x_ticks_and_labels(self):
        self.ax.xaxis.set_minor_locator(HourLocator(byhour=range(0, 24, 3)))
        self.ax.xaxis.set_minor_formatter(DateFormatter("%H:%M"))
        self.ax.xaxis.set_major_locator(DayLocator())
        self.ax.xaxis.set_major_formatter(
            DateFormatter("\n    %Y-%m-%d $\\rightarrow$")
        )

    def _set_gridlines_and_legend(self):
        self.ax.grid(b=True, which="both", color="b", linestyle=":")
        if len(self._synoptic_timeseries_groups) > 1:
            self.ax.legend()

    def _create_and_save_plot(self):
        f = BytesIO()
        self.fig.savefig(f)
        plt.close(self.fig)  # Release some memory
        filename = os.path.join(
            "chart", str(self.current_synoptic_timeseries_group.id) + ".png"
        )
        File(filename).write(f.getvalue())
        f.close()

    def _write_data_to_file_for_unit_testing(self):
        if hasattr(settings, "TEST_MATPLOTLIB") and settings.TEST_MATPLOTLIB:
            filename = os.path.join(
                "chart", str(self.current_synoptic_timeseries_group.id) + ".dat"
            )
            data = [
                repr(line.get_xydata()).replace("\n", " ") for line in self.ax.lines
            ]
            File(filename).write("(" + ", ".join(data) + ")")

    def _get_color(self, i):
        """Return the color to be used for line with sequence i.

        The first line to be drawn uses red, so self.get_color(0)='red';
        the second one uses green, so self.get_color(1)='green'; and there are
        also one or two more colors. We assume the user will not attempt to
        group more than a few time series together. However, if this happens,
        we recycle the colors starting from red again, to make sure we don't
        have an index error or anything.
        """
        colors = ["red", "green", "blue", "magenta"]
        return colors[i % len(colors)]
