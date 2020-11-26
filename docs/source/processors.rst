==========
Processors
==========

.. class:: smartfields.processors.BaseProcessor

    .. method:: __init__(**kwargs)

    .. method:: process(value, instance=None, field=None, dependee=None, stashed_value=None, **kwargs)

    :param value: New value that is being assigned to the parent field.
    :keyword instance: Model instance that a field is attached to.
    :keyword field: Parent field instance.
    :keyword dependee: Instance of a field that depends on the ``field``. It is
                       decided by the ``attname`` or ``suffix`` argument to the
    :keyword stashed_value: This is a previous value that a ``dependee`` field was
                            holding. Very useful for comparing it to new values.


.. class:: smartfields.processors.BaseFileProcessor

    .. method:: get_ext(format=None, **kwargs)



.. class:: smartfields.processors.RenameFileProcessor



.. class:: smartfields.processors.ExternalFileProcessor

    .. method:: __init__(self, cmd_template=None, sleep_time=1, custom_input_path_getter=None, **kwargs)
    :keyword cmd_template: Command template
    :keyword sleep_time: Interval at which to pipe the output from external process
    :keyword custom_input_path_getter: An optional function that will be invoked upon
                                       getting an input file name, i.e. overwrites
                                       behavior of ``get_file_path``



.. class:: smartfields.processors.FFMPEGProcessor

    .. method:: __init__()

    .. method:: process(value, **kwargs)


Here is an examlple of how to convert a video to MP4 format. In this example
every time ``MediaModel`` is instantiated
:class:`~smartfields.dependencies.FileDependency` will automatically attach
another field like attribute to the model ``video_mp4``. Moreover, whenever a
new video file is uploaded or simply assigned to a ``video`` field, it will use
:class:`~smartfields.processors.FFMPEGProcessor` and ``ffmpeg`` to convert
that video file to mp4 format and will assign it the same name as original video
with ``mp4`` suffix and file extension. While converting a video file it will
set progress between 0.0 and 1.0, which can be retrieved from field's status.

.. code-block:: python

   from django.db import models
   from smartfields import fields, dependencies
   from smartfields.processors import FFMPEGProcessor

   class MediaModel(models.Model):
       video = fields.FileField(dependencies=[
           dependencies.FileDependency(suffix='mp4', processor=FFMPEGProcessor(
               vbitrate = '1M',
               maxrate = '1M',
               bufsize = '2M',
               width = 'trunc(oh*a/2)*2', # http://ffmpeg.org/ffmpeg-all.html#scale
               height = 720,
               threads = 0, # use all cores
               abitrate = '96k',
               format = 'mp4',
               vcodec = 'libx264',
               acodec = 'libfdk_aac'))])


Note that sometimes it is required to overwrite the storage behavior, in which case input
path might need to be adjusted. Here is how it can be achieved, while extending the
example above:


.. code-block:: python

   from storages.backends.s3boto3 import S3Boto3Storage

   class MediaModel(models.Model):
       video = fields.FileField(storage=S3Boto3Storage(), dependencies=[
           dependencies.FileDependency(suffix='mp4', processor=FFMPEGProcessor(
               custom_input_path_getter=lambda in_file: in_file.instance.file.url,
               ...
