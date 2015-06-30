from enhydris.settings.base import *

DEBUG = True
TEMPLATE_DEBUG = False
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
# Make this unique, and don't share it with anybody.
SECRET_KEY = 'yy)g)w2jqkpyv9$w39i9$7(6wb+$h(_+x3gj#=@fzs2tmuj$#='
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST = 'smtp.my.domain'
DEFAULT_FROM_EMAIL = 'user@host.domain'
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_HOST_USER = 'automaticsender@my.domain'
EMAIL_HOST_PASSWORD = 'mypassword'


ROOT_URLCONF = 'enhydris.urls'
