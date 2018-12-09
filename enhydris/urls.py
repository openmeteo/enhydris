from django.conf.urls import include, url
from django.contrib import admin

from enhydris.api import urls as enhydris_api_urls

admin.autodiscover()

urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url(r"^api/", include(enhydris_api_urls)),
]
