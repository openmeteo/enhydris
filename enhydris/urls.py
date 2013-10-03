from django.conf.urls import url, include, patterns
from django.contrib import admin
from django.contrib.auth.views import password_reset, password_reset_done
from django.conf import settings

from registration.views import RegistrationView
import profiles

from enhydris.hcore.views import terms
from enhydris.hcore.forms import RegistrationForm

admin.autodiscover()

urlpatterns = patterns(
    '',

    # Django-registration and django-profiles
    (r'^accounts/password/reset/$', password_reset,
     {'template_name': 'registration/password_reset.html'}, 'password_reset'),
    (r'^accounts/password/reset/done/$', password_reset_done,
     {'template_name': 'registration/password_reset_done.html'},
     'password_reset_done'),
    (r'^accounts/', include('registration.backends.default.urls')),
    (r'^profile/', include('profiles.urls')),

    (r'^terms/$', terms, {}, 'terms'),
    (r'^i18n/', include('django.conf.urls.i18n')),
    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    (r'^ajax/', include('ajax_select.urls')),
    (r'^api/', include('enhydris.api.urls')),
    (r'^captcha/', include('captcha.urls')),
    (r'', include('enhydris.hcore.urls')),
)

if getattr(settings, 'REGISTRATION_OPEN', True):
    urlpatterns = patterns(
        '',
        url(r'^accounts/register/$',
            RegistrationView.as_view(form_class=RegistrationForm),
            name='registration_register')) + urlpatterns
