from django.conf.urls.defaults import patterns, url
from piston.resource import Resource
from piston.emitters import Emitter, JSONEmitter
from enhydris.api.authentication import RemoteInstanceAuthentication
from enhydris.api import handlers
from enhydris.api.emitters import CFEmitter, PlainEmitter, GFEmitter

# Default JSON emitter
Emitter.register('default', JSONEmitter, 'application/json; charset=utf-8')
# JSON emitter for sync db process
Emitter.register('json', CFEmitter, 'application/json; charset=utf-8')
# Emitter for gfd (aka GenityFileData)
Emitter.register('gfd', GFEmitter )
gf_auth = RemoteInstanceAuthentication(realm="GentityFile realm")
# Plain emitter
Emitter.register('plain', PlainEmitter, 'text/plain; charset=utf-8')

# Used for gis
station_handler = Resource(handlers.StationHandler)
station_list_handler = Resource(handlers.StationListHandler)

# Used for db sync
Lookup_Resource = Resource(handlers.Lookup_Handler)
Lentity_Resource = Resource(handlers.Lentity_Handler)
Person_Resource = Resource(handlers.Person_Handler)
Organization_Resource = Resource(handlers.Organization_Handler)
Gentity_Resource = Resource(handlers.Gentity_Handler)
Gpoint_Resource = Resource(handlers.Gpoint_Handler)
Gline_Resource = Resource(handlers.Gline_Handler)
Garea_Resource = Resource(handlers.Garea_Handler)
PoliticalDivisionManager_Resource = Resource(
                                    handlers.PoliticalDivisionManager_Handler)
PoliticalDivision_Resource = Resource(handlers.PoliticalDivision_Handler)
WaterDivision_Resource = Resource(handlers.WaterDivision_Handler)
WaterBasin_Resource = Resource(handlers.WaterBasin_Handler)
GentityAltCodeType_Resource = Resource(handlers.GentityAltCodeType_Handler)
GentityAltCode_Resource = Resource(handlers.GentityAltCode_Handler)
FileType_Resource = Resource(handlers.FileType_Handler)
GentityFile_Resource = Resource(handlers.GentityFile_Handler)
EventType_Resource = Resource(handlers.EventType_Handler)
GentityEvent_Resource = Resource(handlers.GentityEvent_Handler)
StationType_Resource = Resource(handlers.StationType_Handler)
StationManager_Resource = Resource(handlers.StationManager_Handler)
Station_Resource = Resource(handlers.Station_Handler)
Overseer_Resource = Resource(handlers.Overseer_Handler)
InstrumentType_Resource = Resource(handlers.InstrumentType_Handler)
Instrument_Resource = Resource(handlers.Instrument_Handler)
Variable_Resource = Resource(handlers.Variable_Handler)
UnitOfMeasurement_Resource = Resource(handlers.UnitOfMeasurement_Handler)
TimeZone_Resource = Resource(handlers.TimeZone_Handler)
TimeStep_Resource = Resource(handlers.TimeStep_Handler)
Timeseries_Resource = Resource(handlers.Timeseries_Handler)

# Used for timeseries data
TSDATA_Resource = Resource(handler=handlers.TSDATA_Handler)
GFDATA_Resource = Resource(handler=handlers.GFDATA_Handler,
                                                    authentication=gf_auth)

# urls
urlpatterns = patterns('',
    url(r'^Lookup/$', Lookup_Resource),
    url(r'^Lookup/(?P<id>\d+)/$', Lookup_Resource),
    url(r'^Lookup/date/(?P<date>.*)/$', Lookup_Resource),
    url(r'^Lentity/$', Lentity_Resource),
    url(r'^Lentity/(?P<id>\d+)/$', Lentity_Resource),
    url(r'^Lentity/date/(?P<date>.*)/$', Lentity_Resource),
    url(r'^Person/$', Person_Resource),
    url(r'^Person/(?P<id>\d+)/$', Person_Resource),
    url(r'^Person/date/(?P<date>.*)/$', Person_Resource),
    url(r'^Organization/$', Organization_Resource),
    url(r'^Organization/(?P<id>\d+)/$', Organization_Resource),
    url(r'^Organization/date/(?P<date>.*)/$', Organization_Resource),
    url(r'^Gentity/$', Gentity_Resource),
    url(r'^Gentity/(?P<id>\d+)/$', Gentity_Resource),
    url(r'^Gentity/date/(?P<date>.*)/$', Gentity_Resource),
    url(r'^Gpoint/$', Gpoint_Resource),
    url(r'^Gpoint/(?P<id>\d+)/$', Gpoint_Resource),
    url(r'^Gpoint/date/(?P<date>.*)/$', Gpoint_Resource),
    url(r'^Gline/$', Gline_Resource),
    url(r'^Gline/(?P<id>\d+)/$', Gline_Resource),
    url(r'^Gline/date/(?P<date>.*)/$', Gline_Resource),
    url(r'^Garea/$', Garea_Resource),
    url(r'^Garea/(?P<id>\d+)/$', Garea_Resource),
    url(r'^Garea/date/(?P<date>.*)/$', Garea_Resource),
    url(r'^PoliticalDivisionManager/$', PoliticalDivisionManager_Resource),
    url(r'^PoliticalDivisionManager/(?P<id>\d+)/$', PoliticalDivisionManager_Resource),
    url(r'^PoliticalDivisionManager/date/(?P<date>.*)/$', PoliticalDivisionManager_Resource),
    url(r'^PoliticalDivision/$', PoliticalDivision_Resource),
    url(r'^PoliticalDivision/(?P<id>\d+)/$', PoliticalDivision_Resource),
    url(r'^PoliticalDivision/date/(?P<date>.*)/$', PoliticalDivision_Resource),
    url(r'^WaterDivision/$', WaterDivision_Resource),
    url(r'^WaterDivision/(?P<id>\d+)/$', WaterDivision_Resource),
    url(r'^WaterDivision/date/(?P<date>.*)/$', WaterDivision_Resource),
    url(r'^WaterBasin/$', WaterBasin_Resource),
    url(r'^WaterBasin/(?P<id>\d+)/$', WaterBasin_Resource),
    url(r'^WaterBasin/date/(?P<date>.*)/$', WaterBasin_Resource),
    url(r'^GentityAltCodeType/$', GentityAltCodeType_Resource),
    url(r'^GentityAltCodeType/(?P<id>\d+)/$', GentityAltCodeType_Resource),
    url(r'^GentityAltCodeType/date/(?P<date>.*)/$', GentityAltCodeType_Resource),
    url(r'^GentityAltCode/$', GentityAltCode_Resource),
    url(r'^GentityAltCode/(?P<id>\d+)/$', GentityAltCode_Resource),
    url(r'^GentityAltCode/date/(?P<date>.*)/$', GentityAltCode_Resource),
    url(r'^FileType/$', FileType_Resource),
    url(r'^FileType/(?P<id>\d+)/$', FileType_Resource),
    url(r'^FileType/date/(?P<date>.*)/$', FileType_Resource),
    url(r'^GentityFile/$', GentityFile_Resource),
    url(r'^GentityFile/(?P<id>\d+)/$', GentityFile_Resource),
    url(r'^GentityFile/date/(?P<date>.*)/$', GentityFile_Resource),
    url(r'^EventType/$', EventType_Resource),
    url(r'^EventType/(?P<id>\d+)/$', EventType_Resource),
    url(r'^EventType/date/(?P<date>.*)/$', EventType_Resource),
    url(r'^GentityEvent/$', GentityEvent_Resource),
    url(r'^GentityEvent/(?P<id>\d+)/$', GentityEvent_Resource),
    url(r'^GentityEvent/date/(?P<date>.*)/$', Gentity_Resource),
    url(r'^StationType/$', StationType_Resource),
    url(r'^StationType/(?P<id>\d+)/$', StationType_Resource),
    url(r'^StationType/date/(?P<date>.*)/$', StationType_Resource),
    url(r'^StationManager/$', StationManager_Resource),
    url(r'^StationManager/(?P<id>\d+)/$', StationManager_Resource),
    url(r'^StationManager/date/(?P<date>.*)/$', StationManager_Resource),
    url(r'^Station/$', Station_Resource),
    url(r'^Station/(?P<id>\d+)/$', Station_Resource),
    url(r'^Station/date/(?P<date>.*)/$', Station_Resource),
    url(r'^Station/info/$', station_handler, {'emitter_format': 'default'}),
    url(r'^Station/info/(?P<id>\d+)/$', station_handler, {'emitter_format': 'default'}),
    url(r'^Station/info/list/$', station_list_handler, {'emitter_format': 'default'}),
    url(r'^Overseer/$', Overseer_Resource),
    url(r'^Overseer/(?P<id>\d+)/$', Overseer_Resource),
    url(r'^Overseer/date/(?P<date>.*)/$', Overseer_Resource),
    url(r'^InstrumentType/$', InstrumentType_Resource),
    url(r'^InstrumentType/(?P<id>\d+)/$', InstrumentType_Resource),
    url(r'^InstrumentType/date/(?P<date>.*)/$', InstrumentType_Resource),
    url(r'^Instrument/$', Instrument_Resource),
    url(r'^Instrument/(?P<id>\d+)/$', Instrument_Resource),
    url(r'^Instrument/date/(?P<date>.*)/$', Instrument_Resource),
    url(r'^Variable/$', Variable_Resource),
    url(r'^Variable/(?P<id>\d+)/$', Variable_Resource),
    url(r'^Variable/date/(?P<date>.*)/$', Variable_Resource),
    url(r'^UnitOfMeasurement/$', UnitOfMeasurement_Resource),
    url(r'^UnitOfMeasurement/(?P<id>\d+)/$', UnitOfMeasurement_Resource),
    url(r'^UnitOfMeasurement/date/(?P<date>.*)/$', UnitOfMeasurement_Resource),
    url(r'^TimeZone/$', TimeZone_Resource),
    url(r'^TimeZone/(?P<id>\d+)/$', TimeZone_Resource),
    url(r'^TimeZone/date/(?P<date>.*)/$', TimeZone_Resource),
    url(r'^TimeStep/$', TimeStep_Resource),
    url(r'^TimeStep/(?P<id>\d+)/$', TimeStep_Resource),
    url(r'^TimeStep/date/(?P<date>.*)/$', TimeStep_Resource),
    url(r'^Timeseries/$', Timeseries_Resource),
    url(r'^Timeseries/(?P<id>\d+)/$', Timeseries_Resource),
    url(r'^Timeseries/date/(?P<date>.*)/$', Timeseries_Resource),
    url(r'^tsdata/(?P<ts_id>\d+)/$', TSDATA_Resource,
                                                  {'emitter_format': 'plain'}),
    url(r'^gfdata/(?P<gf_id>\d+)/$', GFDATA_Resource, {'emitter_format': 'gfd'} ),
)
