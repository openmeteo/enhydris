from enhydris.settings.base import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG
ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)
MANAGERS = ADMINS
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'openmeteo',
        'USER': 'openmeteo',
        'PASSWORD': 'openmeteo',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
TIME_ZONE = 'Europe/Athens'
SITE_ID = 1
SITE_URL = "hydroscope.gr"
MEDIA_ROOT = '/tmp'
MEDIA_URL = '/site_media/'
STATIC_ROOT = 'static/'
STATIC_URL = '/enhydris-static/'
SECRET_KEY = 'irrelevant'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST = 'smtp.my.domain'
DEFAULT_FROM_EMAIL = 'user@host.domain'
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_HOST_USER = 'automaticsender@my.domain'
EMAIL_HOST_PASSWORD = 'mypassword'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

ROOT_URLCONF = 'enhydris.urls'
