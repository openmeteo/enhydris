import string
from django.template import Library
from django.conf import settings
from hydroscope.hcore.models import *

register = Library()

# TODO: Is this really needed?
@register.inclusion_tag('append_get_params.html')
def stationlist_filter_params(get_vars):
    """Return the get parameters for the stationlist filtering mechanism."""
    filter_vars = {}
    # FIXME: DRY: The list of filters are already defined in the view decorator
    filter_var_names = ['sort',]
    for v in filter_var_names:
        filter_vars[v] = getattr(get_vars, v, None)
    return {'filter_vars': filter_vars}


@register.inclusion_tag('filter_table.html')
def filter_table(request, help_inline):
    """Choose the option to be selected based on the GET variables.
    
    "help_inline" variable denotes if an explanation text will be presented or instead
    of this a link to popup help is appeared.
    """
    subdiv1 = 'Sub Division 1'
    subdiv2 = 'Sub Division 2'
    country = ''
    if hasattr(settings, 'FILTER_POLITICAL_SUBDIVISION1_NAME'):
        subdiv1 = settings.FILTER_POLITICAL_SUBDIVISION1_NAME
    if hasattr(settings, 'FILTER_POLITICAL_SUBDIVISION2_NAME'):
        subdiv2 = settings.FILTER_POLITICAL_SUBDIVISION2_NAME
    if hasattr(settings, 'FILTER_DEFAULT_COUNTRY'):
        country = settings.FILTER_DEFAULT_COUNTRY
    vars = {'political_division':
                PoliticalDivision.objects.filter(parent=None),
            'district': [],
            'prefecture': [],
            'water_division': WaterDivision.objects.all(),
            'water_division': WaterDivision.objects.all(),
            'water_basin': WaterBasin.objects.all(),
            'owner': Lentity.objects.all(),
            'type': StationType.objects.all(),
            'get_vars': request.GET,
            'url_type': string.split(request.get_full_path(),sep="/")[1],
            'country': PoliticalDivision.objects.filter(name=country),
            'subdiv1': subdiv1,
            'subdiv2': subdiv2,
            'help_inline': help_inline}
    return vars

@register.inclusion_tag('selected_stations.html')
def filter_station_ids(request, station_id=''):
    """Filter table ids from get vars for table checkbox"""
    if request.method == "GET" :
        try :
            my_vars = {'selected_ids': request.GET["selected_ids"],
                       'station_id': station_id,}
        except:
            my_vars = {'selected_ids': '',
                       'station_id': station_id,}
        return my_vars

@register.filter
def intvalue(value):
    """Return the integer of the argument."""
    return int(value)

@register.filter
def check_contains(dict, word):
    """Check if word is part of comma separated list"""
    rdict = string.split(dict,sep=",")
    if not rdict is None:
        if str(word) in rdict:
            return True
    return False
