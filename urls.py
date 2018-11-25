from django.conf.urls import include, url
from django.contrib import admin

from enhydris import urls as enhydris_urls
from enhydris.api import urls as enhydris_api_urls

admin.autodiscover()

urlpatterns = [
    url(r"^admin/", include(admin.site.urls)),
    url(r"^api/", include(enhydris_api_urls)),
    url(r"", include(enhydris_urls)),
]
