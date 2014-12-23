#!/usr/bin/env python
import os, sys

test_dir = os.path.dirname(__file__)
sys.path.insert(0, test_dir)

import django
from django.conf import settings
from django.test.utils import get_runner

def runtests():
    os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.test_settings'
    if hasattr(django, 'setup'):
        django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["tests"])
    sys.exit(bool(failures))

if __name__ == "__main__":
    runtests()