from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from django.db.models.fields.files import ImageFieldFile, ImageField

from smart_fields.utils import resize_image
import os

class SmartFieldsHandler(object):
    _smart_fields = {}

    def _smart_field(self, field_name):
        return self.smart_fields_settings[field_name]['instance']

    def _smart_field_new_name(self, filename, key, ext=None):
        name, old_ext = os.path.splitext(filename)
        if ext is None:
            ext = old_ext
        return "%s_%s.%s" % (name, key, ext.lower())

    def _smart_field_init(self, field_name, field_settings):
        field_profile = field_settings.get('profile', {})
        if field_profile:
            field_file = self._smart_field(field_name)
            smart_fields = {}
            if field_file:
                storage = field_file.field.storage
            else:
                storage = FileSystemStorage(
                    location=settings.STATIC_ROOT, base_url=settings.STATIC_URL)
            for key in field_profile:
                new_field_name = "%s_%s" % (field_name, key)
                if field_file:
                    new_name = self._smart_field_new_name(
                        field_file.name, key,
                        ext=field_profile[key].get('format', None))
                else:
                    new_name = field_profile[key].get('default', None)
                if not new_name:
                    new_field = ImageField(
                        upload_to=lambda x, y: y, 
                        storage=storage, name=new_field_name)
                    new_field_file = ImageFieldFile(self, new_field, new_name)
                    self.__dict__[new_field_name] = new_field_file
                    smart_fields[key] = new_field_file
            self._smart_fields[field_name] = smart_fields
            
    @property
    def smart_fields(self):
        if not self._smart_fields:
            self.smart_fields_init()
        return self._smart_fields

    def smart_fields_init(self):
        for field_name, field_settings in self.smart_fields_settings.iteritems():
            self._smart_field_init(field_name, field_settings)

    @property
    def smart_fields_settings(self):
        raise NotImplementedError()

    def _smart_fields_image_save(self, image, image_profile):
        image.open()
        for key in image_profile:
            x, y = image_profile[key].get(
                'dimensions', image._get_image_dimensions())
            format = image_profile[key].get('format', 'PNG')
            new_image = self.smart_fields[image.field.name][key]
            new_name = self._smart_field_new_name(
                image.name, key, ext=image_profile[key].get('format', None))
            new_image.save(
                new_name, resize_image(image, x, y, format=format), save=False)
            new_image.close()
            image.seek(0)
        image.close()
    
    def smart_fields_save(self, old):
        for field_name, field_settings in self.smart_fields_settings.iteritems():
            field_profile = field_settings.get('profile', {})
            field_file = self._smart_field(field_name)
            is_new = False
            if field_file:
                if not (old and old._smart_field(field_name)):
                    self._smart_field_init(field_name, field_settings)
                    is_new = True
                elif old._smart_field(field_name) != field_file:
                    is_new = True
            if old and old._smart_field(field_name):
                if not is_new:
                    self._smart_field_init(field_name, field_settings)
                else:
                    self.smart_fields_cleanup(old, field_name)
            if is_new and field_profile:
                type = field_settings.get('type', 'file')
                if type == 'image':
                    self._smart_fields_image_save(field_file, field_profile)

    def smart_fields_cleanup(self, instance, field_name):
        field_settings = instance.smart_fields_settings.get(field_name, {})
        keepfiles = field_settings.get('keepfiles', False)
        field_profile = field_settings.get('profile', {})
        field_file = instance._smart_field(field_name)
        if field_file and not keepfiles:
            # best attempt to clean up orphan files
            for key in field_profile:
                try: instance.smart_fields[field_name][key].delete(save=False)
                except OSError: pass
            try: field_file.delete(save=False)
            except OSError: pass

