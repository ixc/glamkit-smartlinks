from django.test import TestCase
from django.template import Context, Template

from ...tests.models import Movie
from ...parser import SmartLinkParser
from ...conf import SmartLinkConf
from .. import register_smart_link


class SmartLinksMainTest(TestCase):
    """
    A simple integration test.
    """

    def setUp(self):
        self.template =Template("""{% load smartlinks %}
{{ smartlink|smartlinks }}
{{ smartembed|smartlinks }}
""".replace('\n', ''))

        register_smart_link(('m',), SmartLinkConf(Movie.objects,
        embeddable_attributes=('image',)))

        self.m = Movie.objects.create(
            title="Mad Max",
            slug="mad-max",
            year="1986"
        )


        self.smartlink = '[[ Mad Max::: ]]'
        self.smartembed = '{{ Mad Max | image }}'

        self.context = Context({
            'smartlink': self.smartlink,
            'smartembed': self.smartembed
        })

    def testFilter(self):
        self.assertEqual(
            self.template.render(self.context),
            SmartLinkParser(
                    {'m': SmartLinkConf(Movie.objects)}
                ).parse(
                SmartLinkParser.finder.match(self.smartlink)) + self.m.image()
        )