Welcome to django-smartfields's documentation!
==============================================

**Django Model Fields that are smart**

This application introduces a totally new way of handling field's values through
unique ways they are assigned and processed. It is so simple that nothing needs
to be done in order to start using it, yet it is so powerful, that it can handle
automatic image and video file conversions with a simple specification of a
conversion function. Check it out, and it will forever change the way you handle
Model Fields.

------------
Installation
------------
::

    pip install django-smartfields


------------
Latest build
------------

Forkme on Github: `django-smartfields <https://github.com/lehins/django-smartfields>`_

------------
Introduction
------------

Here is a short introduction of how this app works and a simple example how it
can be used.

First of all, as name suggests, it mainly deals with Model Fields, hence it is
supplied with a custom version of every Django's Field. There is no difference
form original versions of fields in terms of interaction with database, forms or
with any other Django codebase, so both kinds of fields can be used together
safely and interchangeably. Main distinction form Django's fields is that all
smartfields accept a keyword argument ``dependencies``, which should be a list
of :class:`Dependency's<smartfields.dependencies.Dependency>` or
:class:`FileDependency's<smartfields.dependencies.FileDependency>`.

`Dependency` is a concept that allows you to change the value of any field or an
attribute attached to the model instance, including the field `Dependency` which
it is specified for. Each `Dependency` handles the value from a field through
`Processors` which are functions that can be accepted as ``default``,
``pre_processor`` and ``processor`` kwargs. An actual model attribute or a field
which a processed value will be assigned to is specified by one or none of the
kwargs ``suffix`` and ``attname``. More details on those see documentation in
:doc:`dependencies` and :doc:`processors` sections,
but for now let's see a couple of simple examples.

Example
^^^^^^^

Let's say we have a Product model where a slug needs to be automatically
generated from product's name and also properly modified to look like a slug.

.. code-block:: python

    from django.db.models import models
    from django.utils.text import slugify
    from smartfields import fields
    from smartfields.dependencies import Dependency

    def name_getter(value, instance, **kwargs):
        return instance.name

    class Product(models.Model):
        name = models.CharField(max_length=255)
        slug = fields.SlugField(dependencies=[
            Dependency(default=name_getter, processor=slugify)
        ])

Here is what will happen in above example whenever an instance of ``Product``
is created:

    * Whenever ``Product`` is initilized and ``slug`` field is empty, it will
      attempt to get a value from ``name`` field. In case when it is still empty
      before model is being saved it will attempt to get the value again, all
      because of ``default`` function ``name_getter``.
    * Right before the model is saved ``processor`` function ``slugify`` will be
      invoked, and value of the field from ``name`` will be modified to look like
      a slug. Important part is, processor will be invoked only whenever the
      value of ``slug`` field has changed.

------------------------
Important Perculiarities
------------------------

* Fields are processed in order they are specified in a Model.
* Dependencies are processed in the order they are speciefied in the
  ``dependencies`` list, except the ones with ``async`` flag, these are
  processed last, but also in the order they were specified.


------------
More Details
------------

.. toctree::
   :maxdepth: 1

   dependencies
   processors

------------
Project Info
------------

.. toctree::
   :maxdepth: 1

   changelog
   authors
   license

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
