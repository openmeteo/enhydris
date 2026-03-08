from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions

from . import *  # NOQA

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "openmeteo",
        "USER": "runner",
        "PASSWORD": "topsecret",
        "HOST": "localhost",
        "PORT": 5432,
    }
}
LANGUAGE_CODE = "en"
LANGUAGES = {
    ("en", "English"),
    ("el", "Ελληνικά"),
}

headless = ChromeOptions()
headless.add_argument("--headless")

SELENIUM_WEBDRIVERS = {
    "default": {
        "callable": webdriver.Chrome,
        "args": [],
        "kwargs": {"options": headless},
    },
}
