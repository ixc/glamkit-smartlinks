from django.core.exceptions import ValidationError

from django.db.models.fields import CharField as ModelCharField
from django.forms.fields import CharField as FormsCharField
from django.utils.encoding import smart_unicode
from django import forms
from django.utils.safestring import SafeData
from django.contrib.admin.widgets import AdminTextInputWidget

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


class SmartLink(object):
    """
    Wrapper for the smartlink data.
    """
    def __init__(self, instance, field_name):
        self.instance = instance
        self.field_name = field_name
        self.parser = SmartLinkParser(smartlinks_conf)

    @property
    def verbose_text(self):
        """
        :return: Verbose text for the smartlink.
        """
        return self.parser.get_smartlink_text(self.raw)

    def _get_raw(self):
        return (self.instance.__dict__[self.field_name] or '')
    def _set_raw(self, val):
        setattr(self.instance, self.field_name, val)
    #: Setter and getter for the raw data in the
    #: field.
    #: :return: Raw smartlink.
    raw = property(_get_raw, _set_raw)

    @property
    def url(self):
        """
        :return: URL the smartlink is pointing to,
        or empty string if it is unresolved.
        :rtype: unicode
        """
        obj = self.object
        if obj is None:
            return u""
        # Calling ``self.object`` sets ``self.parser.conf``.
        conf = self.parser.conf
        url = getattr(obj, conf.url_field, u"")
        return url() if callable(url) else url

    @property
    def object(self):
        """
        :return: Object the smartlink is pointing to
        or ``None`` if it is unresolved.
        """
        try:
            return self.parser.get_smartlinked_object(self.raw)
        except (IndexEntry.DoesNotExist,
                IndexEntry.MultipleObjectsReturned):
            return None

    @property
    def rendered_link(self):
        """
        :return: rendered ``<a href='...'>...</a>`` tag.
        :rtype: SafeString
        """
        return self.parser.process_smartlinks(self.raw)

    def __unicode__(self):
        """
        Return URL by default.
        """
        return self.raw

    def __len__(self):
        return len(self.raw)

class SmartLinkDescriptor(object):
    def __init__(self, field):
        self.field = field

    def __get__(self, instance, owner):
        if instance is None:
            raise AttributeError('Can only be accessed via an instance.')
        smartlink = instance.__dict__[self.field.name]
        if smartlink is None:
            return None
        return SmartLink(instance, self.field.name)

    def __set__(self, obj, value):
        if isinstance(value, SmartLink):
            obj.__dict__[self.field.name] = value.raw
        else:
            obj.__dict__[self.field.name] = value


class SmartLinkField(ModelCharField):
    """
    Model field for a smartlink, for use in model definitions.
    It can be useful for linking to internal content through one particular
    field, much like internal analogue of ``UrlField``::

        class Quote(models.Model):
            link = smartlinks.SmartLinkField()

    From then one, ``quote_instance.link`` will return an instance of
    :py:class:`smartlinks.fields.SmartLink`, which will render to URL of the smartlink
    in the template.

    Usage::

        >>> q = Quote(link="[[ Scar Face ]]") # square brackets are optional
        >>> q.link.raw
        u'[[ Scar Face ]]'
        >>> q.link.verbose_text
        u'Scar Face'
        >>> q.link.rendered_link
        u'<a alt="scar face" href="/movies/scar-face-2">Scar Face</a>'
        >>> q.link.object
        <Movie: Scar Face>
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
            widget=SmartLinkWidget,
        )
        defaults.update(kwargs)
        return super(SmartLinkField, self).formfield(**defaults)

    def contribute_to_class(self, cls, name):
        super(SmartLinkField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, SmartLinkDescriptor(self))

    def pre_save(self, model_instance, add):
        value = super(SmartLinkField, self).pre_save(model_instance, add)
        return value.raw

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return value.raw

    def get_prep_value(self, value, connection=None, prepared=False):
        try:
            return value.raw
        except AttributeError:
            return value

    def south_field_triple(self):
        """
        Return a suitable description of this field for South.
        """
        from south.modelsinspector import introspector
        field_class = 'django.db.models.CharField'
        args, kwargs = introspector(self)
        return (field_class, args, kwargs)


class SmartLinkWidget(AdminTextInputWidget):
    """
    Custom descriptors require custom classes.
    """
    def render(self, name, value, attrs=None):
        if value is not None:
            try:
                value = value.raw
            except AttributeError:
                pass
        return super(SmartLinkWidget, self).render(name, value, attrs)

    def _has_changed(self, initial, data):
        return True

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
    widget = SmartLinkWidget

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

from django.contrib.admin.options import FORMFIELD_FOR_DBFIELD_DEFAULTS
FORMFIELD_FOR_DBFIELD_DEFAULTS[SmartLinkField] = {'widget': SmartLinkWidget}
