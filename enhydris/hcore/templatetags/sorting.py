# coding=UTF-8

from django import template
from django.utils import html

register = template.Library()


@register.simple_tag
def sorter(column, sort_order, label):
    """Return a label with a sorting indicator that can be used for sorting.

    {% sorter column_name sort_order label %}

    This tag returns "label", possibly followed by a downward or an upward
    arrow that indicates the current sorting method, all that enclosed in a
    href hyperlink that would cause the sorting order to be changed so that
    it goes primarily by the specified column. "sort_order" is the current
    sort order. If the first column of sort_order is the same as "column_name",
    the tag adds a downward or upward arrow (depending on whether the sorting
    is direct or reverse).
    """
    sign = ''
    indicator = ''
    if sort_order and (sort_order[0] == column):
        indicator = '&nbsp;↓'
        sign = '-'
    elif sort_order and (sort_order[0] == '-' + column):
        indicator = '&nbsp;↑'
    target = '?sort={}{}&{}'.format(
        sign, column, '&'.join(['sort=' + x for x in sort_order]))
    return '<a href="%s">%s%s</a>' % (html.escape(target), label, indicator)
