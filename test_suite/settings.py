from django.conf.global_settings import *
import os, sys

BASE_PATH = os.path.join(os.path.dirname(__file__), '..')

sys.path.insert(0, BASE_PATH)

DEBUG = False
SECRET_KEY = 'django-smartfields'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    }
}


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.admin',
    'django.contrib.sites',
    
    'smartfields',
    'sample_app',
)

SITE_ID = 1
