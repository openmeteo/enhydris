from django.conf.urls.defaults import include, patterns
from django.contrib import admin
from django.contrib.auth.views import password_reset, password_reset_done
from enhydris.hcore.views import terms

admin.autodiscover()

urlpatterns = patterns(
    '',

    (r'^accounts/password/reset/$', password_reset,
     {'template_name': 'registration/password_reset.html'}, 'password_reset'),
    (r'^accounts/password/reset/done/$', password_reset_done,
     {'template_name': 'registration/password_reset_done.html'},
     'password_reset_done'),
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
