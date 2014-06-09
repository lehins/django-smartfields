import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models


__all__ = [
    "Dependency", "FileDependency", "MP4Dependency", "WEBMDependency"
]



class Dependency(object):
    handler = None
    processor_class = None

    def __init__(self, dependency=None, handler=None, persistent=True,
                 processor_class=None, **kwargs):
        """:class:`Dependency` is the actual smart class that allows you to
        specify any necessary handling and processing of field values that
        depend on other model fields. Any extra kwargs will be passed over to
        the :func:`BaseProcessor.process` so it is the way to customize an
        individual FieldProcessor behavior.

        :keyword str dependency: name of the field attached to the same `Model`
        that this field is dependent upon. In case iy is not specified it will
        be a self dependancy.

        :keyword function handler: a function that will handle the
        dependency. It should take model instance, field instance and field
        value as arguments and return new value of the field.

        :keyword bool persistent: if it set to False, handling will be turned off.

        :keyword BaseProcessor processor_class: class that will be instantiated
        and used later for field value processing. It takes precedence over
        :class:`Fieldmanager`s processor_class in Field processing.

        """
        self.dependency = dependency
        if callable(handler):
            self.handler = handler
        self.extra_kwargs = kwargs
        self.persistent = persistent
        if processor_class is not None:
            self.processor_class = processor_class


    def handle(self, instance, field, value):
        if not self.persistent:
            return value
        if self.dependency is not None:
            value = getattr(instance, self.dependency)
        if self.handler is not None:
            value = self.handler(instance, field, value)
        setattr(instance, field.name, value)
        return value


    def update(self, instance, field, value, processor=None):
        if self.dependency is not None:
            value = getattr(instance, self.dependency)
        if self.processor_class is not None: # override handlers processor
            processor = self.processor_class(value, field=field, instance=instance)
        if processor is not None:
            value = processor.process(**self.extra_kwargs)
        setattr(instance, field.name, value)




class ForwardDependency(Dependency):

    def __init__(self, dependency, **kwargs):
        """Reverses the dependency, another words, managed field becomes the
        field, that dependancy is dependant upon. Which enforces `dependency` to
        be a required argument.

        """

        self.forward_dependency = dependency
        super(ForwardDependency, self).__init__(**kwargs)

    def handle(self, instance, field, value):
        field = instance._meta.get_field(self.forward_dependency)
        super(ForwardDependency, self).handle(instance, field, value)

    def update(self, instance, field, value, processor=None):
        field = instance._meta.get_field(self.forward_dependency)
        super(ForwardDependency, self).update(instance, field, value, processor=processor)




class FileDependency(Dependency):

    _field_file = None
    _using_default = False
    file_field_class = models.FileField

    @property
    def field_file_class(self):
        return self.file_field_class.attr_class

    def __init__(self, suffix=None, default=None, storage=None,
                 storage_default=None, **kwargs):
        self.suffix = suffix
        kwargs['suffix'] = suffix
        self.format = kwargs.get('format', None)
        self.default = default
        self.storage = storage
        self.storage_default = storage_default or FileSystemStorage(
            location=settings.STATIC_ROOT, base_url=settings.STATIC_URL)
        super(FileDependency, self).__init__(**kwargs)

    def get_name(self, field):
        return "%s_%s" % (field.name, self.suffix)

    def make_filename(self, original_file):
        self._using_default = False
        if original_file:
            name, original_ext = os.path.splitext(original_file.name)
            if self.format is None:
                ext = original_ext
            else:
                ext = ".%s" % self.format
            return "%s_%s%s" % (name, self.suffix, ext.lower())
        if self.default:
            self._using_default = True
        return self.default

    def handle(self, instance, field, field_file):
        if self.suffix is None:
            return super(FileDependency, self).handle(
                instance, field, field_file)
        filename = self.make_filename(field_file)
        if field_file:
            storage = self.storage or field.storage
        else:
            storage = self.storage_default
        new_field_name = "%s_%s" % (field.name, self.suffix)
        new_field = self.file_field_class(
            upload_to=lambda instance, name: name,
            storage=storage, name=new_field_name)
        new_field_file = self.field_file_class(
            instance, new_field, filename)
        self._field_file = new_field_file
        return super(FileDependency, self).handle(
            instance, new_field, new_field_file)

    def delete(self):
        if self._field_file and not self._using_default:
            try:
                self._field_file.delete(save=False)
            except: # can raise OSError or any other exception, depends on backend
                if not self._field_file.field.FAIL_SILENTLY:
                    raise

    def update(self, instance, field, field_file, processor=None):
        if self.dependency is not None:
            value = getattr(instance, self.dependency)
        else:
            value = field_file
        #if not value:
        #    return
        if self.processor_class is not None:
           processor = self.processor_class(value, field=field, instance=instance)
        content = processor.process(**self.extra_kwargs)
        new_file = self.handle(instance, field, field_file)
        new_file.save(new_file.name, content, save=False)
        



class WEBMDependency(FileDependency):

    def __init__(self, *args, **kwargs):
        default_kwargs = {
            'cmd_template': (
                "ffmpeg -i {input} -y -codec:v {vcodec} -b:v {vbitrate} "\
                "-maxrate {maxrate} -bufsize {bufsize} -vf "\
                "scale={width}:{height} -threads {threads} -c:a {acodec} {output}"),
            'format': 'webm',
            'converter': 'avconv',
            'vcodec': 'libvpx',
            'vbitrate': '1M',
            'maxrate': '1M',
            'bufsize': '2M',
            'width': 'trunc(oh/a/2)*2', # make sure width is divisible by 2
            'height': 720,
            'threads': 4,
            'acodec': 'libvorbis',
            'abitrate': '96k'
        }
        default_kwargs.update(kwargs)
        super(WEBMDependency, self).__init__(*args, **default_kwargs)




class MP4Dependency(FileDependency):

    def __init__(self, *args, **kwargs):
        default_kwargs = {
            'cmd_template': (
                'ffmpeg -i {input} -y -c:v {vcodec} -b:v {vbitrate} -maxrate {maxrate} -bufsize '\
                '{bufsize} -vf scale={width}:{height} -threads {threads} -c:a '\
                '{acodec} -b:a {abitrate} {output}'),
            'format': 'mp4',
            'converter': 'avconv',
            'vcodec': 'libx264',
            'vbitrate': '1M',
            'maxrate': '1M',
            'bufsize': '2M',
            'width': 'trunc(oh/a/2)*2', # make sure width is divisible by 2
            'height': 720,
            'threads': 0,
            'acodec': 'libfdk_aac',
            'abitrate': '96k'
        }
        default_kwargs.update(kwargs)
        super(MP4Dependency, self).__init__(*args, **default_kwargs)