DEBUG = True
TEMPLATE_DEBUG = False

ROOT_URLCONF = 'enhydris.urls'

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES =  {
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

# Options for django-registration
ACCOUNT_ACTIVATION_DAYS = 7
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST = 'smtp.my.domain'
DEFAULT_FROM_EMAIL = 'user@host.domain'
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_HOST_USER = 'automaticsender@my.domain'
EMAIL_HOST_PASSWORD = 'mypassword'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.contrib.markup',
    'django.contrib.admin',
    'django.contrib.sites',
    'django.contrib.humanize',
    'django.contrib.gis',

    'rest_framework',
    'south',
    'enhydris.sorting',
    'registration',
    'profiles',
    'ajax_select',
    'captcha',
    'django_tables2',

    'enhydris.dbsync',
    'enhydris.hcore',
    'enhydris.hprocessor',
    'enhydris.hchartpages',
    'enhydris.api',
    'enhydris.permissions',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django_notify.middleware.NotificationsMiddleware',
    'enhydris.sorting.middleware.SortingMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

APPEND_SLASH = True

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.request',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'django_notify.context_processors.notifications',
)

TEMPLATE_DIRS = ('enhydris/templates',)

AUTH_PROFILE_MODULE = 'hcore.UserProfile'
LOGIN_REDIRECT_URL = '/'
