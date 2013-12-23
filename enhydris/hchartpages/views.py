from django.views.generic import list_detail
from django.shortcuts import get_object_or_404
from django.http import HttpResponsePermanentRedirect
from django.core.urlresolvers import reverse
from enhydris.hchartpages.models import ChartPage, Chart, Variable

def chartpage_detail(request, urlcode, **kwargs):
    kwargs["queryset"] = ChartPage.objects.all()
    page = get_object_or_404(ChartPage, url_name = urlcode)
    object_id = page.id
    charts = Chart.objects.order_by('order').filter(chart_page=object_id)
    variables = Variable.objects.extra(order_by=['chart__order','-is_main_variable',]).filter(chart__chart_page=object_id)
    kwargs["template_name"] = "chart_detail.html"
    kwargs["template_object_name"] = "page"
    kwargs["extra_context"] = { 'charts': charts, 'variables': variables}
    return list_detail.object_detail(request, object_id = object_id, **kwargs)

def url_redir(request, url_id):
    page = get_object_or_404(ChartPage, url_int_alias=url_id)
    urlcode = page.url_name
    return HttpResponsePermanentRedirect(reverse('enhydris.hchartpages.views.chartpage_detail', args=[urlcode,]))

