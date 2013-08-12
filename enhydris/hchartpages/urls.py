from django.conf.urls import patterns

from enhydris.hchartpages import views

urlpatterns = patterns('',

    (r'^(?P<url_id>\d+)/$', 
     views.url_redir, {}, 'url_redir'),
    (r'^(?P<urlcode>[^/]+)/$',
     views.chartpage_detail, {}, 'chartpage_detail'),
     
)
