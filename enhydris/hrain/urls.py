from django.conf.urls import patterns

from enhydris.hrain import views

urlpatterns = patterns('',
    (r'^$', views.index, {}, 'index'),
    (r'^event/(-?\d+)/', views.event, {}, 'event'),
)
