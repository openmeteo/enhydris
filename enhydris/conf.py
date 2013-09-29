import tempfile
import os.path

# We do want to import settings, even if apparently we don't use it,
# so that others can import settings from here. The useless "assert
# settings" statement serves only to fool lint checkers.

from django.conf import settings
assert settings

from appconf import AppConf


class EnhydrisConf(AppConf):

    FILTER_DEFAULT_COUNTRY = None
    FILTER_POLITICAL_SUBDIVISION1_NAME = None
    FILTER_POLITICAL_SUBDIVISION2_NAME = None
    USERS_CAN_ADD_CONTENT = False
    SITE_CONTENT_IS_FREE = False
    TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS = False
    STORE_TSDATA_LOCALLY = True
    REMOTE_INSTANCE_CREDENTIALS = {}
    USE_OPEN_LAYERS = True
    MIN_VIEWPORT_IN_DEGS = 0.04
    MAP_DEFAULT_VIEWPORT = (19.3, 34.75, 29.65, 41.8)
    TS_GRAPH_CACHE_DIR = os.path.join(tempfile.gettempdir(),
                                      'enhydris-timeseries-graphs')
    TS_GRAPH_BIG_STEP_DENOMINATOR = 200
    TS_GRAPH_FINE_STEP_DENOMINATOR = 50
    SITE_STATION_FILTER = {}
    DISPLAY_COPYRIGHT_INFO = False
    WGS84_NAME = 'WGS84'

    class Meta:
        prefix = 'ENHYDRIS'
