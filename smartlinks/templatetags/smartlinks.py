from django import template

from .. import smartlinks_conf
from ..parser import SmartLinkParser, SmartEmbedParser
from ..models import IndexEntry

register = template.Library()

link_parser = SmartLinkParser(smartlinks_conf)
embed_parser = SmartEmbedParser(smartlinks_conf)

@register.filter
def smartlinks(value):
    """
    Parse the smartlinks in the data piped through the filter.

    Replaces each smartlink with a corresponding
    ``<a href=...>...</a>`` link
    """
    for parser in (link_parser, embed_parser):
        value = parser.process_smartlinks(value)
    return value

@register.filter
def get_smartlinked_obj(value):
    """
    Get the object the smartlink is referring to,
    or ``None``.
    """
    try:
        return link_parser.get_smartlinked_object(value)
    except (IndexEntry.DoesNotExist,
            IndexEntry.MultipleObjectsReturned):
        return None