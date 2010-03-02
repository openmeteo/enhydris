from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib.auth.views import password_reset, password_reset_done, password_change, password_change_done
from django.contrib import admin
from django.views.generic.simple import direct_to_template
from registration.views import register
from profiles.views import create_profile, edit_profile, profile_detail
from hydroscope.hcore.forms import HcoreRegistrationForm
from hydroscope.hcore.views import terms, profile_view

admin.autodiscover()

urlpatterns = patterns('',
    (r'^accounts/register/$', register, {'form_class':
        HcoreRegistrationForm}, 'registration_register'),
    (r'^accounts/', include('registration.urls')),
    (r'^accounts/password_reset/$', password_reset, {'template_name':
        'registration/password_reset.html'}),
    (r'^accounts/password_reset_done/$', password_reset_done,
        {'template_name': 'registration/password_reset_done.html'}),
    (r'^accounts/password_change/$', password_change, {'template_name':
        'registration/password_change.html'}),
    (r'^accounts/password_change_done/$', password_change_done,
        {'template_name': 'registration/password_change_done.html'}),


    # django profiles
    # to enable django <-> site admin overlapping
    #(r'^profiles/admin/(.*)', admin.site.root),
    #(r'^profile/', include('profiles.urls')),
    (r'^profile/create/$', create_profile, {}, 'profiles_create_profile'),
    (r'^profile/edit/$', edit_profile, {}, 'profiles_edit_profile'),
    (r'^profile/(?P<username>\w+)/$', profile_view, {},
                                 'profiles_profile_detail'),


    # contact form
    (r'^contact/$', include('hydroscope.contact.urls')),
    # terms of usage
    (r'^terms/$', terms),

    # internationalization
    (r'^i18n/', include('django.conf.urls.i18n')),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),
    (r'^grappelli/', include('grappelli.urls')),
    (r'^ajax/', include('ajax_select.urls')),
    (r'^api/', include('hydroscope.api.urls')),
    (r'', include('hydroscope.hcore.urls')),
)
