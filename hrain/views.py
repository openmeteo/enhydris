from django.shortcuts import render_to_response
from enhydris.hrain import models

def index(request):
    return render_to_response('rain-index.html',
        { 'events': models.Event.objects.all() })
