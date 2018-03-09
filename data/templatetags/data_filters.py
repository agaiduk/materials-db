from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def commas_to_spaces(value):
    '''
    Replace all commas by white spaces
    '''
    return value.replace(',', ' ')

