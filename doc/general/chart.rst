.. chart:

===================
How the chart works
===================

In the time series detail page there is a chart that aims to give the
user a quick overview of the time series. It is zoomable and it should
be obvious how it works, but this text explains it in detail.

At the time of this writing, the chart consists of 200 points joined
together with a line. Since the chart isn't much wider than 200 pixels
anyway (e.g. at this time it is 400 pixels wide) this "line" that joins
the points together isn't really much of a line—it's more like an
additional point interpolated between the two points, or maybe it's an
almost vertical line.

The thing is that we have only 200 points when the time series might
actually have hundreds of thousands or millions of points. So what we
actually do is divide the entire time range of the time series in 200
intervals; for each interval we calculate the max, min and mean value;
and we plot these three values (dark line for the mean, light line for
the min and max). For each point, y is therefore the mean, max or int
for the corresponding interval; and x is the center of the interval.

This explains why at high zoom levels the max, min and mean coincide.

This doesn't always work right. Precipitation, in particular, is
problematic because, except for high zoom levels, the max is so much
larger than the mean that the latter is plotted very near zero. But as a
quick overview it generally does its job.
