from django.conf import settings
from django.template import Library, Node, TemplateSyntaxError

register = Library()

class SettingsNode( Node ):
    def __init__( self, setting_names ):
        self.setting_names = setting_names

    def render( self, context ):
        for setting_name in self.setting_names:
            try:
                val = settings.__getattr__( setting_name )
            except AttributeError:
                val = None
            context[ setting_name ] = val
        return ''

def do_settings( parser, token ):
    bits = token.split_contents()
    if not len( bits ) > 1:
        raise TemplateSyntaxError( '%r tag requires at least one argument' %
bits[ 0 ] )
    return SettingsNode( bits[ 1: ] )

do_settings = register.tag( 'settings', do_settings )
