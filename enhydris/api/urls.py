from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.generics import RetrieveAPIView
from enhydris.hcore import models
from enhydris.api.views import modelnames, TimeseriesList, TimeseriesDetail,\
    Tsdata, ListAPIView, StationList, StationDetail

_urls = ['enhydris.api.views',
         url(r'^$', 'api_root'),
         url(r'^tsdata/(?P<pk>\d+)/$', Tsdata.as_view(), name='tsdata')]
for _x in modelnames:
    model = models.__dict__[_x]
    if _x == 'Station':
        list_view = StationList.as_view()
        detail_view = StationDetail.as_view()
    elif _x == 'Timeseries':
        list_view = TimeseriesList.as_view()
        detail_view = TimeseriesDetail.as_view()
    else:
        detail_view = RetrieveAPIView.as_view(model=model)
        list_view = ListAPIView.as_view(model=model)
    _urls.append(url(r'^{0}/$'.format(_x), list_view, name=_x + '-list'))
    _urls.append(url(r'^{0}/modified_after/(?P<modified_after>.*)/$'
                     .format(_x), list_view, name=_x + '-list'))
    _urls.append(url(r'^{0}/(?P<pk>\d+)/$'.format(_x), detail_view,
                     name=_x + '-detail'))

urlpatterns = format_suffix_patterns(patterns(*_urls))
