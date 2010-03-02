from django.conf import settings
from django.conf.urls.defaults import *
from hydroscope.contact import views

urlpatterns = patterns('',
    (r'^$', views.contactview, {}, 'contact_form'),
)
