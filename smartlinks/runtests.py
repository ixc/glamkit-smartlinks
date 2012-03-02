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

from django.test.simple import DjangoTestSuiteRunner

test_runner = DjangoTestSuiteRunner(verbosity=1,
    interactive=True,
    failfast=False)
failures = test_runner.run_tests(['smartlinks',], verbosity=1)

if failures:
    sys.exit(failures)