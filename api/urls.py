from django.conf.urls.defaults import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework import generics
from enhydris.hcore import models
from enhydris.api.views import modelnames
from enhydris.api import serializers

_urls = ['enhydris.api.views', url(r'^$', 'api_root')]
for _x in modelnames:
    model = models.__dict__[_x]
    serializer_class = serializers.StationSerializer if _x=='Station' else None
    _urls.append(url(r'^{0}/$'.format(_x),
                     generics.ListAPIView.as_view(
                            model=model, serializer_class=serializer_class),
                     name=_x+'-list'))
    _urls.append(url(r'^{0}/(?P<pk>\d+)/$'.format(_x),
                     generics.RetrieveAPIView.as_view(
                            model=model, serializer_class=serializer_class),
                     name=_x+'-detail'))

urlpatterns = format_suffix_patterns(patterns(*_urls))
