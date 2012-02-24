from django.core.exceptions import ValidationError
from django.test import TestCase
from django.db import models

from smartlinks import register_smart_link
from smartlinks.fields import SmartLinkFormField, SmartLinkField
from smartlinks.conf import SmartLinkConf
import smartlinks.conf as conf

from .models import Movie

class MySmartLinkConf(SmartLinkConf):
    def find_object(self, query):
        return 'object'

class MyModel(models.Model):
    link = SmartLinkField(max_length=200)

class SmartLinkFieldTest(TestCase):
    def setUp(self):
        register_smart_link(('z',), MySmartLinkConf(
            queryset=MyModel.objects,
            searched_fields=()))

        register_smart_link(('u'), SmartLinkConf(queryset=Movie.objects, searched_fields=('title',)))

    def tearDown(self):
        # Clean global configuration.
        while conf.smartlinks_conf.keys():
            conf.smartlinks_conf.pop(
                conf.smartlinks_conf.keys()[0])

    def testValidation(self):
        f = SmartLinkFormField()
        self.assertRaises(ValidationError, f.clean, '[][][][]')
        self.assertEqual(f.clean(' [[ hello]]'), '[[ hello]]')
        self.assertEqual(f.clean('hello'), '[[ hello ]]')
        self.assertEqual(f.clean(' [[ model->hello|description]]'),
                         '[[ model->hello|description]]')

        f = SmartLinkFormField(verify_exists=True)
        self.assertRaises(ValidationError, f.clean, '[[ q->hello ]]')
        register_smart_link(('q',), MySmartLinkConf(
            queryset=MyModel.objects,
            searched_fields=()))

        # Now register the smartlink and check that it checks out OK.
        self.assertEqual(f.clean('[[ q->hello ]]'), '[[ q->hello ]]')

    def testMagicUrlField(self):
        # <fieldname>_url() should appear and it should work properly.
        m = MyModel(link='[[ google.com ]]')

        # No such object => empty string.
        self.assertEqual('', m.get_link_url())

    def testMagicGetObjectField(self):
        m = Movie.objects.create(
            title='My Movie',
            slug='mymovie',
            year=2001
        )

        zz = MyModel(link='[[ u->mymovie ]]')
        self.assertEqual(zz.get_link_object(), m)

        # Correct handling of empty string, None, and
        # non-resolving string.
        zz.link = ''
        self.assertEqual(zz.get_link_object(), None)

        zz.link = None
        self.assertEqual(zz.get_link_object(), None)

        zz.link = ' '
        self.assertEqual(zz.get_link_object(), None)

