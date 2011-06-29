from django.conf.urls.defaults import patterns

from enhydris.hfaq import views

urlpatterns = patterns('',

    (r'^$', 
     views.faqpage_detail, {}, 'faqpage_detail'),
     
)
