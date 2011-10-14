import os
from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.gdal import SpatialReference
from enhydris.gis_objects.models import (GISBorehole, GISPump, GISRefinery,
                                         GISSpring, GISAqueductNode,
                                         GISAqueductLine, GISReservoir)

site_mapping_borehole = {
    'gis_id'        : 'ID',
    'name'          : 'NAME',
    'code'          : 'CODE',
    'group'         : 'Group',
    'point'         : 'POINT',
}

site_mapping_pump = {
    'gis_id'        : 'ID',
    'name'          : 'NAME',
    'entity_type'   : 'TYPE',
    'point'         : 'POINT',
}

site_mapping_refinery = {
    'gis_id'        : 'ID',
    'name'          : 'NAME',
    'point'         : 'POINT',
}

site_mapping_spring = {
    'name'          : 'NAME',
    'original_gentity_id'    : 'GENTITY_ID',
    'point'         : 'POINT',
}

site_mapping_aqueduct_node = {
    'gis_id'        : 'ID',
    'name'          : 'NAM',
    'entity_type'     : 'NODE_TYPE',
    'type_name'     : 'Type_Name',
    'point'         : 'POINT',
}

site_mapping_aqueduct_line = {
    'gis_id'        : 'ID',
    'name'          : 'NAME',
    'entity_type'   : 'TYPE',
    'q'             : 'Q',
    'exs'           : 'EXS',
    'remarks'       : 'REMARKS',
    'original_gentity_id'    : 'GENTITY_ID',
    'type_name'     : 'Type_Name',
    'linestring'    : 'LINESTRING',
}

site_mapping_reservoir = {
    'area'          : 'AREA',
    'entity_type'   : 'TYPE',
    'name'          : 'NAME',
    'original_gentity_id':  'GENTITY_ID',
    'mpoly'         : 'POLYGON',
}

borehole_shp = os.path.abspath('/home/itia/soulman/eydap-geodata/borehole.shp')
pump_shp = os.path.abspath('/home/itia/soulman/eydap-geodata/pumping.shp')
refinery_shp = os.path.abspath('/home/itia/soulman/eydap-geodata/refinery.shp')
spring_shp = os.path.abspath('/home/itia/soulman/eydap-geodata/spring.shp')
aqueduct_node_shp = os.path.abspath('/home/itia/soulman/eydap-geodata/aqueductc.shp')
aqueduct_line_shp = os.path.abspath('/home/itia/soulman/eydap-geodata/aqueductl.shp')
reservoir_shp = os.path.abspath('/home/itia/soulman/eydap-geodata/reservoir.shp')

elements_orig = [
            [GISBorehole, site_mapping_borehole, borehole_shp],
            [GISPump, site_mapping_pump, pump_shp],
            [GISRefinery, site_mapping_refinery, refinery_shp],
            [GISSpring, site_mapping_spring, spring_shp],
            [GISAqueductNode, site_mapping_aqueduct_node, aqueduct_node_shp],
            [GISAqueductLine, site_mapping_aqueduct_line, aqueduct_line_shp],
            [GISReservoir, site_mapping_reservoir, reservoir_shp],
           ]

#elements = [
#            [GISAqueductLine, site_mapping_aqueduct_line, aqueduct_line_shp],
#           ]
elements=elements_orig

#srid=2100 for GGRS87

def run(verbose=True):
    for element in elements:
        element_lm = LayerMapping(element[0], 
                                  element[2],
                                  element[1],
                                  transform=True,
                                  source_srs = SpatialReference(2100),
                                  encoding = 'windows-1253')
        element_lm.save(strict=True, verbose=verbose)
