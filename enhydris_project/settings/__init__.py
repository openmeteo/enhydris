import os

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
    "rest_auth",
    "bootstrap3",
    # Registration
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "rest_auth.registration",
    "rest_captcha",
    "enhydris",
    "enhydris.api",
    "django.contrib.admin",
    "rules.apps.AutodiscoverRulesConfig",
    "parler",
    "nested_admin",
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

USE_L10N = True

AUTHENTICATION_BACKENDS = (
    "rules.permissions.ObjectPermissionBackend",
    "django.contrib.auth.backends.ModelBackend",
)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}
ACCOUNT_AUTHENTICATION_METHOD = "username"
REST_AUTH_REGISTER_SERIALIZERS = {
    "REGISTER_SERIALIZER": (
        "enhydris.api.serializers_captcha.RegisterWithCaptchaSerializer"
    )
}
OLD_PASSWORD_FIELD_ENABLED = True

# Default Enhydris settings
ENHYDRIS_FILTER_DEFAULT_COUNTRY = None
ENHYDRIS_FILTER_POLITICAL_SUBDIVISION1_NAME = None
ENHYDRIS_FILTER_POLITICAL_SUBDIVISION2_NAME = None

ENHYDRIS_REGISTRATION_OPEN = False
ACCOUNT_EMAIL_REQUIRED = ENHYDRIS_REGISTRATION_OPEN
ACCOUNT_EMAIL_VERIFICATION = ENHYDRIS_REGISTRATION_OPEN and "mandatory" or "optional"
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
ENHYDRIS_MAP_MARKERS = {"0": "images/drop_marker.png"}
ENHYDRIS_MAP_MIN_VIEWPORT_SIZE = 0.04
ENHYDRIS_MAP_DEFAULT_VIEWPORT = (19.3, 34.75, 29.65, 41.8)
ENHYDRIS_TIMESERIES_DATA_DIR = "timeseries_data"
ENHYDRIS_TS_GRAPH_BIG_STEP_DENOMINATOR = 200
ENHYDRIS_TS_GRAPH_FINE_STEP_DENOMINATOR = 50
ENHYDRIS_SITE_STATION_FILTER = {}
ENHYDRIS_DISPLAY_COPYRIGHT_INFO = False

if os.environ.get("SELENIUM_BROWSER", False):
    from selenium import webdriver

    SELENIUM_WEBDRIVERS = {
        "default": {
            "callable": webdriver.__dict__[os.environ["SELENIUM_BROWSER"]],
            "args": (),
            "kwargs": {},
        }
    }
