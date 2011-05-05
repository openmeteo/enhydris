from django.conf.urls.defaults import patterns

from enhydris.contourplot import views

urlpatterns = patterns('',

    (r'^contours/(?P<urlcode>[^/]+)/$',
     views.contourpage_detail, {}, 'contourpage_detail'),
    (r'^contours/images/(?P<imgurl>[^/]+)$',
     views.image_serve, {}, 'image_serve'),
     
)
