from django import template
register = template.Library()

def dict_get(value, arg):
    #custom template tag used like so:
    #{{dictionary|dict_get:var}}
    #where dictionary is duh a dictionary and var is a variable representing
    #one of it's keys
    if value:
        return value.get(arg, None)

    return None

register.filter('dict_get',dict_get)
