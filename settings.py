# Django settings for enhydris project.
# coding=UTF-8
import sys
import os.path
from django.utils.translation import ugettext_lazy as _

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))

DEBUG = True
TEMPLATE_DEBUG = False
STATIC_SERVE = True

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
    ('Seraphim Mellos', 'mellos@indifex.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'postgresql_psycopg2'
DATABASE_NAME = 'hydrotest'
DATABASE_USER = 'hydro'
DATABASE_PASSWORD = 'f@nt@'
DATABASE_HOST = 'localhost'
DATABASE_PORT = ''

#AUTHENTICATION_BACKENDS = ('ldap_auth.LDAPBackend',
#                           'django.contrib.auth.backends.ModelBackend')

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Athens'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# This is from django-multilingual
LANGUAGES = (
    ('en', u'English'),
    ('el', u'Ελληνικά'),
)
DEFAULT_LANGUAGE = 1

SITE_ID = 1
SITE_URL = "hydroscope.gr"

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_PATH, 'site_media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/site_media/'

# Capthca options
CAPTCHA_ROOT=os.path.join(PROJECT_PATH, 'site_media/captchas/')
CAPTCHA_FONT=os.path.join(PROJECT_PATH, 'site_media/arizona.ttf')


# Options for django-notify
NOTIFICATIONS_STORAGE = 'session.SessionStorage'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Grappelli title
GRAPPELLI_ADMIN_TITLE = 'Enhydris Administration'

# The URL where requests are redirected after login when the
# contrib.auth.login view gets no next parameter.
LOGIN_REDIRECT_URL = '/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'yy)g)w2jqkpyv9$w39i9$7(6wb+$h(_+x3gj#=@fzs2tmuj$#='

# Django profile
AUTH_PROFILE_MODULE = 'hcore.UserProfile'

# Session Timeout
SESSION_COOKIE_AGE=3600
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# GentityFile upload directory (must be relative path and it'll be created
# under site_media dir)
GENTITYFILE_DIR = 'gentityfile'

# GIS Configuration
GIS_SERVER="147.102.160.29"

# Options for django-registration
ACCOUNT_ACTIVATION_DAYS=7
EMAIL_USE_TLS = True
EMAIL_HOST='smtp.gmail.com'
EMAIL_HOST_USER='hydroscope.noreply@gmail.com'
EMAIL_HOST_PASSWORD='f@nt@st!c'
EMAIL_PORT=587


# Options for political divisions
FILTER_DEFAULT_COUNTRY= 'GREECE'
FILTER_POLITICAL_SUBDIVISION1_NAME= _('District')
FILTER_POLITICAL_SUBDIVISION2_NAME= _('Prefecture')

# Options for site content
USERS_CAN_ADD_CONTENT=False
SITE_CONTENT_IS_FREE=False
TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS=False

# Options for timeseries data
# If this is set to false then users cannot upload timeseries data to this
# instance and can ogly view existing data. Also, in order to download the
# data, the REMOTE_INSTANCE_CREDENTIALS should be set for the instance that all
# the data came from.
STORE_TSDATA_LOCALLY=True

# Domain-specific credentials for instance authentication.
# Used primarily when the 'STORE_TSDATA_LOCALLY=False' in order to pull
# timeseries data from the originating hydroscope instance using
# username/password authentication. The user credentials must belong to a
# superuser.
#
# For example to be able to pull from kyy.hydroscope.gr define:
#REMOTE_INSTANCE_CREDENTIALS = {'kyy.hydroscope.gr': ('myusername', 'mypassword')}


# Options for ajax selects
AJAX_LOOKUP_CHANNELS = {
    'maintainers': dict(model='auth.User', search_field='username'),
}


# Django context processors
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django_notify.context_processors.notifications',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#   'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django_notify.middleware.NotificationsMiddleware',
    'pagination.middleware.PaginationMiddleware',
    'django_sorting.middleware.SortingMiddleware',
)

ROOT_URLCONF = 'enhydris.urls'

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(sys.modules[__name__].__file__), 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'grappelli',
    'django.contrib.admin',
    'django.contrib.sites',
    'django.contrib.humanize',

    # Debugging Apps
    'django_extensions',
    'piston',

    # Dependencies
    'south',
    'pagination',
    'django_sorting',
    'profiles',
    'registration',
    'ajax_select',

    # Hydroscope Apps
    'enhydris.dbsync',
    'enhydris.hcore',
    'enhydris.contact',
    'enhydris.api',
    'enhydris.permissions',
)
