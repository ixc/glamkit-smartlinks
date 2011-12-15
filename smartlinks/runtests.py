#!/usr/bin/env python
import sys, os

from django.conf import settings


DIRNAME = os.path.dirname(__file__)

sys.path.insert(0, os.path.abspath(os.path.join(DIRNAME, "../")))

settings.configure(DEBUG = True,
   DATABASE_ENGINE = 'sqlite3',
   DATABASE_NAME = os.path.join(DIRNAME,
                                'database.db'),

   INSTALLED_APPS = (
       'smartlinks',
       'django_nose',
       'smartlinks.tests',
       'django.contrib.contenttypes')
)

#nose.main(argv=None)

from django_nose import NoseTestSuiteRunner
from django.test.simple import run_tests

failures = run_tests(['smartlinks',], verbosity=1)
if failures:
    sys.exit(failures)

#NoseTestSuiteRunner().run_tests(['smartlinks'])