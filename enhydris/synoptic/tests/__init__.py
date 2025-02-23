import matplotlib.dates

# In matplotlib 3.3, the default date epoch changed from 0000-12-31 to 1970-01-01. When
# testing, we want to use the same epoch regardless the matplotlib version, because some
# tests (namely tests.test_tasks.ChartTestCase) check the data provided to matplotlib to
# verify that the chart is correct, and matplotlib provides the dates in
# days-since-epoch format.
if hasattr(matplotlib.dates, "set_epoch"):
    matplotlib.dates.set_epoch("0000-12-31T00:00")
