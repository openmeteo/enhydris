import shutil
import tempfile

from django.test import override_settings


class RandomEnhydrisTimeseriesDataDir(override_settings):
    """
    Override ENHYDRIS_TIMESERIES_DATA_DIR to a temporary directory.

    Specifying "@RandomEnhydrisTimeseriesDataDir()" as a decorator is the same
    as "@override_settings(ENHYDRIS_TIMESERIES_DATA_DIR=tempfile.mkdtemp())",
    except that in the end it removes the temporary directory.
    """

    def __init__(self):
        self.tmpdir = tempfile.mkdtemp()
        super(RandomEnhydrisTimeseriesDataDir, self).__init__(
            ENHYDRIS_TIMESERIES_DATA_DIR=self.tmpdir
        )

    def disable(self):
        super(RandomEnhydrisTimeseriesDataDir, self).disable()
        shutil.rmtree(self.tmpdir)
