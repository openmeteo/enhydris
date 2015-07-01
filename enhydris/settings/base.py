ROOT_URLCONF = 'enhydris.urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',
    'django.contrib.gis',
    'django.contrib.flatpages',

    'rest_framework',
    'registration',
    'ajax_select',
    'captcha',
    'bootstrap3',

    'enhydris.hcore',
    'enhydris.api',
    'enhydris.permissions',

    # enhydris.hcore overrides some templates from django.contrib.admin; for
    # this reason, it must be listed in INSTALLED_APPS before
    # django.contrib.admin.
    'django.contrib.admin',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
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
    'enhydris.hcore.context_processors.registration',
    'enhydris.hcore.context_processors.map',
)

AUTH_PROFILE_MODULE = 'hcore.UserProfile'
LOGIN_REDIRECT_URL = '/'

ATOMIC_REQUESTS = True
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Options for django-registration
ACCOUNT_ACTIVATION_DAYS = 7
REGISTRATION_OPEN = True
