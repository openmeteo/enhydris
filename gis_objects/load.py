import os
from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.gdal import SpatialReference
from other_gis.models import (GISBorehole, GISPump, GISRefinary,
                              GISSpring, GISAqueductNode,
                              GISAqueductLine)

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
    'type'          : 'TYPE',
    'point'         : 'POINT',
}

site_mapping_refinary = {
    'gis_id'        : 'ID',
    'name'          : 'NAME',
    'point'         : 'POINT',
}

site_mapping_spring = {
    'name'          : 'NAME',
    'gentity_id'    : 'GENTITY_ID',
    'point'         : 'POINT',
}

site_mapping_aqueduct_node = {
    'gis_id'        : 'ID',
    'name'          : 'NAM',
    'node_type'     : 'NODE_TYPE',
    'type_name'     : 'Type_Name',
    'point'         : 'POINT',
}

site_mapping_aqueduct_line = {
    'gis_id'        : 'ID',
    'name'          : 'NAME',
    'type'          : 'TYPE',
    'q'             : 'Q',
    'exs'           : 'EXS',
    'remarks'       : 'REMARKS',
    'gentity_id'    : 'GENTITY_ID',
    'type_name'     : 'Type_Name',
    'linestring'    : 'LINESTRING',
}

borehole_shp = os.path.abspath('/home/itia/soulman/eydap-geodata/borehole.shp')
pump_shp = os.path.abspath('/home/itia/soulman/eydap-geodata/pumping.shp')
refinary_shp = os.path.abspath('/home/itia/soulman/eydap-geodata/refinery.shp')
spring_shp = os.path.abspath('/home/itia/soulman/eydap-geodata/spring.shp')
aqueduct_node_shp = os.path.abspath('/home/itia/soulman/eydap-geodata/aqueductc.shp')
aqueduct_line_shp = os.path.abspath('/home/itia/soulman/eydap-geodata/aqueductl.shp')

elements_orig = [
            [GISBorehole, site_mapping_borehole, borehole_shp],
            [GISPump, site_mapping_pump, pump_shp],
            [GISRefinary, site_mapping_refinary, refinary_shp],
            [GISSpring, site_mapping_spring, spring_shp],
            [GISAqueductNode, site_mapping_aqueduct_node, aqueduct_node_shp],
            [GISAqueductLine, site_mapping_aqueduct_line, aqueduct_line_shp],
           ]

elements = [
            [GISAqueductLine, site_mapping_aqueduct_line, aqueduct_line_shp],
           ]

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
