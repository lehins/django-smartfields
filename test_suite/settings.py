from django.conf.global_settings import *
import os, sys

BASE_PATH = os.path.dirname(__file__)

sys.path.insert(0, os.path.join(BASE_PATH, '..'))

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
    'django.contrib.sessions',
    'django.contrib.contenttypes',
    'django.contrib.sites',
    
    'smartfields',
    'sample_app',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ATOMIC_REQUESTS = True

SITE_ID = 1

MEDIA_ROOT = os.path.join(BASE_PATH, 'media/')

MEDIA_URL = '/media/'

STATIC_ROOT = os.path.join(BASE_PATH, 'static/')

STATIC_URL = '/static/'

ROOT_URLCONF = 'sample_app.urls'