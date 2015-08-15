import os
from django import forms
from django.contrib.staticfiles.storage import staticfiles_storage
from django.db.models import fields
from django.db.models.fields import files
from django.utils.six import text_type
try:
    from django.core import checks
except ImportError: pass

from smartfields.settings import KEEP_ORPHANS
from smartfields.managers import FieldManager
from smartfields.models import SmartfieldsModelMixin
from smartfields.utils import VALUE_NOT_SET

__all__ = [
    'BigIntegerField', 'BinaryField', 'BooleanField', 'CharField', 
    'CommaSeparatedIntegerField', 'DateField', 'DateTimeField', 'DecimalField', 
    'DurationField', 'EmailField', 'Field', 'FilePathField', 'FloatField', 
    'GenericIPAddressField', 'IPAddressField', 'IntegerField', 
    'NullBooleanField', 'PositiveIntegerField', 'PositiveSmallIntegerField',
    'SlugField', 'SmallIntegerField', 'TextField', 'TimeField', 'URLField',
    'UUIDField', 'FileField', 'ImageField',
]

class SmartfieldsDescriptor(object):
    field = None

    def __init__(self, field):
        self.field = field

    def __set__(self, instance, value):
        if self.field.manager is not None:
            value = self.field.manager.pre_process(instance, value)
            if self.field.manager.should_process:
                previous_value = instance.__dict__.get(self.field.name)
                if previous_value is not VALUE_NOT_SET:
                    self.field.manager.stash_previous_value(previous_value)
        instance.__dict__[self.field.name] = self.field.to_python(value)

    def __get__(self, instance=None, model=None):
        if instance is None:
            raise AttributeError(
                "The '%s' attribute can only be accessed from %s instances."
                % (self.field.name, model.__name__))
        return instance.__dict__[self.field.name]


class Field(fields.Field):
    descriptor_class = SmartfieldsDescriptor
    manager_class = FieldManager
    manager = None
    
    def __init__(self, verbose_name=None, name=None, dependencies=None, **kwargs):
        if dependencies is not None:
            self.manager = self.manager_class(self, dependencies)
        self._dependencies = dependencies
        super(Field, self).__init__(verbose_name=verbose_name, name=name, **kwargs)

    def contribute_to_class(self, cls, name, **kwargs):
        super(Field, self).contribute_to_class(cls, name, **kwargs)
        if not issubclass(cls, SmartfieldsModelMixin):
            cls.__bases__ = (SmartfieldsModelMixin,) + cls.__bases__
        if not hasattr(cls, '_smartfields_managers'):
            cls._smartfields_managers = {}
        if self.manager is not None:
            if not isinstance(self, FileField):
                # FileField will itself set the descriptor
                setattr(cls, name, self.descriptor_class(self))
            self.manager.contribute_to_model(cls, name)
            
    def get_status(self, instance):
        if self.manager is not None:
            return self.manager.get_status(instance)

    def pre_save(self, model_instance, add):
        value = super(Field, self).pre_save(model_instance, add)
        if self.manager is not None:
            self.manager.process(model_instance)
            value = getattr(model_instance, self.attname)
        return value


class BooleanField(Field, fields.BooleanField):
    pass


class NullBooleanField(Field, fields.NullBooleanField):
    pass


class SmallIntegerField(Field, fields.SmallIntegerField):
    pass


class IntegerField(Field, fields.IntegerField):
    pass


class BigIntegerField(Field, fields.BigIntegerField):
    pass


class PositiveIntegerField(Field, fields.PositiveIntegerField):
    pass


class PositiveSmallIntegerField(Field, fields.PositiveSmallIntegerField):
    pass


class FloatField(Field, fields.FloatField):
    pass


class DecimalField(Field, fields.DecimalField):
    pass


if hasattr(fields, 'BinaryField'):
    # Django>=1.6
    class BinaryField(Field, getattr(fields, 'BinaryField')):
        pass
else:
    BinaryField = None


class CharField(Field, fields.CharField):
    pass


class TextField(Field, fields.TextField):
    pass


class CommaSeparatedIntegerField(Field, fields.CommaSeparatedIntegerField):
    pass


class DateField(Field, fields.DateField):
    pass


class DateTimeField(Field, fields.DateTimeField):
    pass


class TimeField(Field, fields.TimeField):
    pass


class IPAddressField(Field, fields.IPAddressField):
    pass


class GenericIPAddressField(Field, fields.GenericIPAddressField):
    pass


class EmailField(Field, fields.EmailField):
    pass


class URLField(Field, fields.URLField):
    pass


class SlugField(Field, fields.SlugField):
    pass


##################
# FILES
##################


class FilePathField(Field, fields.FilePathField):
    pass


class FieldFile(files.FieldFile):
    
    def __init__(self, *args, **kwargs):
        self.is_static = kwargs.pop('is_static', False)
        super(FieldFile, self).__init__(*args, **kwargs)
        if self.is_static:
            self.storage = staticfiles_storage

    def save(self, name, content, save=True, instance_update=True):
        # prevent static files from being modified
        if self.is_static:
            return
        name = self.field.generate_filename(self.instance, name)
        self.name = self.storage.save(name, content)
        if instance_update:
            # omit descriptor to prevent stashing the same file
            self.instance.__dict__[self.field.name] = self.name
        self._size = content.size
        self._committed = True
        if save and instance_update:
            self.instance.save()
    save.alters_data = True

    def delete(self, save=True, instance_update=True):
        # prevent static files from being deleted
        if self.is_static or not self:
            return
        if hasattr(self, '_file'):
            self.close()
            del self.file
        self.storage.delete(self.name)
        self.name = None
        if instance_update:
            # omit descriptor to prevent stashing the same file
            self.instance.__dict__[self.field.name] = self.name
        if hasattr(self, '_size'):
            del self._size
        self._committed = False
        if instance_update and getattr(self.field, 'manager', None) is not None:
            self.field.manager.cleanup(self.instance)
        if save and instance_update:
            self.instance.save()
    delete.alters_data = True

    @property
    def state(self):
        if getattr(self.field, 'manager', None) is not None:
            return self.field.manager._get_status(self.instance)[1]['state']

    @property
    def name_base(self):
        if self:
            return os.path.split(self.name)[1]
        return ""

    @property
    def html_tag(self):
        if self:
            return text_type(getattr(self.instance, "%s_html_tag" % self.field.name, ""))
        return ""


class FileDescriptor(files.FileDescriptor):

    def __set__(self, instance, value):
        if self.field.manager is not None:
            value = self.field.manager.pre_process(instance, value)
            previous_value = self.__get__(instance)
            if previous_value is not VALUE_NOT_SET and previous_value._committed and \
               previous_value != value:
                # make sure form saving doesn't replace current file with itself
                self.field.manager.stash_previous_value(previous_value)
        super(FileDescriptor, self).__set__(instance, value)


class FileField(Field, files.FileField):

    attr_class = FieldFile
    descriptor_class = FileDescriptor

    def __init__(self, verbose_name=None, name=None, keep_orphans=KEEP_ORPHANS, 
                 dependencies=None, **kwargs):
        self.keep_orphans = keep_orphans
        if not keep_orphans and dependencies is None:
            # make sure there is a manger so orphans will get cleaned up
            self.manager = self.manager_class(self, [])
        super(FileField, self).__init__(verbose_name, name, 
                                        dependencies=dependencies, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(FileField, self).deconstruct()
        if self.keep_orphans != KEEP_ORPHANS:
            kwargs['keep_orphans'] = self.keep_orphans
        return name, path, args, kwargs


class ImageFieldFile(FieldFile, files.ImageFieldFile):
    pass


def _get_width(image, **kwargs): 
    if image:
        return image.width

def _get_height(image, **kwargs): 
    if image:
        return image.height


class ImageField(FileField):

    attr_class = ImageFieldFile

    def _get_dim_dependency(self, dim):
        from smartfields.dependencies import Dependency
        field = getattr(self, "%s_field" % dim)
        # ugly, but lambdas and bound methods are not picklable
        getter = globals()["_get_%s" % dim]
        return Dependency(attname=field, processor=getter, uid='ImageField._%s' % dim)

    def __init__(self, verbose_name=None, name=None, dependencies=None, 
                 width_field=None, height_field=None, **kwargs):
        dependencies = [d for d in dependencies or []]
        self.width_field, self.height_field = width_field, height_field
        if self.width_field:
            dependencies.append(self._get_dim_dependency('width'))
        if self.height_field:
            dependencies.append(self._get_dim_dependency('height'))
        dependencies = dependencies or None
        super(ImageField, self).__init__(verbose_name, name, 
                                         dependencies=dependencies, **kwargs)

    def check(self, **kwargs):
        errors = super(ImageField, self).check(**kwargs)
        errors.extend(self._check_image_library_installed())
        return errors

    def _check_image_library_installed(self):
        try:
            from PIL import Image  # NOQA
        except ImportError:
            return [
                checks.Error(
                    'Cannot use ImageField because Pillow is not installed.',
                    hint=('Get Pillow at https://pypi.python.org/pypi/Pillow '
                          'or run command "pip install Pillow".'),
                    obj=self,
                    id='fields.E210',
                )
            ]
        else:
            return []

    def deconstruct(self):
        name, path, args, kwargs = super(ImageField, self).deconstruct()
        dependencies = kwargs.get('dependencies', None) 
        if dependencies:
            dims = map(self._get_dim_dependency, ['width', 'height'])
            dependencies = filter(lambda d: d not in dims, dependencies)
            kwargs['dependencies'] = dependencies
        if self.width_field:
            kwargs['width_field'] = self.width_field
        if self.height_field:
            kwargs['height_field'] = self.height_field
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        defaults = {'form_class': forms.ImageField}
        defaults.update(kwargs)
        return super(ImageField, self).formfield(**defaults)


# future added fields

if hasattr(fields, 'DurationField'):
    class DurationField(Field, getattr(fields, 'DurationField')):
        pass
else:
    DurationField = None

if hasattr(fields, 'UUIDField'):
    class UUIDField(Field, getattr(fields, 'UUIDField')):
        pass
else:
    UUIDField = None

