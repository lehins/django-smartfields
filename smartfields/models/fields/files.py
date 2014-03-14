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
    def status(self):
        return self.field.get_status(self.instance)

    @property
    def status_json(self):
        return json.dumps(self.status)

    @property
    def html_tag(self):
        if self.field.html_tag_template is not None and self:
           return self.field.html_tag_template.format(
               file=self, field=self.field, instance=self.instance)
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
    html_tag_template = None

    def __init__(self, keep_orphans=None, html_tag_template=None, **kwargs):
        if keep_orphans is not None:
            self.keep_orphans = keep_orphans
        if html_tag_template is not None:
            self.html_tag_template = html_tag_template
        super(FileField, self).__init__(**kwargs)


    def save_form_data(self, instance, data):
        if not self.keep_orphans and data is not None:
            file = getattr(instance, self.name)
            if file != data:
                file.delete(save=False)
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




class ImageFieldFile(FieldFile, files.ImageFieldFile):
    pass




class ImageField(FileField, models.ImageField):
    attr_class = ImageFieldFile
    manager_class = ImageFieldManager
    html_tag_template = '<img src="{file.url}"/>'




class VideoField(FileField):
    manager_class = VideoFieldManager
    html_tag_template = """<video id="video_{file.field.name}"
    controls="controls" preload="auto" src="{file.url}"/>"""
