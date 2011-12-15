from django.utils.safestring import SafeString
import re

from django.test import TestCase
from django.template.context import Context

from smartlinks.parser import SmartLinkParser, SmartEmbedParser, Parser
from smartlinks.index_conf import IndexConf
from smartlinks.models import IndexEntry


class MyIndexConf(IndexConf):
    def __init__(self):
        pass

    def find_object(self, query):
        if query == "no such object":
            raise IndexEntry.DoesNotExist()
        if query == "more then one":
            raise IndexEntry.MultipleObjectsReturned()
        return "Object: %s" % query

class ParserTest(TestCase):
    def setUp(self):
        self.conf = MyIndexConf()
        self.p = Parser(dict(
            movie=self.conf,
            m=self.conf
        ))

    def testProcessSmartLinks(self):
        input_text = "hello1 hello2 hello3"
        self.p.parse = lambda match: "*"
        self.p.finder = re.compile(r"\w+")
        out = self.p.process_smartlinks(input_text)

        self.assertIsInstance(out, SafeString)

        self.assertEqual(
            out,
            "* * *"
        )

    def testParseNormal(self):
        self.p.parse(self._create_match(
            model="movie",
            query=" Mad Max ",
            verbose_text="    the awesome movie   "
        ))

        self.assertIsInstance(
            self.p.conf,
            MyIndexConf
        )

        self.assertEquals(
            self.p.obj,
            "Object: Mad Max"
        )

        self.assertEquals(
            self.p.template,
            IndexConf.template
        )

        # TODO - error
        self.assertEqual(
            self.p.verbose_text,
            "the awesome movie"
        )

        self.p.parse(self._create_match(
            model="movie",
            query=" Mad Max ",
        ))

        # If no verbose text is provided, the query itself is used.
        self.assertEqual(
            self.p.verbose_text,
            "Mad Max"
        )

    def testParseAmbiguous(self):
        ret = self.p.parse(
            SmartLinkParser.finder.match(
                "[[ movie->more then one | the awesome movie ]]")
        )

        self.assertEqual(
            ret,
            IndexConf.ambiguous_template.render(
                Context(dict(
                    verbose_text="the awesome movie"
                ))
            )
        )

    def testParseNoModel(self):
        smartlink = "[[ photo->Mad Max ]]"

        match = SmartLinkParser.finder.match(smartlink)

        ret = self.p.parse(match)

        self.assertEqual(
            ret,
            IndexConf.model_unresolved_template.render(
                Context(dict(
                    smartlink_text=smartlink,
                    verbose_text="Mad Max",
                    query="photo"
                ))
            )
        )

    def testParseNotFound(self):
        ret = self.p.parse(self._create_match(
            model="movie",
            query=" no such object ",
            verbose_text="    the awesome movie   "
        ))

        # Early bail out, the object was not found =>
        # unresolved template is rendered.
        self.assertEqual(
            ret,
            IndexConf.unresolved_template.render(
                Context(dict(
                    verbose_text="the awesome movie"
                ))
            )
        )

    def testParseNoModel(self):
        self.p.parse(self._create_match(
            query=" obj ",
            verbose_text="    the awesome movie   "
        ))
        self.assertEqual(
            self.p.conf,
            self.conf
        )
        self.assertEqual(
            self.p.template,
            self.conf.template
        )

    def testParseNoConfig(self):
        poor_parser = Parser({})
        self.assertEqual(poor_parser.parse(SmartLinkParser.finder.match(
                "[[ mad max ]]")),
            IndexConf.model_unresolved_template.render(Context({
                'verbose_text': 'mad max'
            }))
        )

    def _create_match(self, model=None, query="", verbose_text=None):
        return type(
            "Match",
            (object,),
            {
                "group": lambda self, key: dict(
                    ModelName=model,
                    Query=query,
                    VerboseText=verbose_text
                )[key],
                "groupdict": lambda self: dict(
                    ModelName=model,
                    Query=query,
                    VerboseText=verbose_text
                )
            }
        )()


class SmartLinkParserTest(TestCase):
    def setUp(self):
        self.p = SmartLinkParser({
            "m": MyIndexConf()
        })

    def testRegexp(self):
        m = SmartLinkParser.finder

        self.assertEqual(
            m.match("[[ Mad max ]]").group('Query').strip(),
            "Mad max"
        )

        self.assertEqual(
            m.match("ModelName"),
            None
        )

        match = m.match("[[ Mad max: beyond thunderdome | Mad max 3 ]]")
        self.assertEqual(
            match.group("Query").strip(),
            "Mad max: beyond thunderdome"
        )

        self.assertEqual(
            match.group("VerboseText").strip(),
            "Mad max 3"
        )

        self.assertEqual(
            match.group("ModelName"),
            None
        )

        match = m.match("[[ e->Mad Max ]]")

        self.assertEqual(
            match.group("ModelName").strip(),
            "e"
        )

        self.assertEqual(
            match.group("Query").strip(),
            "Mad Max"
        )

        match = m.match("[[ Event -> Mad Max | Beyond Thunderdome Fan Convention ]]")

        self.assertEqual(
            match.group("ModelName").strip(),
            "Event"
        )

        self.assertEqual(
            match.group("Query").strip(),
            "Mad Max"
        )

        self.assertEqual(
            match.group("VerboseText").strip(),
            "Beyond Thunderdome Fan Convention"
        )

        # First slash stops the matching
        self.assertEqual(
            m.match(r"\[[ Mad Max ]]"), None
        )


    def testParse(self):
        # Test bailing out.
        self.assertEqual(
            self.p.parse(SmartLinkParser.finder.match("[[ no such object ]]")),
            IndexConf.model_unresolved_template.render(
                Context(dict(
                    verbose_text="no such object",
                ))
            )
        )

        # Test normal running.
        self.assertEqual(
            self.p.parse(SmartLinkParser.finder.match("[[ Mad Max ]]")),
            IndexConf.template.render(
                Context(dict(
                    verbose_text="Mad Max",
                    obj="Object: Mad Max"
                ))
            )
        )

class SmartEmbedParserTest(TestCase):
    def setUp(self):
        self.p = SmartLinkParser({
            "m": MyIndexConf()
        })

    def testRegexp(self):
        m = SmartEmbedParser.finder

        match = m.match("{{ Mad Max | image }}")

        self.assertEqual(
            match.group("Query").strip(),
            "Mad Max"
        )

        self.assertEqual(
            match.group("AttrName").strip(),
            "image"
        )

        match = m.match("{{ Film->Mad Max | Image | crop }}")

        self.assertEqual(
            match.group("ModelName").strip(),
            "Film"
        )

        self.assertEqual(
            match.group("Query").strip(),
            "Mad Max"
        )

        self.assertEqual(
            match.group("AttrName").strip(),
            "Image"
        )

        self.assertEqual(
            match.group("Options").strip(" |"),
            "crop"
        )

        match = m.match("{{ Mad Max | Image | crop | size = 300 }}")

        self.assertEqual(
            match.group("Options").strip(" |"),
            "crop | size = 300"
        )

        # Slash stops matching like before.
        self.assertEqual(
            m.match(r"\{{ Mad Max | Image }}"),
            None
        )

    def testParse(self):
        m = SmartEmbedParser.finder

        class TestEmbedIndexConf(IndexConf):
            def find_object(self, query):
                if query == "no such object":
                    raise IndexEntry.DoesNotExist()
                return type("MyObject", (object,), dict(
                    image=lambda self, *args, **kw: (args, kw),
                ))()

        parser = SmartEmbedParser({
            "movie": TestEmbedIndexConf(
                embeddable_attributes=("image", "video")
            )
        })
        
        # Test bailing out early.
        self.assertEqual(
            parser.parse(m.match("{{ no such object | image }}")),
            TestEmbedIndexConf.model_unresolved_template.render(
                Context(dict(
                    verbose_text="no such object",
                ))
            )
        )

        # Test that options are parsed correctly
        match = m.match(
            "{{ Mad Max | image | size=300 | crop | alignment = north }}")

        # Mocked functions returns things it was passed to.
        self.assertEqual(parser.parse(match),
            (("crop",), {"size": "300", "alignment": "north"})
        )

        # Test unallowed attribute
        smartlink_text = "{{ Mad Max | unallowed_attribute }}"
        self.assertEqual(
            parser.parse(m.match(smartlink_text)),
            TestEmbedIndexConf.disallowed_embed_template.render(Context({
                'smartlink_text': smartlink_text
            }))
        )