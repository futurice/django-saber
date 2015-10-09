#!/usr/bin/env python
from setuptools import setup, find_packages, Command
from setuptools.command.test import test

import os, sys, subprocess

class TestCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        raise SystemExit(
            subprocess.call([sys.executable,
                             'app_test_runner.py',
                             'test_project']))

install_requires = ['cachetools>=1.1.3']
base_dir = os.path.dirname(os.path.abspath(__file__))

setup(
    name = "django-saber",
    version = "0.5",
    description = "Saber provides an in-memory replacement for the Django-ORM",
    url = "http://github.com/futurice/django-saber",
    author = "Jussi Vaihia",
    author_email = "jussi.vaihia@futurice.com",
    packages = ["djangosaber"],
    include_package_data = True,
    keywords = 'django model orm replacement inmemory performance fast calculations',
    license = 'BSD',
    install_requires = install_requires,
    cmdclass = {
        'test': TestCommand,
    },
)
