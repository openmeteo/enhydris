from django.conf.urls import url

from rest_framework import serializers
from rest_framework.generics import RetrieveAPIView
from rest_framework.urlpatterns import format_suffix_patterns

import enhydris.api.views as api_views
from enhydris.hcore import models

_urls = [url(r'^$', api_views.api_root),
         url(r'^tsdata/(?P<pk>\d+)/$', api_views.Tsdata.as_view(),
             name='tsdata')]
for _x in api_views.modelnames:
    model = models.__dict__[_x]
    if _x == 'Station':
        list_view = api_views.StationList.as_view()
        detail_view = api_views.StationDetail.as_view()
    elif _x == 'Timeseries':
        list_view = api_views.TimeseriesList.as_view()
        detail_view = api_views.TimeseriesDetail.as_view()
    else:
        class serializer(serializers.ModelSerializer):
            class Meta:
                model = model
                exclude = ()
        detail_view = RetrieveAPIView.as_view(queryset=model.objects.all(),
                                              serializer_class=serializer)
        list_view = api_views.ListAPIView.as_view(queryset=model.objects.all(),
                                        serializer_class=serializer)
    _urls.append(url(r'^{0}/$'.format(_x), list_view, name=_x + '-list'))
    _urls.append(url(r'^{0}/modified_after/(?P<modified_after>.*)/$'
                     .format(_x), list_view, name=_x + '-list'))
    _urls.append(url(r'^{0}/(?P<pk>\d+)/$'.format(_x), detail_view,
                     name=_x + '-detail'))

urlpatterns = format_suffix_patterns(_urls)
