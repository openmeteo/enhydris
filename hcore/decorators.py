from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q
from django.contrib.gis.geos import Polygon
from enhydris.hcore.models import *

#############################################################
# Decorators for sorting and filtering

def filter_by(filter_list):
    """
    Filter out entries from an object list view.

    Use as a decorator to select particular model fields to filter out
    from a object_list view. Example use::

    @filtering_by(('owner', 'type',))
    def station_list(*args, **kwargs):
        return list_detail.object_list(*args, **kwargs)

    """
    #FIXME: Validation of GET values (e.g. by_wbasin='1002' would raise exc)
    def fil(f):
        def _dec(request, queryset, *args, **kwargs):
            nkwargs = kwargs
            nkwargs["extra_context"] = {}
            for arg in filter_list:
                value = None
                if arg in nkwargs:
                    value = nkwargs.pop(arg)
                if not value and request.GET.__contains__(arg):
                    value = request.GET[arg]
                if value:
                    mydict = {arg: value}
                    if not nkwargs["extra_context"].has_key("advanced_search"):
                        nkwargs["extra_context"].update({"advanced_search":True})
                    # This is a HACK for the self relation table
                    # political division
                    if arg == "political_division":
                        try:
                            queryset = Station.objects.get_by_political_division(value)
                        except:
                            queryset = queryset.none()
                    elif arg == "owner":
                        try:
                            obj = Lentity.objects.get(pk=value)
                            term = obj.__unicode__()
                            queryset = queryset.filter(
                                  Q(owner__organization__name=term) |
                                  Q(owner__person__first_name=term) &
                                  Q(owner__person__last_name=term))
                        except:
                            queryset = queryset.none()
                    elif arg == "type":
                        try:
                            obj = StationType.objects.get(pk=value)
                            term = obj.__unicode__()
                            queryset = queryset.filter(
                                          Q(type__descr=term) |
                                          Q(type__descr_alt=term))
                        except:
                            queryset = queryset.none()
                    elif arg == "water_division":
                        try:
                            obj = WaterDivision.objects.get(pk=value)
                            term = obj.__unicode__()
                            queryset = queryset.filter(
                                      Q(water_division__name=term) |
                                      Q(water_division__name_alt=term))
                        except:
                            queryset = queryset.none()
                    elif arg == "water_basin":
                        try:
                            obj = WaterBasin.objects.get(pk=value)
                            term = obj.__unicode__()
                            queryset = queryset.filter(
                                  Q(water_basin__name=term) |
                                  Q(water_basin__name_alt=term))
                        except:
                            queryset = queryset.none()
                    elif arg == "variable":
                        try:
                            obj = Variable.objects.get(pk=value)
                            term = obj.__unicode__()
                            queryset = queryset.filter(
                                  Q(timeseries__variable__descr=term)).distinct()
                        except:
                            queryset = queryset.none()
                    elif arg == "bounded":
                        try:
                            minx, miny, maxx, maxy=[float(i) for i in value.split(',')]
                            geom=Polygon(((minx,miny),(minx,maxy),(maxx,maxy),(maxx,miny),(minx,miny)),srid=4326)
                            queryset = queryset.filter( Q(point__contained=geom))
                        except:
                            queryset = queryset.none()


            return f(request, queryset, *args, **nkwargs)
        return _dec
    return fil

def sort_by(f):
    """
    Enable sorting in an object list view.
    
    Example use::
    
    @sort_by
    def station_list(*args, **kwargs):
        return list_detail.object_list(*args, **kwargs)

    """
    def _dec(request, queryset, *args, **kwargs):
        nkwargs = kwargs
        column = None
        if 'sort' in nkwargs:
            column = nkwargs.pop(sort)
        if not column and request.GET.__contains__('sort'):
            column = request.GET['sort']
        if column:
            queryset = queryset.order_by(column)
        return f(request, queryset, *args, **nkwargs)
    return _dec

##############################################################################
# Custom login required decorator
##############################################################################


def timeseries_permission(function=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for timeseries_download view that checks if only authenticated
    users have access to the data and then acts like the login_required
    decorator. Otherwise, it just calls the function.
    """

    if hasattr(settings, 'TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS') and\
            settings.TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS:
        return function

    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated(),
        redirect_field_name=redirect_field_name
    )

    if function:
        return actual_decorator(function)
    return actual_decorator


def gentityfile_permission(function=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for gentityfile_download view that checks if only authenticated
    users have access to the data and then acts like the login_required
    decorator. Otherwise, it just calls the function.
    """

    if hasattr(settings, 'TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS') and\
            settings.TSDATA_AVAILABLE_FOR_ANONYMOUS_USERS:
        return function

    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated(),
        redirect_field_name=redirect_field_name
    )

    if function:
        return actual_decorator(function)
    return actual_decorator
