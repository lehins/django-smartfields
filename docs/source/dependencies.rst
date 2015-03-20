============
Dependencies
============

.. class:: smartfields.dependencies.Dependency

    .. method:: __init__(attname=None, suffix=None, processor=None, pre_processor=None, async=False, default=NOT_PROVIDED, processor_params=None, uid=None)

    :keyword str attname: Name of an attribute or an existing field that
       dependecy will assign a value to. Cannot be used together with
       **suffix**.

    :keyword str suffix: Will be used together with a field name in generating
       an **attname** in format `field_name_suffix`. Generated name can refer to
       an attribute or an existing field that dependecy will assign a value
       to. Cannot be used together with **attname**.

    :keyword processor: A function that takes field's value as an argument or an
       instance of a class derived from
       :class:`~smartfields.processors.BaseProcessor`. In a latter case it will
       receive all arguments: ``value``, ``instance``, ``field``,
       ``field_value``, ``dependee``, ``stashed_value`` plus any custom
       kwargs. If a class is passed instead of it's instance it will be
       instantiated, to prevent a common mistake.

    :keyword pre_processor:

    :keyword async:

    :keyword default:

    :keyword processor_params:

    :keyword uid:
      

.. class:: smartfields.dependencies.FileDependency

   Because FileFields are handled in a different way then regular fields we need
   a different type of dependecy too.

    .. method:: __init__(upload_to='', storage=None, keep_orphans=KEEP_ORPHANS, **kwargs)

    :keyword upload_to:

    :keyword storage:

    :keyword keep_orphans:

    
