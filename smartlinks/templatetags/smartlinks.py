from django import template

from smartlinks import smartlinks_conf
from smartlinks.parser import SmartLinkParser, SmartEmbedParser

register = template.Library()

@register.filter
def smartlinks(value):
    """
    Parse the smartlinks in the data piped through the filter.
    """
    filters = [SmartLinkParser, SmartEmbedParser]

    for filter in filters:
        value = filter(smartlinks_conf).process_smartlinks(value)
    return value