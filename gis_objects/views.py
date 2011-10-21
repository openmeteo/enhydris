from django.contrib.gis.shortcuts import render_to_kml
from django.contrib.gis.geos import Polygon
from django.http import Http404
from django.views.generic import list_detail
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from enhydris.hcore.models import Timeseries
from enhydris.hcore.views import clean_kml_request
from enhydris.gis_objects.models import *
from enhydris.gis_objects.decorators import *

models = {'boreholes'       : [GISBorehole,_('Borehole')],
          'pumps'           : [GISPump,_('Pump')],
          'refineries'      : [GISRefinery,_('Refinery')],
          'springs'         : [GISSpring,_('Spring')],
          'aqueduct_nodes'  : [GISAqueductNode,_('Aqueduct node')],
          'aqueduct_lines'  : [GISAqueductLine,_('Aqueduct segment')],
          'reservoirs'      : [GISReservoir,_('Reservoir')],
          }

geom_type={ 'boreholes'         : 'point',
            'pumps'             : 'point',
            'refineries'        : 'point',
            'springs'           : 'point',
            'aqueduct_nodes'    : 'point',
            'aqueduct_lines'    : 'linestring',
            'reservoirs'        : 'mpoly',
          }

models_parent_id={ 'boreholes'  : 'gisboreholespring_ptr_id',
            'pumps'             : 'gpoint_ptr_id',
            'refineries'        : 'gpoint_ptr_id',
            'springs'           : 'gisboreholespring_ptr_id',
            'aqueduct_nodes'    : 'gpoint_ptr_id',
            'aqueduct_lines'    : 'gline_ptr_id',
            'reservoirs'        : 'garea_ptr_id',
          }

templates = {   'boreholes'     : 'borehole_detail.html',
                'pumps'         : 'pump_detail.html',
                'refineries'    : 'refinery_detail.html',
                'springs'       : 'spring_detail.html',
                'aqueduct_nodes': 'aqueduct_node_detail.html',
                'aqueduct_lines': 'aqueduct_segment_detail.html',
                'reservoirs'    : 'reservoir_detail.html',
            }

def kml(request, layer):
    try:
        bbox=request.GET.get('BBOX', request.GET.get('bbox', None))
        other_id=request.GET.get('OTHER_ID', request.GET.get('other_id', None))
        has_timeseries=request.GET.get('TIMESERIES', request.GET.get('timeseries', None))
    except Exception, e:
        raise Http404
    if bbox:
        try:
            minx, miny, maxx, maxy=[float(i) for i in bbox.split(',')]
            geom=Polygon(((minx,miny),(minx,maxy),(maxx,maxy),(maxx,miny),(minx,miny)),srid=4326)
        except Exception, e:
            raise Http404
    try:
        getparams = clean_kml_request(request.GET.items())
        queryres = models[layer][0].objects.all()
        if bbox:
            if geom_type[layer]=='point':
                queryres = queryres.filter(point__contained=geom)
            elif geom_type[layer]=='linestring':
                queryres = queryres.filter(linestring__contained=geom)
            elif geom_type[layer]=='mpoly':
                pass
#                queryres = queryres.filter(mpoly__bboverlaps=geom)
            else:
                assert(False)
        if has_timeseries and has_timeseries in ('True', 'TRUE', 'true'):
            queryres = queryres.filter(gentity_ptr__in=\
                         Timeseries.objects.all().values("gentity").query)
    except Exception, e:
        raise Http404
    if other_id:
        queryres = queryres.filter(id=other_id)
    for arow in queryres:
        if getattr(arow, geom_type[layer]): 
            arow.kml = getattr(arow, geom_type[layer]).kml
    response = render_to_kml('gis_objects.kml', {'places': queryres})
    return response


def gis_objects_brief(request, *args, **kwargs):
    object_id = kwargs['object_id']
    found = False
    for model in models:
        if models[model][0].objects.filter(id=object_id).exists():
            kwargs["extra_context"] = {'type': models[model][1],}
            found = True
            amodel = model
            break
    if not found:
        raise Http404;
    kwargs['object_id'] = getattr(models[amodel][0].objects.get(\
                                  gisentity_ptr = kwargs['object_id']), 
                            models_parent_id[amodel])
    return list_detail.object_detail(request,
                                     queryset=models[amodel][0].objects.all(),
                                     template_object_name = "object",
                                     template_name = "gis_objects_brief.html",
                                     **kwargs)

def gis_objects_detail(request, *args, **kwargs):
    anonymous_can_download_data = False
    if hasattr(settings, 'TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS') and\
            settings.TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS:
        anonymous_can_download_data = True
    object_id = kwargs['object_id']
    kwargs['extra_context']={'use_open_layers': True,
        "anonymous_can_download_data": anonymous_can_download_data,}
    found = False
    for model in models:
        if models[model][0].objects.filter(id=object_id).exists():
            found = True
            amodel = model
            break
    if not found:
        raise Http404;
    kwargs['object_id'] = getattr(models[amodel][0].objects.get(\
                                  gisentity_ptr = kwargs['object_id']), 
                            models_parent_id[amodel])
    return list_detail.object_detail(request,
                                     queryset=models[amodel][0].objects.all(),
                                     template_object_name = "object",
                                     template_name = templates[amodel],
                                     **kwargs)
@sort_by
@filter_by
def gis_objects_list(request, queryset, *args, **kwargs):
    gtypes = GISEntityType.objects.all()
    kwargs["extra_context"] = { "use_open_layers": True,
                                "gtypes": gtypes}
    kwargs["template_name"] = "gis_objects_list.html"
    return list_detail.object_list(request, queryset, *args, **kwargs )
    
