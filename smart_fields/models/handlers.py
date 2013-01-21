from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from django.db.models.fields.files import FieldFile, FileField, ImageFieldFile, \
    ImageField

from smart_fields.utils import ImageConverter, VideoConverter
import os

class SmartFieldsHandler(object):
    _smart_fields = {}

    def _smart_field(self, field_name):
        return self.smart_fields_settings[field_name]['instance']

    def _smart_field_new_name(self, filename, key, ext=None):
        name, old_ext = os.path.splitext(filename)
        if ext is None:
            ext = old_ext
        else:
            ext = ".%s" % ext
        return "%s_%s%s" % (name, key, ext.lower())

    def _smart_field_init(self, field_name, field_settings):
        field_profile = field_settings.get('profile', {})
        if field_profile:
            field_file = self._smart_field(field_name)
            smart_fields = {}
            storage = None
            if field_file:
                storage = field_file.field.storage
            else:
                storage = FileSystemStorage(
                    location=settings.STATIC_ROOT, base_url=settings.STATIC_URL)
            for key, profile in field_profile.iteritems():
                new_field_name = "%s_%s" % (field_name, key)
                new_name = None
                max_dim = profile.get('dimensions', None)
                format = profile.get('format', None)
                mode = profile.get('mode', None)
                if field_file and (max_dim or format or mode):
                    new_name = self._smart_field_new_name(
                        field_file.name, key,
                        ext=format)
                else:
                    new_name = field_profile[key].get('default', None)
                if not new_name is None:
                    new_field = FileField(
                        upload_to=lambda x, y: y, 
                        storage=storage, name=new_field_name)
                    new_field_file = FieldFile(self, new_field, new_name)
                    self.__dict__[new_field_name] = new_field_file
                    smart_fields[key] = new_field_file
            self._smart_fields[field_name] = smart_fields
            
    @staticmethod
    def _smart_fields_progress_setter(progress_key, progress):
        status_codes = {0: 'started', 100: 'complete'}
        status = {
                'task': 'converting',
                'task_name': u"Converting",
                'status': status_codes.get(progress, 'in_progress'),
                'progress': progress,
                }
        cache.set(progress_key, status, timeout=300)

    @classmethod
    def _smart_fields_progress_key(cls, pk, field_name):
        return "%s_%s_%s" % (cls.__name__.lower(), pk, field_name)

    def _smart_fields_image_save(self, image, image_profile):
        image.open()
        converter = ImageConverter(image)
        for key, profile in image_profile.iteritems():
            max_dim = profile.get('dimensions', None)
            format = profile.get('format', None)
            mode = profile.get('mode', None)
            if max_dim or format or mode:
                new_image = self.smart_fields[image.field.name][key]
                new_name = self._smart_field_new_name(
                    image.name, key, ext=image_profile[key].get('format', None))
                new_image.save(new_name, ContentFile(
                        converter.convert(max_dim, format=format, mode=mode)),
                               save=False)
                new_image.close()
        image.close()

    def _smart_fields_video_save(self, file_in, files_out, video_profile):
        f_in = file_in.path
        fs_out = [(files_out[key].path, video_profile[key]) 
                  for key in files_out]
        key = self._smart_fields_progress_key(self.pk, file_in.field.name)
        converter = VideoConverter(
            f_in, fs_out, progress_setter=self._smart_fields_progress_setter,
            progress_key=key)
        converter.start()

    @property
    def smart_fields_settings(self):
        raise NotImplementedError(u"'smart_fields_settings' is a required property. "
                                  "Please refer to documentation.")

    @property
    def smart_fields(self):
        if not self._smart_fields:
            self.smart_fields_init()
        return self._smart_fields

    @classmethod
    def smart_field_status(cls, pk, field_name):
        key = cls._smart_fields_progress_key(pk, field_name)
        status = cache.get(key, None)
        if status and status['status'] == "complete":
            cache.delete(key)
        return status

    def smart_fields_init(self):
        for field_name, field_settings in self.smart_fields_settings.iteritems():
            self._smart_field_init(field_name, field_settings)

    def smart_fields_save(self, old):
        for field_name, field_settings in self.smart_fields_settings.iteritems():
            field_profile = field_settings.get('profile', {})
            field_file = self._smart_field(field_name)
            if issubclass(type(field_file), FieldFile):
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
                    elif not field_file.field.keep_orphans:
                        self.smart_fields_cleanup(old, field_name)
                if is_new and field_profile:
                    media_type = getattr(field_file.field, 'media_type', 'file')
                    self._smart_field_init(field_name, field_settings)
                    if media_type == 'image':
                        self._smart_fields_image_save(field_file, field_profile)
                    elif media_type == 'video':
                        self._smart_fields_video_save(
                            field_file, self.smart_fields[field_name], field_profile)

    def smart_fields_delete(self):
        for field_name in self.smart_fields_settings:
            self.smart_fields_cleanup(self, field_name)

    def smart_fields_cleanup(self, instance, field_name):
        field_file = instance._smart_field(field_name)
        if field_file and issubclass(type(field_file), FieldFile) and \
                not field_file.field.keep_orphans:
            # best attempt to clean up orphans
            for key, f in instance.smart_fields.get(field_name, {}).iteritems():
                try: 
                    if f: f.delete(save=False)
                except OSError: pass
            try: field_file.delete(save=False)
            except OSError: pass

