import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models


__all__ = [
    "Dependency", "FileDependency", "MP4Dependency", "WEBMDependency"
]

FAIL_SILENTLY = getattr(settings, 'SMARTFIELDS_FAIL_SILENTLY', True)


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
           processor = self.processor_class(value)
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
    file_field_class = models.FileField

    @property
    def field_file_class(self):
        return self.file_field_class.attr_class

    def __init__(self, suffix, default=None, storage=None,
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
        if original_file:
            name, original_ext = os.path.splitext(original_file.name)
            if self.format is None:
                ext = original_ext
            else:
                ext = ".%s" % self.format
            return "%s_%s%s" % (name, self.suffix, ext.lower())
        return self.default

    def handle(self, instance, field, field_file):
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
        if self._field_file:
            try:
                self._field_file.delete(save=False)
            except OSError:
                if not FAIL_SILENTLY:
                    raise

    def update(self, instance, field, field_file, processor=None):
        if self.processor_class is not None:
           processor = self.processor_class(field_file)
        content = processor.process(**self.extra_kwargs)
        new_file = self.handle(instance, field, field_file)
        new_file.save(new_file.name, content, save=False)




class WEBMDependency(FileDependency):

    def __init__(self, *args, **kwargs):
        default_kwargs = {
            'cmd_template': (
                "avconv -i {input} -y -codec:v {vcodec} -b:v {vbitrate} -qmin "\
                "10 -qmax 42 -maxrate {maxrate} -bufsize {bufsize} -vf "\
                "scale={width}:{height} -threads {threads} -codec:a {acodec} -b:a "\
                "{abitrate} {output}"),
            'format': 'webm',
            'converter': 'avconv',
            'vcodec': 'libvpx',
            'vbitrate': '300k',
            'maxrate': '300k',
            'bufsize': '600k',
            'width': 640,
            'height': -1,
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
                'avconv -i {input} -y -codec:v {vcodec} -vprofile {vprofile} '\
                '-preset {preset} -b:v {vbitrate} -maxrate {maxrate} -bufsize '\
                '{bufsize} -vf scale={width}:{height} -threads {threads} -codec:a '\
                '{acodec} -b:a {abitrate} {output}'),
            'format': 'mp4',
            'converter': 'avconv',
            'vcodec': 'libx264',
            'vprofile': 'main',
            'preset': 'medium',
            'vbitrate': '600k',
            'maxrate': '600k',
            'bufsize': '600k',
            'width': 640,
            'height': 'trunc(ow/a/2)*2', # fixes: height not divisible by 2
            'threads': 0,
            'acodec': 'libvo_aacenc',
            'abitrate': '96k'
        }
        default_kwargs.update(kwargs)
        super(MP4Dependency, self).__init__(*args, **default_kwargs)