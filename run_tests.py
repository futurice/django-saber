import os, sys
from django.conf import settings

APP = 'djangosaber'
TEST_APP = 'test_project'

settings.configure(DEBUG=True,
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            }
        },
    ROOT_URLCONF="{0}.urls".format(APP),
    AUTH_USER_MODEL='{0}.User'.format(TEST_APP),
    INSTALLED_APPS=('django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.admin',

        APP,
        TEST_APP,))

from django.test.simple import DjangoTestSuiteRunner
test_runner = DjangoTestSuiteRunner(verbosity=1)
failures = test_runner.run_tests([TEST_APP,])
if failures:
    sys.exit(failures)
