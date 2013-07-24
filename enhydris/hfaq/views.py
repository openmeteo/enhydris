from django.views.generic import list_detail
from enhydris.hfaq.models import Topic, Item

def faqpage_detail(request, **kwargs):
    queryset = Item.objects.filter(published=True).order_by('order')
    topics = Topic.objects.all().order_by('order')
    kwargs["template_name"] = "faq_detail.html"
    kwargs["template_object_name"] = "items"
    kwargs["extra_context"] = {'topics': topics, }
    return list_detail.object_list(request, queryset=queryset, **kwargs)

