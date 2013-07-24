from django.conf.urls.defaults import patterns

from enhydris.contourplot import views

urlpatterns = patterns('',

    (r'^(?P<urlcode>[^/]+)/$',
     views.contourpage_detail, {}, 'contourpage_detail'),
    (r'^images/(?P<imgurl>[^/]+)$',
     views.image_serve, {}, 'image_serve'),
    (r'^thumbs/(?P<imgurl>[^/]+)$',
     views.thumb_serve, {}, 'thumb_serve'),
    (r'^last/(?P<urlcode>[^/]+)/$',
     views.last_update, {}, 'last_update'),
     
)
