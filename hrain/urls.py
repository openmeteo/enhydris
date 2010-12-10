from django.conf.urls.defaults import patterns

from enhydris.hrain import views

urlpatterns = patterns('',
    (r'^$', views.index, {}, 'index'),
)
