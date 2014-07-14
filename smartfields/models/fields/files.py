import os, json
from django.db import models
from django.db.models.fields import files
from django.conf import settings

from smartfields.models.fields import Field
from smartfields.utils import from_string_import
from smartfields.models.fields.managers import *

__all__ = [
    "FileField", "ImageField", "VideoField"
]

class FieldFile(files.FieldFile):

    @property
    def state(self):
        return self.status['state']

    @property
    def status(self):
        return self.field.get_status(self.instance)

    @property
    def status_json(self):
        return json.dumps(self.status)

    @property
    def html_tag(self):
        if self.field.html_tag_getter is not None and callable(self.field.html_tag_getter):
            return self.field.html_tag_getter(
                file=self, field=self.field, instance=self.instance, is_empty=bool(self))
        return ''

    @property
    def name_base(self):
        if self:
            return os.path.split(self.name)[1]
        return ''


    def delete(self, **kwargs):
        if self.field.manager is not None:
            self.field.manager.delete()
        super(FieldFile, self).delete(**kwargs)
    delete.alters_data = True




class FileField(Field, models.FileField):
    """Regular FileField that cleansup after itself."""
    attr_class = FieldFile
    manager_class = FileFieldManager
    keep_orphans = getattr(settings, 'SMARTFIELDS_KEEP_ORPHANS', False)
    crop_filename = getattr(settings, 'SMARTFIELDS_CROP_FILENAMES', False)
    html_tag_getter = None
    _generate_filename = None

    def __init__(self, keep_orphans=None, crop_filename=None, html_tag_getter=None, 
                 upload_to='', **kwargs):
        if keep_orphans is not None:
            self.keep_orphans = keep_orphans
        if crop_filename is not None:
            self.crop_filename = crop_filename
        self.html_tag_getter = html_tag_getter or self.html_tag_getter
        super(FileField, self).__init__(**kwargs)
        self.upload_to = upload_to
        if callable(upload_to):
            self._generate_filename = upload_to


    def save_form_data(self, instance, data):
        if not self.keep_orphans and data is not None:
            file = getattr(instance, self.name)
            if file != data:
                try:
                    file.delete(save=False)
                except: # can raise OSError or any other exception, depends on backend
                    if not file.field.FAIL_SILENTLY:
                        raise
        super(FileField, self).save_form_data(instance, data)


    def pre_save(self, model_instance, add):
        "Saves the file, updates dependants just before saving the model."
        # Skipping parent's pre_save call on purpose
        file = super(models.FileField, self).pre_save(model_instance, add)
        if file and not file._committed:
            # Commit the file to storage prior to saving the model
            file.save(file.name, file, save=False)
            if self.manager is not None:
                self.manager.update(model_instance)
        return file


    def delete(self, model_instance):
        if not self.keep_orphans:
            field_file = getattr(model_instance, self.name)
            if field_file:
                field_file.delete()


    def generate_filename(self, *args):
        if self._generate_filename is not None:
            filename = self._generate_filename(*args)
        else:
            filename = super(FileField, self).generate_filename(*args)
        if self.crop_filename and len(filename) > self.max_length:
            path, fullname = os.path.split(filename)
            name, ext = os.path.splitext(fullname)
            new_name_len = self.max_length - (len(path) + len(ext) + 1)
            if new_name_len > 0:
                name = name[:new_name_len]
                filename = os.path.join(path, name + ext)
        return filename
                


class ImageFieldFile(FieldFile, files.ImageFieldFile):
    pass




class ImageField(FileField, models.ImageField):
    attr_class = ImageFieldFile
    manager_class = AsyncImageFieldManager

    def html_tag_getter(self, empty=False, **kwargs):
        if not empty:
            return '<img src="{file.url}"/>'.format(**Kwargs)
        return ''




class VideoField(FileField):
    manager_class = VideoFieldManager

    def html_tag_getter(self, empty=False, **kwargs):
        if not empty:
            return """<video id="video_{file.field.name}"
            controls="controls" preload="auto" src="{file.url}"/>""".format(**kwargs)
        return ''
