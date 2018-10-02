"""
Hcore Widgets
"""

from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.forms.utils import flatatt
from django.template.loader import render_to_string
import django.forms as forms

class SelectWithPop(forms.Select):
    """
    This widget creates a popup with a plus button on the right which
    opens a form for inline instance creation of foreign models
    """
    def __init__(self, model_name='', *args, **kwargs):
        """
        Overiden init method to populate gentities
        """
        self.model_name = model_name
        super(SelectWithPop, self).__init__(*args, **kwargs)

    def render(self, name, *args, **kwargs):
        if not self.model_name:
            self.model_name = name
        html = super(SelectWithPop, self).render(name, *args, **kwargs)
        popupplus = render_to_string("form/popplus.html",
                                                    {'field': self.model_name,
                                                     'orig_name': name})
        return html+popupplus


class ReadOnlyWidget(forms.Widget):
    """
    This is a widget for read only form fields.
    """
    def render(self, name, value, attrs):
        final_attrs = self.build_attrs(attrs, name=name)
        if hasattr(self, 'initial'):
            value = self.initial
            return mark_safe("<p %s>%s</p>" % (flatatt(final_attrs),
escape(value) or ''))

    def _has_changed(self, initial, data):
        return False

class ReadOnlyField(forms.Field):
    """
    This is a formfield similar to editable=False but actually displays the
    value of the field.
    """
    widget = ReadOnlyWidget
    def __init__(self, widget=None, label=None, initial=None, help_text=None):
        super(type(self), self).__init__(self, label=label, initial=initial,
            help_text=help_text, widget=widget)
        self.widget.initial = initial

    def clean(self, value):
        return self.widget.initial
