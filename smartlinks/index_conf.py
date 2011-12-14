import re

from django.template import Template
from django.utils.datastructures import SortedDict
from django.contrib.contenttypes.models import ContentType

from smartlinks.models import IndexEntry

# ..py:data:: smartlinks_conf
#
# Extremely scary global state. Mutable during initialization.
#
# Model shortcut -> :py:class:IndexConf instance.
smartlinks_conf = SortedDict()

class IndexConf(object):
    """
    Configuration of the smartlink index.

    Example configuration::

        SmartLinkConf(
            queryset=Event.objects,
            searched_fields=('title', 'slug', 'pk', 'my_custom_callback',)
            embeddable_attributes=('image', 'video',),
        )

    ..py:attribute:: queryset
        Fields which are searched

    ..py:attribute:: searched_fields
        List of

        - strings which are attributes or callable names
        - tuples of the strings specified above

    ..py:attribute:: embeddable_attributes
        List of callables or attribute names on the model
        specified as strings.

    Note that all templates are available on both class-level and instance-level.
    Class-level templates are used when the model is not specified and
    as the defaults for model-based templates.

    """

    # Regexp to match the characters which are removed during stemming.
    # By default all non-alphanumerics are removed.
    stemming_replace = re.compile(r"\W")

    # Template for normal rendering of the smartlink.
    template=Template("".join(
        ['<a href="{{ obj.get_absolute_url }}" title="{{ obj }}">',
         '{{ verbose_text }}',
         '</a>']
    ))

    # Error template used in case the smartlink can not be resolved.
    unresolved_template = Template(
            '<span class="smartlinks-unresolved">{{ verbose_text }}</span>')

    # Error template used in case the model name specified for the smartlink
    # was not referenced during configuration.
    model_unresolved_template = Template(
            '<span class="smartlinks-unresolved">{{ smartlink_text }}</span>')

    # Error template for the case when smartlink description corresponds to more then
    # one entry in the index.
    ambiguous_template = Template(
            '<span class="smartlinks-ambiguous">{{ verbose_text }}</span>')

    # Error template used in case the attributes of the model which were
    #    not specified in the 'embeddable_attributes' are being accessed.
    disallowed_embed_template = Template(
        '<span class="smartlinks-unallowed">{{ smartlink_text }}</span>')

    searched_fields=('pk', '__unicode__', 'slug', 'title')

    def __init__(self,
        queryset,
        searched_fields=None,
        embeddable_attributes=(),
        template=None,
        unresolved_template=None,
        model_unresolved_template=None,
        ambiguous_template=None,
        disallowed_embed_template=None
        ):

        self.queryset = queryset

        # Hack to make iteration over fields easier and more unified -
        # strings are turned into one-element tuple.
        if searched_fields:
            self.searched_fields = [f if isinstance(f, tuple)
                                    else (f,) for f in searched_fields]

        self.embeddable_attributes = embeddable_attributes

        # Change the default attributes only if they weren't changed
        self.template = template or self.template
        self.ambiguous_template = ambiguous_template or self.ambiguous_template
        if model_unresolved_template is not None:
            self.model_unresolved_template = model_unresolved_template
        if unresolved_template is not None:
            self.unresolved_template = unresolved_template
        if disallowed_embed_template is not None:
            self.disallowed_embed_template = disallowed_embed_template


    def find_object(self, query):
        """
        Find the entry in the :py:class:`IndexEntry` corresponding to the query
        and return the corresponding object.

        EG if class 'Celebration' is smartlinked, an instance of 'Celebration'
        will be returned or DoesNotExist/MultipleObjectsReturned default exception
        will be raised.

        :param query: String representing the query to search in index for.

        :throws:
            - :py:class:`IndexEntry`.DoesNotExist Django exception.
            - :py:class:`IndexEntry`.MultipleObjectsReturned Django exception.
        """
        query = dict(
            value = self._stem(query),
            content_type = self.queryset.model
        )

        try:
            return IndexEntry.objects.get(**query).content_object
        except IndexEntry.DoesNotExist:

            # A fallback in case we can't find an exact match -
            # let's just contend ourselves with STARTSWITH.
            query['value__startswith'] = query['value']
            del query['value']
            return IndexEntry.objects.get(**query).content_object

    # TODO - create meaningful flag names for those
    def update_index_for_object(self, model, instance, created='deleteme'):
        """
        Update index for the updated/deleted/created object.
        Creates/Removes SmartLinkIndex objects.

        :param model: SmartLinked model, subclass of Django's models.Model.
        :param instance: Instance of the model being processed for SmartLink
        caching.
        :param created: a flag.
            - False: object is edited.
            - True: object is created.
            - 'deleteme': object is deleted.

        Note:
            - we might run into cache invalidation problems if the django
                signal is bypassed - update_index_for_object will never
                get called and
        """
        deleted = created == 'deleteme'
        content_type = ContentType.objects.get_for_model(model)

        if not created or deleted:

            # Delete the previously cached objects
            self.objects.delete(
                content_type=content_type,
                object_id=instance.pk
            )

        if not deleted:

            # Update the index with new entries.
            for search_string in self._get_search_strings_for_index(instance):
                IndexEntry.objects.create(
                    value=search_string,
                    content_type=content_type,
                    object_id=instance.pk
                )

    def recreate_index(self):
        """
        Re-create the index for the ``self.queryset`` if it exists.
        Assumes the index is empty.
        """
        if self.queryset:
            for instance in self.queryset:
                self.update_index_for_object(instance.model, instance, created=True)

    def _get_search_strings_for_index(self, instance):
        """
        Get the searchable strings according to the configuration.
        """
        for fieldset in self.searched_fields:
            search_string = ''

            for fieldname in fieldset:

                # Will not throw AttributeError or TypeError, sanity check was
                # already performed by smartlink configuration.
                value = getattr(instance, fieldname)
                if callable(value):
                    value = value()

                search_string += unicode(value)

            yield search_string

    def _stem(self, query):
        """
        Perform (very basic) stemming of the query:
            - Delete all non-alphanumeric characters.
            - Put everything to lower case.

        :param query: string-like object.
        :rtype: string
        """
        return self.stemming_replace.sub("", query).lower()