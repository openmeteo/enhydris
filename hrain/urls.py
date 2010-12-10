from django.conf.urls.defaults import patterns

from enhydris.hrain import views

urlpatterns = patterns('',
    (r'^$', views.index, {}, 'index'),
    (r'^event/(\d+)-(\d+)-(\d+)T(\d+):(\d+)/', views.event, {}, 'event'),
)
