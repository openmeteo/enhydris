from django import template

register = template.Library()
@register.inclusion_tag("form_as_table_rows.html", takes_context=True)
def form_as_table_rows(context, form, id=None):
    """
    Create a form using HTML table rows.
    """
    context["form"] = form
    context["id"] = id
    return context

@register.inclusion_tag("forms_as_table_cols.html", takes_context=True)
def forms_as_table_cols(context, formset, id=None):
    """
    Create a form using HTML table rows.
    """
    context["form"] = formset
    context["id"] = id
    return context
