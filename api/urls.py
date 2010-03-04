from django.conf.urls.defaults import *
from piston.resource import Resource
from piston.emitters import Emitter
from enhydris.api.authentication import RemoteInstanceAuthentication
from enhydris.api.handlers import *
from enhydris.api.emitters import CFEmitter, TSEmitter

# JSON emitter for sync db process
Emitter.register('json', CFEmitter, 'application/json; charset=utf-8')
# hts emitter for remote hts file downloading (incl. http authentication)
Emitter.register('hts', TSEmitter, 'text/vnd.openmeteo.timeseries;charset=iso-8859-7')
auth = RemoteInstanceAuthentication(realm="Timeseries realm")

# Used for gis
station_handler = Resource(StationHandler)
station_list_handler = Resource(StationListHandler)

# Used for db sync
Lookup_Resource = Resource(Lookup_Handler)
Lentity_Resource = Resource(Lentity_Handler)
Person_Resource = Resource(Person_Handler)
Organization_Resource = Resource(Organization_Handler)
Gentity_Resource = Resource(Gentity_Handler)
Gpoint_Resource = Resource(Gpoint_Handler)
Gline_Resource = Resource(Gline_Handler)
Garea_Resource = Resource(Garea_Handler)
PoliticalDivisionManager_Resource = Resource(PoliticalDivisionManager_Handler)
PoliticalDivision_Resource = Resource(PoliticalDivision_Handler)
WaterDivision_Resource = Resource(WaterDivision_Handler)
WaterBasin_Resource = Resource(WaterBasin_Handler)
GentityAltCodeType_Resource = Resource(GentityAltCodeType_Handler)
GentityAltCode_Resource = Resource(GentityAltCode_Handler)
FileType_Resource = Resource(FileType_Handler)
GentityFile_Resource = Resource(GentityFile_Handler)
EventType_Resource = Resource(EventType_Handler)
GentityEvent_Resource = Resource(GentityEvent_Handler)
StationType_Resource = Resource(StationType_Handler)
StationManager_Resource = Resource(StationManager_Handler)
Station_Resource = Resource(Station_Handler)
Overseer_Resource = Resource(Overseer_Handler)
InstrumentType_Resource = Resource(InstrumentType_Handler)
Instrument_Resource = Resource(Instrument_Handler)
Variable_Resource = Resource(Variable_Handler)
UnitOfMeasurement_Resource = Resource(UnitOfMeasurement_Handler)
TimeZone_Resource = Resource(TimeZone_Handler)
TimeStep_Resource = Resource(TimeStep_Handler)
Timeseries_Resource = Resource(Timeseries_Handler)

# Used for timeseries data
TSDATA_Resource = Resource(handler=TSDATA_Handler, authentication=auth)

# urls
urlpatterns = patterns('',
   url(r'^station/(?P<station_id>\d+)/', station_handler),
   url(r'^station_list/', station_list_handler),
    url(r'^Lookup/$', Lookup_Resource),
    url(r'^Lentity/$', Lentity_Resource),
    url(r'^Person/$', Person_Resource),
    url(r'^Organization/$', Organization_Resource),
    url(r'^Gentity/$', Gentity_Resource),
    url(r'^Gpoint/$', Gpoint_Resource),
    url(r'^Gline/$', Gline_Resource),
    url(r'^Garea/$', Garea_Resource),
    url(r'^PoliticalDivisionManager/$', PoliticalDivisionManager_Resource),
    url(r'^PoliticalDivision/$', PoliticalDivision_Resource),
    url(r'^WaterDivision/$', WaterDivision_Resource),
    url(r'^WaterBasin/$', WaterBasin_Resource),
    url(r'^GentityAltCodeType/$', GentityAltCodeType_Resource),
    url(r'^GentityAltCode/$', GentityAltCode_Resource),
    url(r'^FileType/$', FileType_Resource),
    url(r'^GentityFile/$', GentityFile_Resource),
    url(r'^EventType/$', EventType_Resource),
    url(r'^GentityEvent/$', GentityEvent_Resource),
    url(r'^StationType/$', StationType_Resource),
    url(r'^StationManager/$', StationManager_Resource),
    url(r'^Station/$', Station_Resource),
    url(r'^Overseer/$', Overseer_Resource),
    url(r'^InstrumentType/$', InstrumentType_Resource),
    url(r'^Instrument/$', Instrument_Resource),
    url(r'^Variable/$', Variable_Resource),
    url(r'^UnitOfMeasurement/$', UnitOfMeasurement_Resource),
    url(r'^TimeZone/$', TimeZone_Resource),
    url(r'^TimeStep/$', TimeStep_Resource),
    url(r'^Timeseries/$', Timeseries_Resource),
    url(r'^tsdata/(?P<ts_id>\d+)/$', TSDATA_Resource, {'emitter_format': 'hts'} ),
)
