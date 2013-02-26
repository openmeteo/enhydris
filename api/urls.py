from django.conf.urls.defaults import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework import generics
from enhydris import models

_models = ('Lookup Lentity Person Organization Gentity Gpoint Gline Garea '
           'PoliticalDivisionManager PoliticalDivision WaterDivision '
           'WaterBasin GentityAltCodeType GentityAltCode FileType GentityFile '
           'EventType GentityEvent StationType StationManager Station Overseer '
           'InstrumentType Instrument Variable UnitOfMeasurement TimeZone '
           'TimeStep Timeseries').split()
_urls = ['enhydris.api.views', url(r'^$', 'api_root')]
for _x in _models:
    model = models.__dict__[_x]
    _urls.append(url(r'^{0}/$'.format(_x),
                     generics.ListAPIView.as_view(model=model)))
    _urls.append(url(r'^{0}/(?P<id>\d+)/$'.format(_x),
                     generics.RetrieveAPIView.as_view(model=model)))

urlpatterns = format_suffix_patterns(patterns(_urls))
