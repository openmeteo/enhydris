from django.conf.urls.defaults import patterns

from enhydris.gis_objects import views
from enhydris.gis_objects.models import GISEntity

objects = {'queryset': GISEntity.objects.all(),
           'template_object_name': 'object',}

urlpatterns = patterns('',

    (r'^l/$',
     views.gis_objects_list, objects, 'gis_objects_list'),
    (r'^b/(?P<object_id>\d+)/$',
     views.gis_objects_brief, {}, 'gis_objects_brief'),
    (r'^d/(?P<object_id>\d+)/$',
     views.gis_objects_detail, {}, 'gis_objects_detail'),
    (r'^(?P<layer>[^/]+)/kml/$', views.kml, {}),
     
)
