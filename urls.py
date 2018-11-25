from django.conf.urls import include, url
from django.contrib import admin

from ajax_select import urls as ajax_select_urls

from enhydris import urls as enhydris_urls
from enhydris.api import urls as enhydris_api_urls

admin.autodiscover()

urlpatterns = [
    url(r"^admin/", include(admin.site.urls)),
    url(r"^ajax/", include(ajax_select_urls)),
    url(r"^api/", include(enhydris_api_urls)),
    url(r"", include(enhydris_urls)),
]
