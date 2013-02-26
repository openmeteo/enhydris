from django.conf.urls.defaults import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.generics import RetrieveAPIView, ListAPIView
from enhydris.hcore import models
from enhydris.api.views import modelnames, TimeseriesList, TimeseriesDetail
from enhydris.api import serializers

_urls = ['enhydris.api.views', url(r'^$', 'api_root')]
for _x in modelnames:
    model = models.__dict__[_x]
    serializer_class = None
    if _x == 'Station':
        serializer_class = serializers.StationSerializer
    detail_view = RetrieveAPIView.as_view(model=model,
                                          serializer_class=serializer_class)
    list_view = ListAPIView.as_view(model=model,
                                    serializer_class=serializer_class)
    if _x == 'Timeseries':
        list_view = TimeseriesList.as_view()
        detail_view = TimeseriesDetail.as_view()
    _urls.append(url(r'^{0}/$'.format(_x), list_view, name=_x+'-list'))
    _urls.append(url(r'^{0}/(?P<pk>\d+)/$'.format(_x), detail_view,
                     name=_x+'-detail'))

urlpatterns = format_suffix_patterns(patterns(*_urls))
