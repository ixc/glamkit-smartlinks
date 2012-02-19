from django.core.exceptions import ValidationError

from django.db.models.fields import CharField as ModelCharField
from django.forms.fields import CharField as FormsCharField
from django.utils.encoding import smart_unicode

from .parser import SmartEmbedParser, SmartLinkParser, Parser
from smartlinks.models import IndexEntry
from . import smartlinks_conf

class SmartLinkValidator(object):
    """
    There are two validation levels:

        - Validate that the text is actually formed like a valid smartlink.
        - Validate that the smartlink is resolved properly (``verify_exists``
        is responsible for that).
    """

    message = (
        u'Enter a valid smartlink. The syntax is '
        u' [[ smartlink ]] or [[ smartlink | verbose text ]] '
        u' or [[ model->smartlink ]] or [[ model->smartlink | verbose text ]].'
    )

    unresolved_message = (
        u'This smartlink has correct formatting, but it did not resolve '
        u'to a valid existing object.'
    )

    code = 'invalid'

    def __init__(self,
                 verify_exists=False):
        super(SmartLinkValidator, self).__init__()
        self.verify_exists = verify_exists

    def __call__(self, value):
        value = smart_unicode(value.strip())

        if not value:
            # Do not attempt to verify empty links.
            return

        for parser in (SmartLinkParser, SmartEmbedParser):
            match = parser.finder.match(value)
            if match:
                break
        else:
            raise ValidationError(self.message)

        if self.verify_exists:

            # Early return from ``Parser`` class indicates that
            # there were errors during smartlink resolution.
            if Parser.parse(parser(smartlinks_conf), match):
                raise ValidationError(self.unresolved_message)


class SmartLinkField(ModelCharField):
    """
    Model field for a smartlink, for use in model definitions.
    It can be useful for linking to internal content through one particular
    field, much like internal analogue of ``UrlField``::

        class Quote(models.Model):
            link = smartlinks.SmartLinkField()

    This fields provides three magic methods:

    ``get_<fieldname>_url`` method, which will automatically resolve
    smartlink. eg. in our example you can do::

        q = Quote.objects.all()[0]
        url = q.get_link_url() # Returns URI, or empty string when resolution fails.

    ``get_<fieldname>_text`` method, which will automatically resolve
    smartlink. eg. in our example you can do::

        q = Quote.objects.all()[0]
        url = q.get_link_text() # Returns text to use in the link.

   To get the actual object referred to by the smartlink, use
   ``get_<fieldname>_object`` method. It will return ``None`` if lookup failed
   or was ambiguous.

    Note that the field returns the object URI, and not the rendered
    ``<a href=...></a>`` tag.
    """

    def __init__(self, verify_exists=False,
                 max_length=300,
                 help_text="Enter a valid smartlink",
                 *args, **kwargs):
        """
        :param verify_exists: If this parameter is set to ``True``, and
        the entered smartlink does not resolve the validator will complain.

        Inspired by ``UrlField`` behavior.
        """
        self.max_length = max_length
        self.help_text = help_text
        self.verify_exists = verify_exists
        self.verify_exists = verify_exists
        super(SmartLinkField, self).__init__(*args,
                                            max_length = max_length,
                                            help_text = help_text,
                                             **kwargs)

    def formfield(self, **kwargs):
        defaults = dict(
            form_class=SmartLinkFormField,
            max_length=self.max_length,
            verify_exists=self.verify_exists,
            help_text=self.help_text,
        )
        defaults.update(kwargs)
        return super(SmartLinkField, self).formfield(**defaults)

    def contribute_to_class(self, cls, name):
        super(SmartLinkField, self).contribute_to_class(cls, name)

        def resolve_smartlink(instance):
            """
            Return the object pointed by the smartlink
            or None.
            """
            link = getattr(instance, self.name)
            parser = SmartLinkParser(smartlinks_conf)
            try:
                return parser.get_smartlinked_object(link)
            except (IndexEntry.DoesNotExist,
                    IndexEntry.MultipleObjectsReturned):
                return None

        def resolve_smartlink_url(instance):
            """
            Return the URL of the smartlink.
            """
            link = getattr(instance, self.name)
            parser = SmartLinkParser(smartlinks_conf)

            try:
                obj = parser.get_smartlinked_object(link)
                conf = parser.conf
            except (IndexEntry.DoesNotExist,
                    IndexEntry.MultipleObjectsReturned):
                return u""
            url = getattr(obj, conf.url_field, u"")
            return url() if callable(url) else url

        def resolve_smartlink_text(instance):
            """
            Return the Text of the smartlink.
            """
            link = getattr(instance, self.name)
            parser = SmartLinkParser(smartlinks_conf)
            return parser.get_smartlink_text(link) # sets verbose_text

        setattr(cls, 'get_%s_object' % self.name, resolve_smartlink)
        setattr(cls, 'get_%s_url' % self.name, resolve_smartlink_url)
        setattr(cls, 'get_%s_text' % self.name, resolve_smartlink_text)

    def south_field_triple(self):
        """
        Return a suitable description of this field for South.
        """
        from south.modelsinspector import introspector
        field_class = 'django.db.models.CharField'
        args, kwargs = introspector(self)
        return (field_class, args, kwargs)


class SmartLinkFormField(FormsCharField):
    """
    Form field for a smartlink, for use in forms.

    Most of the time the user won't need to use this field manually,
    it should be automatically used by ``ModelForm``s.

    The field validates whether the stored value is a valid *smartlink*.
    It can optionally check whether smartlink resolves to a valid object
    at save time (there is no guarantee though that it will still
    resolve at the render time).
    """
    def __init__(self, max_length=None,
                       min_length=None,
                       verify_exists=False,
                       *args,
                       **kw):
        """
        :param verify_exists: Verify that smartlink resolves to
        an existing object.
        """
        super(SmartLinkFormField, self).__init__(max_length,
                                             min_length,
                                             *args,
                                             **kw)
        self.validators.append(SmartLinkValidator(verify_exists))

    def to_python(self, value):
        value = value.strip()

        # Add square brackets if the field is non-empty.
        if value and not value.startswith("["):
            value = u"[[ %s ]]" % value
        return super(SmartLinkFormField, self).to_python(value)