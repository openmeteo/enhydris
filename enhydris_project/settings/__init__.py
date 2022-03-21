import os
import sys

# Development settings (to be overridden in production settings.py)
DEBUG = True
SECRET_KEY = "topsecret"
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "enhydris",
        "USER": "enhydris",
        "PASSWORD": "topsecret",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
SITE_ID = 1
STATIC_URL = "/static/"

ROOT_URLCONF = "enhydris.urls"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.humanize",
    "django.contrib.gis",
    "django.contrib.flatpages",
    "django.contrib.postgres",
    "rest_framework",
    "rest_framework.authtoken",
    "dj_rest_auth",
    "enhydris",
    "enhydris.telemetry",
    "enhydris.api",
    "django.contrib.admin",
    "rules.apps.AutodiscoverRulesConfig",
    "parler",
    "nested_admin",
    "crequest",
    "bootstrap4",
    #
    # Registration
    "registration",
    "captcha",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.contrib.flatpages.middleware.FlatpageFallbackMiddleware",
    "crequest.middleware.CrequestMiddleware",
]

APPEND_SLASH = True
USE_L10N = True

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "enhydris.context_processors.registration",
                "enhydris.context_processors.map",
            ]
        },
    }
]

LOGIN_REDIRECT_URL = "/"

ATOMIC_REQUESTS = True
TEST_RUNNER = "django.test.runner.DiscoverRunner"
USE_TZ = True

# By default, when uploading files, Django stores them in memory if they're small
# and to a temporary file if they're large. But we want to always use a file, because
# when the user uploads time series data we pass (a hard link to) the temporary file to
# a celery worker so that the processing happens offline.
# It would have been better to modify upload handlers for time series uploads only
# (see "Modifying upload handlers on the fly" in the Django documentation), but at the
# time of this writing this would be hard or impossible because that functionality is
# currently using the Django admin.
FILE_UPLOAD_HANDLERS = ["django.core.files.uploadhandler.TemporaryFileUploadHandler"]

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

AUTHENTICATION_BACKENDS = (
    "rules.permissions.ObjectPermissionBackend",
    "enhydris.auth.AuthBackend",
)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

ACCOUNT_ACTIVATION_DAYS = 1
REGISTRATION_OPEN = False

# For an explanation of the following, see
# https://github.com/mbi/django-simple-captcha/issues/84
CAPTCHA_TEST_MODE = len(sys.argv) > 1 and sys.argv[1] == "test"

ENHYDRIS_USERS_CAN_ADD_CONTENT = False
ENHYDRIS_OPEN_CONTENT = False

ENHYDRIS_MAP_BASE_LAYERS = {
    "Open Street Map": r"""
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: (
                'Map data © <a href="https://www.openstreetmap.org/">' +
                'OpenStreetMap</a> contributors, ' +
                '<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>'
            ),
            maxZoom: 18,
        })
    """,
    "Open Cycle Map": r"""
        L.tileLayer("https://{s}.tile.thunderforest.com/cycle/{z}/{x}/{y}.png", {
            attribution: (
                'Map data © <a href="https://www.openstreetmap.org/">' +
                'OpenStreetMap</a> contributors, ' +
                '<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>'
            ),
            maxZoom: 18,
        })
    """,
}
ENHYDRIS_MAP_DEFAULT_BASE_LAYER = "Open Street Map"
ENHYDRIS_MAP_MIN_VIEWPORT_SIZE = 0.04
ENHYDRIS_MAP_DEFAULT_VIEWPORT = (19.3, 34.75, 29.65, 41.8)
ENHYDRIS_TIMESERIES_DATA_DIR = "timeseries_data"
ENHYDRIS_TS_GRAPH_BIG_STEP_DENOMINATOR = 200
ENHYDRIS_TS_GRAPH_FINE_STEP_DENOMINATOR = 50
ENHYDRIS_SITES_FOR_NEW_STATIONS = set()
ENHYDRIS_CELERY_SEND_TASK_ERROR_EMAILS = True

CELERY_BEAT_SCHEDULE = {
    "fetch-telemetry-data": {
        "task": "enhydris.telemetry.tasks.fetch_all_telemetry_data",
        "schedule": 60,
    }
}

if os.environ.get("SELENIUM_BROWSER", False):
    from selenium import webdriver

    SELENIUM_WEBDRIVERS = {
        "default": {
            "callable": webdriver.__dict__[os.environ["SELENIUM_BROWSER"]],
            "args": (),
            "kwargs": {},
        }
    }

LANGUAGE_CODE = "en"
