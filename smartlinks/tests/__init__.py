from django.test import TestCase
from django.db import models

from smartlinks.index_conf import SmartLinkConf
from smartlinks import register, register_smart_link,\
    IncorrectlyConfiguredSmartlinkException, AlreadyRegisteredSmartlinkException

from .templatetags import *
from .index_conf import *
from .models import *
from .parser import *
from .management import *

import smartlinks.index_conf as index_conf

class Event(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)

    def my_favourite_func(self, arg):
        pass

    def my_func_without_args(self):
        pass

    def get_image(self):
        pass

    def get_video(self):
        pass



class RegistrationTest(TestCase):
    def setUp(self):
        while index_conf.smartlinks_conf.keys():
            index_conf.smartlinks_conf.pop(
                index_conf.smartlinks_conf.keys()[0])

    def tearDown(self):
        # Clean global configuration.
        while index_conf.smartlinks_conf.keys():
            index_conf.smartlinks_conf.pop(
                index_conf.smartlinks_conf.keys()[0])


    def testRegisterLinks(self):
        conf = SmartLinkConf(queryset=Event.objects)
        smartlinks_conf = register(
            (('e', 'event'), conf),
            (('m', 'movie'), conf)
        )

        self.assertEqual(smartlinks_conf,
            {
                'e': conf,
                'event': conf,
                'm': conf,
                'movie': conf
            }
        )

    def testRegisterLink(self):
        conf = SmartLinkConf(queryset=Event.objects)

        smartlinks_conf = register_smart_link(
            ('e', 'event'), conf)

        self.assertEqual(smartlinks_conf, {
            'e': conf,
            'event': conf
        })

        # TODO -- check sending/receiving signals

    def testSanityChecks(self):
        # No such field on the model => exception.
        self.assertRaises(IncorrectlyConfiguredSmartlinkException,
            register_smart_link,
            ('e',),
            SmartLinkConf(Event.objects, searched_fields=('blah',)))

        # Searched field is a function with too many argument => exception.
        self.assertRaises(IncorrectlyConfiguredSmartlinkException,
            register_smart_link,
            ('e'),
            SmartLinkConf(Event.objects, searched_fields=('my_favourite_func')))

        # While registering the callable with no args should work just fine.
        register_smart_link(('zzz',), SmartLinkConf(Event.objects,
                                        searched_fields=('my_func_without_args',)))

        # We also can't register the model with same shortcut twice.
        self.assertRaises(AlreadyRegisteredSmartlinkException,
            register_smart_link,
            ('zzz',), SmartLinkConf(Event.objects))
