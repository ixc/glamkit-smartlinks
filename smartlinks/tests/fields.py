from django.core.exceptions import ValidationError
from django.test import TestCase
from django.template.base import Template
from django.template.context import Context

from smartlinks import register_smart_link
from smartlinks.fields import SmartLinkFormField
from smartlinks.conf import SmartLinkConf
from smartlinks.templatetags.smartlinks import smartlinks
import smartlinks.conf as conf

from .models import Movie2, LinkModel

class SmartLinkFieldTest(TestCase):
    def setUp(self):
        if not 'zzz' in conf.smartlinks_conf:
            register_smart_link(('zzz',), SmartLinkConf(queryset=Movie2.objects,
                searched_fields=('title', 'slug',),))

        self.l = LinkModel(link=u'[[ my awesome Movie2 | Terrible ]]')

    def tearDown(self):
        pass

    def testValidation(self):
        f = SmartLinkFormField()
        self.assertRaises(ValidationError, f.clean, '[][][][]')
        self.assertEqual(f.clean(' [[ hello]]'), '[[ hello]]')
        self.assertEqual(f.clean('hello'), '[[ hello ]]')
        self.assertEqual(f.clean(' [[ model->hello|description]]'),
                         '[[ model->hello|description]]')

        f = SmartLinkFormField(verify_exists=True)
        self.assertRaises(ValidationError, f.clean, '[[ zzz->hello ]]')

        Movie2.objects.create(title='hello', slug='hello', year=3999)
        # Now register the smartlink and check that it checks out OK.
        self.assertEqual(f.clean('[[ zzz->hello ]]'), '[[ zzz->hello ]]')

    def testQuiteFailure(self):
        # Empty ``link`` field shouldn't raise any errors.
        l = LinkModel.objects.create()
        self.assertEqual(
            l.link.url,
            u""
        )

        self.assertEqual(
            l.link.object,
            None
        )

        # Problematic smartlink shouldn't raise any errors either.
        l = LinkModel.objects.create(link='[[ lsdfjlkdjfg->sdfsdfdf ]]')
        self.assertEqual(
            l.link.url,
            u""
        )

        self.assertEqual(
            l.link.object,
            None
        )

    def testTemplateRendering(self):
        self.m = Movie2.objects.create(
            title='My Movie2',
            slug='my-awesome-Movie2',
            year=2001
        )

        self.assertEqual(Template("{{ obj.link.url }}").render(
            Context({'obj': LinkModel(link="[[ zzz->my Movie2 ]]")})),
            self.m.get_absolute_url()
        )

    def testDescriptor(self):
        self.m = Movie2.objects.create(
            title='My Movie2',
            slug='my-awesome-Movie2',
            year=2001
        )

        l = LinkModel.objects.create(link=u"[[ zzz->my Movie2 ]]")
        pk = l.pk
        self.assertEqual(
            LinkModel.objects.get(pk=pk).link.raw,
            u"[[ zzz->my Movie2 ]]"
        )

        l.link = u"[[ my hated Movie2 ]]"
        l.save()
        self.assertEqual(
            LinkModel.objects.get(pk=pk).link.raw,
            u"[[ my hated Movie2 ]]"
        )

        self.assertEqual(
            l.link.raw,
            u"[[ my hated Movie2 ]]"
        )

    def testUrl(self):
        self.m = Movie2.objects.create(
            title='My Movie2',
            slug='my-awesome-Movie2',
            year=2001
        )

        self.assertEqual(
            self.l.link.url,
            self.m.get_absolute_url()
        )

    def testVerboseText(self):
        self.assertEqual(
            self.l.link.verbose_text,
            u"Terrible"
        )

    def testGetObject(self):
        self.m = Movie2.objects.create(
            title='My Movie2',
            slug='my-awesome-Movie2',
            year=2001
        )

        self.assertEqual(
            self.l.link.object,
            self.m
        )

    def testRenderedLink(self):
        self.m = Movie2.objects.create(
            title='My Movie2',
            slug='my-awesome-Movie2',
            year=2001
        )

        self.assertEqual(
            self.l.link.rendered_link,
            smartlinks(self.l.link.raw)
        )

    def testLen(self):
        self.m = Movie2.objects.create(
            title='My Movie2',
            slug='my-awesome-Movie2',
            year=2001
        )

        self.assertEqual(
            len(self.l.link),
            len(self.m.get_absolute_url())
        )
