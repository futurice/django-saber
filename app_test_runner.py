#!/usr/bin/env python
import os
import sys

from optparse import OptionParser

from django.conf import settings
from django.core.management import call_command

import django

APP = 'djangosaber'
TEST_APP = 'test_project'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(os.path.dirname(__file__), "templates"),
        ],
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ]
        },
    },
]

def main():
    parser = OptionParser()
    parser.add_option("--DATABASE_ENGINE", dest="DATABASE_ENGINE", default="sqlite3")
    parser.add_option("--DATABASE_NAME", dest="DATABASE_NAME", default="sqlite.db")
    parser.add_option("--DATABASE_USER", dest="DATABASE_USER", default="")
    parser.add_option("--DATABASE_PASSWORD", dest="DATABASE_PASSWORD", default="")
    parser.add_option("--SITE_ID", dest="SITE_ID", type="int", default=1)
    parser.add_option("--cmd", dest="cmd", default="test")
    parser.add_option("--cmdargs", dest="cmdargs", default="")
    options, args = parser.parse_args()

    if options.cmdargs:
        args += options.cmdargs.split(',')
    
    try:
        app_path = args[0]
    except IndexError:
        raise SystemExit("Usage: app_test_runner.py [path-to-app] [app-test-case]")
    else:
        if app_path.endswith("/"):
            app_path = app_path[:-1]
        parent_dir, app_name = os.path.split(app_path)
        sys.path.insert(0, parent_dir)
    
    settings.configure(**{
        "DATABASES": {
            'default': {
                "ENGINE": 'django.db.backends.%s' % options.DATABASE_ENGINE,
                "NAME": options.DATABASE_NAME,
                "USER": options.DATABASE_USER,
                "PASSWORD": options.DATABASE_PASSWORD,
            }
        },
        "DEBUG": True,
        "ALLOWED_HOSTS": ['*'],
        "USE_TZ": True,
        "SITE_ID": options.SITE_ID,
        "ROOT_URLCONF": "{0}.urls".format(TEST_APP),
        "TEMPLATES": TEMPLATES,
        "INSTALLED_APPS": (
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.sites",

            "django_extensions",

            APP,
            TEST_APP,
        ),
        "MIDDLEWARE_CLASSES": (),
    })

    if django.VERSION[:2] >= (1, 7):
        django.setup()

    call_command(options.cmd, *args[1:])

if __name__ == "__main__":
    main()
