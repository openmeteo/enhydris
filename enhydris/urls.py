from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth.views import password_reset, password_reset_done
from django.conf import settings

from ajax_select import urls as ajax_select_urls
from captcha import urls as captcha_urls
from registration.backends.default import urls as registration_urls
from registration.backends.default.views import RegistrationView

from enhydris.api import urls as enhydris_api_urls
from enhydris.hcore import urls as enhydris_hcore_urls
from enhydris.hcore.forms import RegistrationForm
from enhydris.hcore.views import ProfileDetailView, ProfileEditView

admin.autodiscover()

urlpatterns = [
    url(r'^accounts/', include(registration_urls)),

    url(r'^profile/$', ProfileDetailView.as_view(),
        name='current_user_profile'),
    url(r'^profile/edit/$',
        ProfileEditView.as_view(),
        name='profile_edit'),
    url(r'^profile/(?P<slug>[^/]+)/$', ProfileDetailView.as_view(),
        name='profile_detail'),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^ajax/', include(ajax_select_urls)),
    url(r'^api/', include(enhydris_api_urls)),
    url(r'^captcha/', include(captcha_urls)),
    url(r'', include(enhydris_hcore_urls)),
]

if getattr(settings, 'REGISTRATION_OPEN', True):
    urlpatterns.insert(
        0, url(r'^accounts/register/$',
               RegistrationView.as_view(form_class=RegistrationForm),
               name='registration_register'))
