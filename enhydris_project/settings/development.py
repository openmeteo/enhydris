from . import *  # NOQA

DEBUG = True
INSTALLED_APPS.append("corsheaders")  # NOQA
MIDDLEWARE.insert(0, "corsheaders.middleware.CorsMiddleware")  # NOQA
CORS_ORIGIN_ALLOW_ALL = True
