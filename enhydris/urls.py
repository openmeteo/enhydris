from django.conf.urls import url, include, patterns
from django.contrib import admin
from django.contrib.auth.views import password_reset, password_reset_done
from django.conf import settings

from registration.backends.default.views import RegistrationView

from enhydris.hcore.forms import RegistrationForm
from enhydris.hcore.views import ProfileDetailView, ProfileEditView

admin.autodiscover()

urlpatterns = patterns(
    '',

    # Registration and profiles
    (r'^accounts/password/reset/$', password_reset,
     {'template_name': 'registration/password_reset.html'}, 'password_reset'),
    (r'^accounts/password/reset/done/$', password_reset_done,
     {'template_name': 'registration/password_reset_done.html'},
     'password_reset_done'),
    (r'^accounts/', include('registration.backends.default.urls')),

    url(r'^profile/$', ProfileDetailView.as_view(),
        name='current_user_profile'),
    url(r'^profile/edit/$',
        ProfileEditView.as_view(),
        name='profile_edit'),
    url(r'^profile/(?P<slug>[^/]+)/$', ProfileDetailView.as_view(),
        name='profile_detail'),

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
