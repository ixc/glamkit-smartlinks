import re

from django.template import Template
from django.utils.datastructures import SortedDict
from django.contrib.contenttypes.models import ContentType

from smartlinks.models import IndexEntry, INDEX_ENTRY_LEN

#: Configuration global state. Mutable during initialization.
#:
#: Maps model shortcuts to :py:class:`SmartLinkConf` instances.
smartlinks_conf = SortedDict()

class SmartLinkConf(object):
    """
    Configuration of the smartlink index.

    .. highlight:: python

    Example configuration::

        SmartLinkConf(
            queryset=Event.objects,
            searched_fields=('title', 'slug', 'pk', 'my_custom_callback',),
            embeddable_attributes=('image', 'video',),
        )
    """

    #: Queryset to which the smartlink resolution is limited to. Comes in handy when
    #: you want to limit the ability to link to non-public content, eg::
    #:
    #:      queryset = Movie.objects.filter(public=True)
    queryset = None

    #: Fields which are searched for the smartlinks resolution.
    #: List of
    #:
    #:    - strings which are attributes or methods of the class,
    #:represented as strings.
    #:    - tuples of the strings specified above.
    #:
    #: EG the possible configuration might look like::
    #:
    #:      searched_fields = ('pk', '__unicode__', 'title', ('title', 'year'))
    #:
    #: Under the configuration specified above, with the model and the object
    #: specified below::
    #:
    #:      class Movie(models.Model):
    #:          title = models.CharField()
    #:          year = models.IntegerField()
    #:
    #:          def __unicode__(self):
    #:              return "movie %s" % self.title
    #:
    #:      Movie.objects.create(title="Mad Max", year=1984)
    #:
    #: The following links will work:
    #:
    #:      - ``[[ Mad Max ]]``
    #:      - ``[[ movie Mad Max ]]``
    #:      - ``[[ Mad Max 1984 ]]``
    #: Note that the order of the fields in the tuple is significant, eg
    #: ``[[ 1984 Mad Max ]]`` will **not** work.
    #:
    #: Also note that it is possible to do more complicated lookups using
    #: dot-notation. For instance, if you have two models::
    #:
    #:      class Teacher(models.Model):
    #:          position = models.CharField(max_length=100)
    #:          person = models.OneToOneField('Person')
    #:
    #:      class Person(model.Model):
    #:          name = models.CharField(max_length=100)
    #:
    #: And you want to be able to smartlink to the teacher using either his
    #: position or name the valid configuration would be::
    #:
    #:      searched_fields = ('position', 'person.name',)
    #:
    #: .. warning:: Dot-notation lookup does not try to be type-safe. If
    #: you misspell an attribute in the configuration, smartlinks library
    #: will be throwing ``KeyError`` during resolution time.
    #:
    #: If you desire a custom logic for the search terms generation,
    #: method py:meth:`_get_search_strings_for_index` is a good candidate for
    #: overwriting.
    searched_fields = ('pk', '__unicode__', 'slug', 'title')

    embeddable_attributes = ()
    """
    Sometimes just getting the link to the referenced object is not enough - we
    might want it's image, videoclip or in general any custom attribute.

    That's where *smartembeds* come to the rescue. Using proper configuration
    and the syntax almost identical to smartlinks we can get hold of those attributes.

    Suppose our *smartlinked* model looks like::

        class Movie(models.Model):
            title = models.CharField()
            image = models.ImageField()

            def image(self, size=300, alt='Image'):
                # ...some code to do resizing if ``size`` is specified...

                return '<img src="%s" title="%s" />' % (self.image.url, alt)

    Examples of smartembeds include::

        # Everything before the pipe symbol works the same way
        # as in smartlinks, the next string after the pipe symbol is the
        # attribute we are resolving.
        {{ Mad Max | image }}

        # Models are selected as usual
        {{ event->Mad Max | image }}

        # Furthermore, we can pass various parameters to the image method.
        {{ Mad Max | image | 300 | My image title }}

        # And those can be passed using keyword arguments.
        {{ Mad Max | image | 300 | alt=My image title }}
        {{ Mad Max | image | alt=My image title | size=300 }}

    The parameter ``embeddable_attributes`` specifies a tuple of method names
    specified as strings, eg ``embeddable_attributes= ('image', 'video')``.

    .. highlight:: python

    The reason behind this configuration settings is security pre-caution:
    we don't want users to be able to include links like ``{{ user->admin | password }}``,
    or, heaven forbid, ``{{ user->admin | delete }}``.
    """

    #: Regexp to match the characters which are removed during stemming.
    #: By default all non-alphanumerics and underscores are removed.
    stemming_replace = re.compile(r"[\W_]")

    #: Field used to get URL on the instance.
    url_field = "get_absolute_url"

    #: Template for normal rendering of the smartlink.
    #: Available objects are ``obj``, representing the linked instance,
    #: and ``verbose_text``.
    template = Template("".join(
        ['<a href="{{ obj.%s }}" title="{{ obj }}">' % url_field,
         '{{ verbose_text }}',
         '</a>']
    ))

    #: Error template used in case the smartlink can not be resolved.
    #: Available object is ``verbose_text``.
    unresolved_template = Template(
        '<span class="smartlinks-unresolved">{{ verbose_text }}</span>')

    #: Error template used in case the model name specified for the smartlink
    #: was not referenced during configuration.
    #: Available object is ``verbose_text``, representing the whole
    #: smartlink.
    model_unresolved_template = Template(
        '<span class="smartlinks-unresolved">{{ verbose_text }}</span>')

    #: Error template for the case when smartlink description corresponds to more then
    #: one entry in the index.
    #: Available object is ``verbose_text``.
    ambiguous_template = Template(
        '<span class="smartlinks-ambiguous">{{ verbose_text }}</span>')

    #: Error template used in case the attributes of the model which were
    #:    not specified in the 'embeddable_attributes' are being accessed.
    #: Available object is ``smartlink_text``, representing the whole
    #: smartlink.
    disallowed_embed_template = Template(
        '<span class="smartlinks-unallowed">{{ smartlink_text }}</span>')


    def __init__(self,
                 queryset=None,
                 searched_fields=None,
                 embeddable_attributes=(),
                 template=None,
                 unresolved_template=None,
                 model_unresolved_template=None,
                 ambiguous_template=None,
                 disallowed_embed_template=None
    ):
        if queryset is not None:
            self.queryset = queryset

        if searched_fields is not None:
            self.searched_fields = searched_fields

        # Hack to make iteration over fields easier and more unified -
        # strings are turned into one-element tuple.
        self.searched_fields = [f if isinstance(f, tuple)
                                else (f,) for f in self.searched_fields]

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

    def resolve_model(self):
        if hasattr(self.queryset, 'model'):
            return self.queryset.model
        elif callable(self.queryset):
            return self.queryset().model
        else:
            return self.queryset

    def find_object(self, query):
        """
        Find the entry in the :py:class:`IndexEntry` corresponding to the query
        and return the corresponding object.
        
        EG if class ``Celebration`` is smartlinked, an instance of ``Celebration``
        will be returned or one of ``DoesNotExist`` or ``MultipleObjectsReturned`` exceptions
        will be raised.

        Note that by overriding this method one can use smartlinks on the objects not
        in the database, eg Wikipedia::

            class WikiProxy(object):
                def __init__(self, title):
                    self.title = title

                def get_absolute_url(self):
                    return "http://en.wikipedia.com/wiki/%s" % self.title

            class WikiLinkConf(SmartLinkConf):

                # Note empty ``searched_fields`` - otherwise resolving engine
                # will get confused.
                searched_fields = ()

                def find_object(self, query):

                    # Possibly a piece of logic to find whether the article exists
                    # in wikipedia.
                    condition = ...

                    if condition:
                        return WikiProxy(title)

            register_smart_link(('w', 'wiki',), WikiLinkConf())

        :param query: String representing the query to search in index for.

        :throws:
            - :py:class:`IndexEntry`.DoesNotExist Django exception.
            - :py:class:`IndexEntry`.MultipleObjectsReturned Django exception.
        """


        query = dict(
            value=self._stem(query),
            content_type=ContentType.objects.get_for_model(self.resolve_model())
        )

        try:
            return IndexEntry.objects.get(**query).content_object
        except IndexEntry.DoesNotExist:
            # A fallback in case we can't find an exact match -
            # let's just contend ourselves with STARTSWITH.
            query['value__startswith'] = query['value']
            del query['value']
            return IndexEntry.objects.get(**query).content_object

    def update_index_for_object(self, sender, instance, created='deleteme', **kw):
        """
        Update index for the updated/deleted/created object.
        Creates/Removes SmartLinkIndex objects.

        This method gets attached to the ``post_save`` and ``delete``
        signals by the function :py:func:`register`.

        Note that if this method is somehow bypassed while the data is changed - eg
        ``.update()`` is called
        on the queryset, smartlink resolution will run into cache invalidation problems.
        At that point the best bet will be to run ``./manage.py reset_smartlink_index``,
        see :py:meth:`recreate_index`.

        :param sender: SmartLinked model, subclass of Django's models.Model.
        :param instance: Instance of the model being processed for SmartLink
        caching.
        
        :param created: a flag.
        
            - False: object is edited.
            - True: object is created.
            - 'deleteme': object is deleted.
        """
        deleted = created == 'deleteme'
        content_type = ContentType.objects.get_for_model(sender)

        if not created or deleted:
            # Delete the previously cached objects
            IndexEntry.objects.filter(
                content_type=content_type,
                object_id=instance.pk
            ).delete()

        try:
            qs_instance = self.queryset.filter(pk=instance.pk)
        except AttributeError:
            qs_instance = self.queryset().filter(pk=instance.pk)


        if not deleted and qs_instance:
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
            for instance in self.queryset.all():
                self.update_index_for_object(instance.__class__,
                    instance, created=True)

    def _get_search_strings_for_index(self, instance):
        """
        Get the searchable strings according to the configuration.

        This method is a good candidate for overriding if one needs custom
        logic for generating search string out of the index. EG one might want
        to create an entry in :py:class:`IndexEntry` per line in the ``instance.description``
        field::

            class GlossaryIndexConf(IndexConf):
                def _get_search_strings_for_index(self, instance):
                    # Note that if that this method is overriden, param
                    # self.searched_fields becomes redundant.

                    # One entry in index per line.
                    return [self._stem(line) for line in instance.description.split('\n')]

        Note how important it is to remember to apply the stemming and to get rid of
        the duplicates - otherwise, :py:class:`IndexEntry` will complain.

        :param instance: Instance returned by :py:meth:`find_object`, usually one which belongs
        to :py:attr:`queryset`.

        :return: Set of all string to be added to index.
        :rtype: iterable
        """

        # We are using set as we want to avoid the possible duplicates.
        search_strings = set()

        for fieldset in self.searched_fields:
            search_string = ''

            for fieldname in fieldset:
                # Dot-lookups are not guaranteed to resolve properly, because
                # they are difficult to verify during registration.

                # The lookups without '.'s are safe --
                # the sanity check was already performed during configuration.
                fieldnames = fieldname.split('.')
                value = instance

                for fieldname in fieldnames:
                    if value:
                        try:
                            value = getattr(value, fieldname)
                        except AttributeError:
                            value = value.get(fieldname)
                        if callable(value):
                            value = value()

                    search_string += unicode(value)

            # Stemming has to be performed before throwing out duplicated,
            # because otherwise some duplicates can be missed.
            search_strings.add(self._stem(search_string))

        return search_strings

    def _stem(self, query):
        """
        Perform (very basic) stemming of the query:

            - Delete all non-alphanumeric characters.
            - Put everything to lower case.
            - Uses only first :py:data:`INDEX_ENTRY_LEN` characters in the query.

        :param query: string-like object.
        :rtype: string
        """
        return self.stemming_replace.sub(u"", query).lower()[:INDEX_ENTRY_LEN]