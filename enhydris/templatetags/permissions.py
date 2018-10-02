from django.template import Library

register = Library()

@register.filter
def can_edit(user, object):
    return _check_perm(user,object,'edit')
@register.filter
def can_delete(user, object):
    return _check_perm(user,object,'delete')

def _check_perm(user, object, perm):
    if not user.is_authenticated():
        return False
    if user.has_row_perm(object, perm):
        return True
    return False
