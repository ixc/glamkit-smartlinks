from __future__ import absolute_import

from django import template

from smartlinks.conf import smartlinks_conf
from ..parser import SmartLinkParser, SmartEmbedParser
from ..models import IndexEntry

register = template.Library()

@register.filter
def smartlinks(value):
    """
    Parse the smartlinks in the data piped through the filter.

    Replaces each smartlink with a corresponding
    ``<a href=...>...</a>`` link
    """
    link_parser = SmartLinkParser(smartlinks_conf)
    embed_parser = SmartEmbedParser(smartlinks_conf)
    for parser in (link_parser, embed_parser):
        value = parser.process_smartlinks(value)
    return value

@register.filter
def smartlink_obj(value):
    """
    Get the object the smartlink is referring to,
    or ``None``.
    """
    link_parser = SmartLinkParser(smartlinks_conf)
    try:
        return link_parser.get_smartlinked_object(value)
    except (IndexEntry.DoesNotExist,
            IndexEntry.MultipleObjectsReturned):
        return None

@register.filter
def smartlink_url(value):
    """
    Get the URL smartlinked object is referring to.
    """
    link_parser = SmartLinkParser(smartlinks_conf)

    try:
        obj = link_parser.get_smartlinked_object(value)
        conf = link_parser.conf
        url = getattr(obj, conf.url_field, None)
        return url() if callable(url) else url
    except (IndexEntry.DoesNotExist,
            IndexEntry.MultipleObjectsReturned):
        return None
