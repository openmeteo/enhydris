from . import *  # NOQA

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "openmeteo",
        "USER": "postgres",
        "PASSWORD": "",
        "HOST": "localhost",
        "PORT": 5432,
    }
}
LANGUAGE_CODE = "en"
LANGUAGES = {
    ("en", "English"),
    ("el", "Ελληνικά"),
}
PARLER_LANGUAGES = {
    SITE_ID: [{"code": LANGUAGE_CODE}, {"code": "el"}],  # NOQA
    "default": {"fallbacks": ["en"], "hide_untranslated": True},
}
