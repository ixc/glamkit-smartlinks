from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django.template.context import Context

from smartlinks.conf import SmartLinkConf
from smartlinks.models import IndexEntry

from smartlinks.tests.models import Movie


class ConfTest(TestCase):
    def setUp(self):
        self.ae = self.assertEqual

        self.m = Movie.objects.create(
            title="Mad Max",
            slug="mad-max",
            year=1984
        )

        self.secret_movie = Movie.objects.create(
            title="Secret Movie",
            slug='secret-movie',
            public=False,
            year=2000
        )

        self.harry1 = Movie.objects.create(
            title="Dirty Harry",
            slug="dirty-harry",
            year=1971
        )

        self.harry2 = Movie.objects.create(
            title="Dirty Harry",
            slug='dirty-harry',
            year=1976
        )

        self.movie_conf = SmartLinkConf(
            Movie.objects,
            searched_fields=(
                'title',
                'slug',
                ('title', 'year',),
                '__unicode__',
                'pk'
            )
        )

        self.movie_conf.update_index_for_object(Movie,
            self.m,
            created=True)

        self.movie_conf.update_index_for_object(Movie,
            self.harry1,
            created=True)

        self.movie_conf.update_index_for_object(Movie,
            self.harry2,
            created=True)

        self.movie_conf.update_index_for_object(Movie,
            self.secret_movie,
            created=True)

    def tearDown(self):
        IndexEntry.objects.all().delete()

    def testTemplates(self):
        # Test normal template.
        obj = type("MyObj", (object,), dict(
            __unicode__ = lambda self: u"obj",
            get_absolute_url = lambda self: "google.com"
        ))

        self.assertEqual(
            self.movie_conf.template.render(
                Context({
                    'obj': obj,
                    "verbose_text": u"verbose_text"
                })
            ),
            "".join(
                ['<a href="google.com" title="obj">',
                 'verbose_text',
                 '</a>']
        ))


        # Unresolved template.
        self.assertEqual(
            self.movie_conf.unresolved_template.render(
                Context({
                    "verbose_text": "verbose_text"
                })
            ),
            '<span class="smartlinks-unresolved">verbose_text</span>'
        )

        # Ambigous template.
        self.assertEqual(
            self.movie_conf.ambiguous_template.render(
                Context({
                    "verbose_text": "verbose_text"
                })
            ),
            '<span class="smartlinks-ambiguous">verbose_text</span>'
        )

        # Disallowed embeds template.
        self.assertEqual(
            self.movie_conf.disallowed_embed_template.render(
                Context({
                    "smartlink_text": "smartlink text"
                })
            ),
            '<span class="smartlinks-unallowed">smartlink text</span>'
        )


        # No model found template
        self.assertEqual(
            self.movie_conf.unresolved_template.render(
                Context({
                    "verbose_text": "smartlink_text"
                })
            ),
            '<span class="smartlinks-unresolved">smartlink_text</span>'
        )

        
    def testFindObject(self):
        self.assertEqual(
            self.movie_conf.find_object(
                query="Mad Max"
            ),
            self.m
        )

        self.assertEqual(
            self.movie_conf.find_object(
                query="Mad Max 1984"
            ),
            self.m
        )

        self.assertEqual(
            self.movie_conf.find_object(
                query=unicode(self.m.pk)
            ),
            self.m
        )

        self.assertEqual(
            self.movie_conf.find_object(
                query="mad-max-1984"
            ),
            self.m
        )

        # Falls back to __startswith if the object
        # can not be found.
        self.assertEqual(
            self.movie_conf.find_object(
                query="mad-max-1984"
            ),
            self.m
        )

        # Non-public movies can not be smartlinked to.

        # TODO -- so apparently our public-queryset
        # thing isn't working.
        self.assertRaises(
            IndexEntry.DoesNotExist,
            lambda: self.movie_conf.find_object(
                "Secret Movie"
            )
        )

        # We don't want the smartlink resolved
        # when there is an ambiguity.
        self.assertRaises(
            IndexEntry.MultipleObjectsReturned,
            lambda: self.movie_conf.find_object(
                "Dirty Harry"
            )
        )

        self.assertEqual(
            self.movie_conf.find_object(
                query="Dirty Harry: 1976"
            ),
            self.harry2
        )

    def testUpdateIndexForObject(self):
        # Dirty Harry 1971 would have:
        expected_entries = (
            u'dirtyharry',
            u'dirtyharry1971',
            unicode(self.harry1.pk),
            u'dirtyharryreleasedin1971',
        )

        # Let's check items first.
        indexed_entries = lambda: IndexEntry.objects.filter(
            content_type = ContentType.objects.get_for_model(Movie),
            object_id = self.harry1.pk
        )

        self.assertItemsEqual(
            expected_entries,
            [i.value for i in indexed_entries()]
        )

        # Signal for deleting the object.
        self.movie_conf.update_index_for_object(Movie,
            self.harry1,
            created='deleteme')

        # Now nothing should be stored in the index.
        self.assertItemsEqual(
            [],
            indexed_entries()
        )

        # And let's test creation.
        self.movie_conf.update_index_for_object(Movie,
            self.harry1,
            created=True
        )

        # Now they should be equal back again.
        self.assertItemsEqual(
            expected_entries,
            [i.value for i in indexed_entries()]
        )

        # And let's test editing.
        self.harry1.title = "Awesome Harry"
        self.harry1.slug = "awesome-harry"

        expected_entries = (
            u'awesomeharry',
            u'awesomeharry1971',
            unicode(self.harry1.pk),
            u'awesomeharryreleasedin1971',
        )

        # ...and the editing should work as well.
        self.movie_conf.update_index_for_object(Movie,
            self.harry1,
            created=False
        )


        self.assertItemsEqual(
            expected_entries,
            [i.value for i in indexed_entries()]
        )