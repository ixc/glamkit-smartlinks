from django.test import TestCase
from django.template import Context, Template

from ...tests.models import Movie
from ...parser import SmartLinkParser
from ...index_conf import IndexConf


class SmartLinksMainTest(TestCase):
    """
    A simple integration test.
    """

    def setUp(self):
        self.template =Template("""{% load smartlinks %}
{{ smartlink | smartlinks }}
{{ smartembed | smartlinks }}
""".replace('\n', ''))

        self.m = Movie.objects.create(
            title="Mad Max",
            slug="mad-max",
            year="1986"
        )

        self.smartlink = '[[ Mad Max ]]'
        self.smartembed = '{{ Mad Max | image }}'

        self.context = Context({
            'smartlink': self.smartlink,
            'smartembed': self.smartembed
        })

    def testFilter(self):
        out = self.template.render(self.context)
        self.assertEqual(
            out,
            SmartLinkParser(
                    {'m': IndexConf(Movie.objects)}
                ).parse(
                SmartLinkParser.finder.match(self.smartlink)) + self.m.image()
        )