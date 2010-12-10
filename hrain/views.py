from django.shortcuts import render_to_response
from enhydris.hrain import models

def index(request):
    eventgroups = {}
    for e in models.Event.objects.all():
        eventgroups.setdefault(e.start_date.year, []).append(e)
    return render_to_response('rain-index.html', { 'eventgroups': eventgroups })
