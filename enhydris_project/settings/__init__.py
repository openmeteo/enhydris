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
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.humanize",
    "django.contrib.gis",
    "django.contrib.flatpages",
    "rest_framework",
    "rest_framework.authtoken",
    "rest_auth",
    # Registration
    "allauth",
    "allauth.account",
    "rest_auth.registration",
    "rest_captcha",
    "enhydris",
    "enhydris.api",
    # enhydris overrides some templates from django.contrib.admin; for
    # this reason, it must be listed in INSTALLED_APPS before
    # django.contrib.admin.
    "django.contrib.admin",
    "rules.apps.AutodiscoverRulesConfig",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.contrib.flatpages.middleware.FlatpageFallbackMiddleware",
]

APPEND_SLASH = True

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
            ]
        },
    }
]

LOGIN_REDIRECT_URL = "/"

ATOMIC_REQUESTS = True
TEST_RUNNER = "django.test.runner.DiscoverRunner"
USE_TZ = True

AUTHENTICATION_BACKENDS = (
    "rules.permissions.ObjectPermissionBackend",
    "django.contrib.auth.backends.ModelBackend",
)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}
ACCOUNT_AUTHENTICATION_METHOD = "username"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
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

ENHYDRIS_REGISTRATION_OPEN = True
ENHYDRIS_USERS_CAN_ADD_CONTENT = False

ENHYDRIS_MIN_VIEWPORT_IN_DEGS = 0.04
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
