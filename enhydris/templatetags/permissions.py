from django.template import Library

register = Library()


@register.filter
def can_edit(user, object):
    return _check_perm(user, object, "edit")


@register.filter
def can_delete(user, object):
    return _check_perm(user, object, "delete")


def _check_perm(user, object, perm):
    return user.is_superuser
