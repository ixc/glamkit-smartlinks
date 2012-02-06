from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

#: Maximum length of the index entry in the database.
INDEX_ENTRY_LEN = 300

class IndexEntry(models.Model):
    """
    In order to simplify the smartlink resolution process the index of
    stemified attributes is kept.

    Consider adding smartlinks to models Event, Movie and Book. Suppose
    our toy application looks like this::

        class Event(models.Model):
            title = CharField()
            date = DateField()

        class Movie(models.Model):
            title = CharField()
            release_date = DateField()

        class Book(models.Model):
            title = CharField()
            printed = DateField()

            def __unicode__(self):
                return u"%s printed in %s" % (self.title, self.printed)

    In that context it is natural to refer to the ``Event`` by ``title`` or
    by ``title`` and ``date``, to the ``Movie`` by ``title`` or by ``title`` and the
    ``release_date``, and to the ``Book`` by ``title``, ``title`` and ``printed``,
    or ``__unicode__``.

    Furthermore, if a movie in our database was called *Mad Max* and released in
    *1984* we would like the queries ``[[ Mad Max ]]``, ``[[ Mad Max: 1984 ]]``,
    ``[[ Mad Max 1984 ]]`` and ``[[ mad max - 1984 ]]`` to resolve to the same
    good old *Mad Max*.

    Such querying is impossible without some sort of denormalization. Proper fulltext
    search is one option, but it's an overkill in terms of features,
    and the performance might quickly become unacceptable with one query per smartlink
    for each content page.

    Hence smartlinks library uses it's own cache in a form of a single table.
    During the configuration stage the user specifies which fields are *smartlinkable*
    like so::

        ('title', ('title', 'printed',), '__unicode__', 'pk')

    Such configuration would create three entries in the index per each book, all
    linking to the same object, with ``title``, ``title`` and ``printed`` concatenated,
    and the result of calling ``__unicode__``.

    .. note:: The order in which fields are specified is important. In our toy example
        ``[[ One Hundred Years of Solitude 1967 ]]`` will work, but
        ``[[ (1967) One Hundred Years of Solitude ]]`` won't.

    Furthermore, the values of the attributes are stemmed[#stemming] with all letters
    brought to the lower case and non-alphanumeric removed.

    For instance, for the book *One Hundred Years of Solitude* printed in 1967 we
    will create the following entries in the index:

        - onehundreadyearsofsolitude
        - onehundreadyearsofsolitude1967
        - onehundreadyearsofsolitudeprintedin1967
        - 27

    .. warning:: Having a cached index means having all the headache associated with
        invalidating it at the correct time. You can't call ``qs.update(...)``, delete
        records en masse, import data from other database or use fixtures on smartlinked
        data without manually updating the index. Legacy data present before the
        smartlinks installation becomes a problem as well. The solution is to call
        ``./manage.py reset_smartlink_index`` after such changes.

    .. [#stemming] In this context, removing unneded characters from the word
        combination.
    """

    # Value after stemming.
    value = models.CharField(db_index=True, max_length=INDEX_ENTRY_LEN)

    # Link to the object being smartlinked. To the performance freaks:
    # generic relations are just fine in this case because we don't want JOIN's
    # anyway.
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return "'%s' for (%s-%s)" % (self.value, self.content_type, self.object_id)

    class Meta:
        unique_together = (("value", "content_type", "object_id",),)