Changelog
=========

1.1.0
------

* renamed ``Dependency.async`` to ``Dependency.async_``.
  Fix for `#16 <https://github.com/lehins/django-smartfields/issues/16>`_.
  Thanks `@zglennie <https://github.com/zglennie>`_
* Fix compatibility with ``Django=2.x``:

  * Added ``app_name='smartifelds'`` to ``urls.py`` file
  * Stop using ``_size`` and ``_set_size()`` attributes in ``NamedTemporaryFile``,
    since those where only available in ``Django=1.x``

1.0.7
-----

* added ``gis`` fields.
* made ``lxml`` a default parser for HTMLProcessor.

1.0.6
-----

* added ``RenameFileProcessor``

1.0.5
-----

* minor bug fixes.

1.0.4
-----

* Switched to MIT License
* Added ``stashed_value`` to processors.

1.0.3
-----

* Added support for ``Wand`` with ``WandImageProcessor``.
* Made it compatible with Django 1.8
* Updated compiled JavaScript file.

1.0.2
-----

* Introduced ``pre_processor``.
* Made ``UploadTo`` serializible.
* Got rid of custom handlers.
* Minor bugfixes.

1.0.0
-----

* Initial release
