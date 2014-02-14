import os
from django.db import models
from django.db.models.fields import files
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from smartfields.utils import from_string_import
from smartfields.models.fields import Field

__all__ = (
    "FileField", "ImageField", "ImageDependant", "VideoField",
    #"PDFField", "SmartHTMLField", "AudioField"
)

IMAGE_CONVERTER = from_string_import(
    getattr(settings, 'SMARTFIELDS_IMAGE_CONVERTER', 
            'smartfields.utils.image.ImageConverter'))

VIDEO_CONVERTER = from_string_import(
    getattr(settings, 'SMARTFIELDS_VIDEO_CONVERTER', 
            'smartfields.utils.video.VideoConverter'))


class FileFieldMixin(object):
    keep_orphans = getattr(settings, 'SMARTFIELDS_KEEP_ORPHANS', False)

    def sf_init(self, keep_orphans):
        if keep_orphans is not None:
            self.keep_orphans = keep_orphans

    def sf_save_form_data(self, instance, data):
        # remove file if it is marked to be cleared
        if data is not None and not self.keep_orphans:
            file = getattr(instance, self.attname)
            file.delete(save=False)

    
class FileField(models.FileField):
    keep_orphans = getattr(settings, 'SMARTFIELDS_KEEP_ORPHANS', False)

    def __init__(self, keep_orphans=None, upload_url=None, **kwargs):
        if keep_orphans is not None:
            self.keep_orphans = keep_orphans
        self.upload_url = upload_url
        print kwargs
        super(FileField, self).__init__(**kwargs)

    def save_form_data(self, instance, data):
        if data is not None and not self.keep_orphans:
            file = getattr(instance, self.attname)
            file.delete(save=False)
        super(FileField, self).save_form_data(instance, data)



class FileDependant(object):

    file_field_class = models.FileField

    @property
    def field_file_class(self):
        return self.file_field_class.attr_class

    def __init__(self, suffix, format=None, default=None, storage=None, 
                 storage_default=None, **kwargs):
        self.suffix = suffix
        self.format = format
        self.default = default
        self.storage = storage
        self.storage_default = storage_default or FileSystemStorage(
            location=settings.STATIC_ROOT, base_url=settings.STATIC_URL)
        self.extra_kwargs = kwargs
        self.extra_kwargs['format'] = format

    def get_attname(self, field):
        return "%s_%s" % (field.attname, self.suffix)

    def make_filename(self, original_file):
        if original_file:
            name, original_ext = os.path.splitext(original_file.name)
            if self.format is None:
                ext = original_ext
            else:
                ext = ".%s" % self.format
            return "%s_%s%s" % (name, self.suffix, ext.lower())
        return self.default

    def attach_file(self, instance, field_file):
        field = field_file.field
        filename = self.make_filename(field_file)
        if filename is None:
            new_field_file = None
        else:
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
        setattr(instance, self.get_attname(field), new_field_file)
        return new_field_file

    def handle_dependency(self, instance, field):
        return self.attach_file(instance, getattr(instance, field.attname))

            
class ImageDependant(FileDependant):

    file_field_class = models.ImageField


class DependantFieldFileMixin(object):

    def delete_dependants(self):
        if self and not self.field.keep_orphans and self:
            for d in self.field.dependencies:
                # getting the actual dependant field file
                f = getattr(self.instance, d.get_attname(self.field), None)
                if f:
                    try: 
                        f.delete(save=False)
                    except OSError: pass

    def update_dependants(self):
        converter = self.converter_class(self)
        for d in self.field.dependencies:
            new_file = d.attach_file(self.instance, self)
            content = converter.convert(**d.extra_kwargs)
            new_file.save(new_file.name, ContentFile(content), save=False)
            setattr(self.instance, d.get_attname(self.field), new_file)


class ImageFieldFile(files.ImageFieldFile, DependantFieldFileMixin):
    converter_class = IMAGE_CONVERTER

    def delete(self, **kwargs):
        self.delete_dependants()
        super(ImageFieldFile, self).delete(**kwargs)
    delete.alters_data = True


class ImageField(models.ImageField, FileField):
    attr_class = ImageFieldFile
    
    def __init__(self, keep_orphans=None, dependants=None, upload_url=None, **kwargs):
        self.dependencies = dependants or []
        super(ImageField, self).__init__(**kwargs)

    def contribute_to_class(self, cls, name):
        cls.smartfields_dependencies.append(self)
        super(ImageField, self).contribute_to_class(cls, name)

    def pre_save(self, model_instance, add):
        "Saves the file, updates dependants just before saving the model."
        file = super(models.FileField, self).pre_save(model_instance, add)
        if file and not file._committed:
            # Commit the file to storage prior to saving the model
            file.save(file.name, file, save=False)
            file.update_dependants()
        return file


class VideoField(FileField):
    pass