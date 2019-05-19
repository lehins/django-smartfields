django-smartfields
##################

.. image:: https://readthedocs.org/projects/django-smartfields/badge/?version=latest
   :target: https://readthedocs.org/projects/django-smartfields/?badge=latest
   :alt: Documentation Status

.. image:: https://img.shields.io/pypi/v/django-smartfields.svg
   :target: https://pypi.python.org/pypi/django-smartfields/
   :alt: Latest Version

.. image:: https://landscape.io/github/lehins/django-smartfields/master/landscape.png
   :target: https://landscape.io/github/lehins/django-smartfields/master
   :alt: Code Health

.. image:: https://img.shields.io/coveralls/lehins/django-smartfields.svg
   :target: https://coveralls.io/r/lehins/django-smartfields
   :alt: Tests Coverage

.. image:: https://travis-ci.org/lehins/django-smartfields.svg?branch=master
   :target: https://travis-ci.org/lehins/django-smartfields
   :alt: Travis-CI


Django Model Fields that are smart.
-----------------------------------

This app introduces a declarative way of handling fields' values. It can be
especially useful when one field depends on a value from another field, even if
a field depends on itself. At first it might sound useless, but, as it turns
out, it is an amazing concept that helps in writing clear, concise and DRY code.

Best way to describe is on a simple example. Let's say there is a field where
you store a custom html page and you would like to have another field attached
to the same model store the same page but with html tags stripped out, moreover
you would like it to update whenever the first field changes it's value. A
common way to handle that issue is to overwrite model's ``save`` method and put
all the logic there, right? What if you could just give a field a function that
does the stripping and everything else is taking care of? Wouldn't that be nice,
huh?  Well, that's one of many things this app let's you do.

Another great example is django's ``ImageField`` that can update ``width_field``
and ``height_field`` whenever image is changed. This app uses similar concepts
to achive that functionality. But here is a more powerful example that
demonstrates the value of this app. Let's say you would like to have a user be
able to upload an image in any format and automatically add another version of
this image converted to JPEG and shrunk to fit in a box size of 1024x768. Here
is how it could look with utilization of `django-smartfields`:

.. code-block:: python

    from django.db import models

    from smartfields import fields
    from smartfields.dependencies import FileDependency
    from smartfields.processors import ImageProcessor

    class User(models.Model):
        # ... more fields ....
        avatar = fields.ImageField(upload_to='avatar', dependencies=[
            FileDependency(attname='avatar_jpeg', processor=ImageProcessor(
                format='JPEG', scale={'max_width': 1024, 'max_height': 768})),
        ])
        avatar_jpeg = fields.ImageField(upload_to='avatar')
        # ... more fields ...

That's it. Did I mention that it will also clean up old files, when new ones are
uploaded?

So, hopefully I got you convinced to give this app a try. There is full
documentation also on the way, but for now you can check out 'tests' folder for
some examples.

Django settings
---------------

Required django apps for most of the functionality:

.. code-block:: python

    INSTALLED_APPS = [
        'django.contrib.auth',
        'django.contrib.sessions',
        'django.contrib.contenttypes',
        'django.contrib.sites',

        'smartfields',

        # optional, needed for forms
        'crispy_forms'
    ]

Other required settings

.. code-block:: python

    MIDDLEWARE = [
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware'
    ]

    SITE_ID = 1

Dependencies
------------
* `Django <https://djangoproject.com/>`_ versions >= 1.7 (should aslo work for 2.x)
* `Python Pillow <https://pillow.readthedocs.org>`_ - (optional) used for
  image conversion/resizing. AND/OR
* `Wand <http://docs.wand-py.org>`_ - (optional) also for image processing.
* `ffmpeg <https://www.ffmpeg.org/>`_ - (optional) for video conversion. (can
  be easily adopted for `avconv <https://libav.org/avconv.html>`_).
* `BeautifulSoup4 <https://pypi.python.org/pypi/beautifulsoup4/>`_ - (optional)
  for HTML stripping
* `lxml <https://pypi.python.org/pypi/lxml>`_ - (optional) for BeautifulSoup.
* `django-crispy-forms
  <https://readthedocs.org/projects/django-crispy-forms/>`_ - (optional) for
  ajax uploading.
* `Plupload <http://www.plupload.com/>`_ - (optional) for ajax uploading.
* `Bootstrap3 <http://getbootstrap.com/>`_ - (optional) for ajax uploading.
