from django.views.generic import list_detail
from django.shortcuts import get_object_or_404
from enhydris.hchartpages.models import ChartPage

def chartpage_detail(request, urlcode, **kwargs):
    kwargs["queryset"] = ChartPage.objects.all()
    page = get_object_or_404(ChartPage, url_name = urlcode)
    object_id = page.id
    kwargs["template_name"] = "chart_detail.html"
    kwargs["template_object_name"] = "page"
    return list_detail.object_detail(request, object_id = object_id, **kwargs)
