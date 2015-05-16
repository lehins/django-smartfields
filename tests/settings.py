from django.conf.global_settings import *
import os

BASE_PATH = os.path.dirname(__file__)

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
    'crispy_forms',
    'test_app',
    'test_suite',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware'
)

SITE_ID = 1

MEDIA_ROOT = os.path.join(BASE_PATH, 'media/')

MEDIA_URL = '/media/'

STATIC_ROOT = os.path.join(BASE_PATH, 'static/')

STATIC_URL = '/static/'

ROOT_URLCONF = 'tests.urls'

CRISPY_TEMPLATE_PACK = 'bootstrap3'
