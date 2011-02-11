USE_I18N = True

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.csrf.middleware.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django_notify.middleware.NotificationsMiddleware',
    'pagination.middleware.PaginationMiddleware',
    'django_sorting.middleware.SortingMiddleware',
)

ROOT_URLCONF = 'enhydris.urls'

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django_notify.context_processors.notifications',
)

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(sys.modules[__name__].__file__),
                                                        'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'grappelli',
    'django.contrib.admin',
    'django.contrib.sites',
    'django.contrib.humanize',
    'django.contrib.gis',

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

NOTIFICATIONS_STORAGE = 'session.SessionStorage'

AJAX_LOOKUP_CHANNELS = {
    'maintainers': dict(model='auth.User', search_field='username'),
}

LOGIN_REDIRECT_URL = '/'
AUTH_PROFILE_MODULE = 'hcore.UserProfile'
USE_OPEN_LAYERS = True 
