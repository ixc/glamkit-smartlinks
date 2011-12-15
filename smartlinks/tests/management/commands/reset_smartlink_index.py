from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from smartlinks.management.commands.reset_smartlink_index import recreate_index

from smartlinks.models import IndexEntry
from smartlinks.index_conf import IndexConf
from smartlinks import register, register_smart_link

from smartlinks.tests.models import Movie

class IndexResetTest(TestCase):
    def testIndexRecreation(self):
        register_smart_link(('m', 'movie'), IndexConf(
            Movie.objects,
            searched_fields=('title',)
            )
        )

        self.m1 = Movie.objects.create(
            title="Mad Max",
            slug="mad-max",
            year="1986"
        )
        self.m2 = Movie.objects.create(
            title="Once upon a time in the West",
            slug="once",
            year="1990"
        )

        # Now let's tinker with the smartlink index and see whether it would
        # be able to restore itself to the initial state.
        IndexEntry.objects.all().delete()

        IndexEntry.objects.create(
            value="bogus",
            content_type=ContentType.objects.all()[0],
            object_id=200
        )

        IndexEntry.objects.create(
            value="bogus2",
            content_type=ContentType.objects.all()[0],
            object_id=200
        )

        # ...and see whether it can re-create itself properly.
        recreate_index()

        self.assertEqual(IndexEntry.objects.count(),
            2)

        # As only one field is searched, it should create one entry per
        # :py:class:`Movie` object.
        self.assertEqual(IndexEntry.objects.filter(object_id=self.m1.pk).count(),
         1)

        self.assertEqual(IndexEntry.objects.filter(object_id=self.m2.pk).count(),
         1)

