from django.conf.urls.defaults import include, patterns
from django.contrib import admin
from enhydris.hcore.views import terms

admin.autodiscover()

urlpatterns = patterns(
    '',

    (r'^accounts/', include('registration.urls')),
    (r'^terms/$', terms, {}, 'terms'),
    (r'^i18n/', include('django.conf.urls.i18n')),
    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    (r'^grappelli/', include('grappelli.urls')),
    (r'^ajax/', include('ajax_select.urls')),
    (r'^api/', include('enhydris.api.urls')),
    (r'', include('enhydris.hcore.urls')),
)
