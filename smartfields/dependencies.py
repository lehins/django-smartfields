import os
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.files.base import File
from django.core.files.storage import default_storage
from django.db.models.fields import files, NOT_PROVIDED, FieldDoesNotExist
from django.db.utils import ProgrammingError
from django.utils.deconstruct import deconstructible
from django.utils import six

from smartfields.fields import FieldFile
from smartfields.settings import KEEP_ORPHANS
from smartfields.utils import VALUE_NOT_SET

__all__ = [
    'Dependency', 'FileDependency'
]

@deconstructible
class Dependency(object):
    _stashed_value = VALUE_NOT_SET
    field = None
    model = None

    def __init__(self, field_name=None, attname=None, suffix=None, processor=None,
                 async=False, default=NOT_PROVIDED, pre_init=None, post_init=None,
                 pre_save=None, post_save=None, pre_delete=None, post_delete=None,
                 processor_params=None, uid=None):
        """
        Every Dependency depends on a field, either itself or another field specified
        by a `field_name`.
        if field_name is None and attname or suffix are also None, this
        dependency becomes a forward dependency. All async=True will run last.

        """
        self._field_name = field_name
        assert attname is None or suffix is None, \
            "It is invalid to set both attname and suffix at the same time."
        self._attname = attname
        self._suffix = suffix
        self._processor = processor
        self.async = async
        assert not async or processor, \
            "Asynchrounous processing doesn't make sense without a processor."
        self._default = default
        self._pre_init, self._post_init = pre_init, post_init
        self._pre_save, self._post_save = pre_save, post_save
        self._pre_delete, self._post_delete = pre_delete, post_delete
        self._processor_params = processor_params or {}
        if self._processor is not None and hasattr(self._processor, 'check_params'):
            self._processor.check_params(**self._processor_params)
        self._uid = uid

    def __eq__(self, other):
        return (type(self) is type(other) and
                self._field_name == other._field_name and
                self._attname == other._attname and
                self._suffix == other._suffix and
                self._processor == other._processor and
                self._default == other._default and
                self._pre_init == other._pre_init and 
                self._post_init == other._post_init and
                self._pre_save == other._pre_save and
                self._post_save == other._post_save and 
                self._pre_delete == other._pre_delete and
                self._post_delete == other._post_delete and
                self._processor_params == other._processor_params and
                self._uid == other._uid)

    @property
    def name(self):
        if self._attname:
            return self._attname
        if self._suffix:
            return "%s_%s" % (self.field.name, self._suffix)
        return self.field.name

    @property
    def _dependee(self):
        try:
            return self.model._meta.get_field(self.name)
        except FieldDoesNotExist: pass

    @property
    def _dependor(self):
        if self._field_name is not None:
            return self.model._meta.get_field(self._field_name)
        return self.field

    @property
    def has_stashed_value(self):
        return self._stashed_value is not VALUE_NOT_SET

    def stash_previous_value(self, instance, value):
        if self._stashed_value is VALUE_NOT_SET and self._dependee is not self.field:
            self._stashed_value = value
            self.set_value(instance, None)
            #instance.__dict__[self.name] = None

    def restore_stash(self, instance):
        if self.has_stashed_value:
            self.set_value(instance, self._stashed_value)
            self._stashed_value =  VALUE_NOT_SET

    def cleanup(self, instance):
        pass

    def cleanup_stash(self):
        self._stashed_value = VALUE_NOT_SET

    def contribute_to_model(self, model):
        self.model = model
        assert not self.async or self._dependee is None, \
            "Cannot do asynchronous processing and setting value on a field, dependee has" \
            "has to be a regular attribute."

    def set_field(self, field):
        if self.field is not None:
            # TODO: maybe use this as a factory to create a new instance?
            raise ProgrammingError(
                "This %s is already handling field: %s. Create a new instance" % (
                    self.__class__.__name__, self.field.name))
        self.field = field

    def has_default(self):
        return self._default is not NOT_PROVIDED
        
    def get_default(self, value, instance):
        if self.has_default():
            if callable(self._default):
                return self._default(value, instance=instance, field=self.field)
            return self._default

    def post_init(self, value, instance, field_value, *args, **kwargs):
        if self.has_default() and (
                self._dependee is None or 
                self._dependee.value_from_object(instance) in self._dependee.empty_values):
            default_value = self.get_default(value, instance)
            self.set_value(instance, default_value, is_default=True)

    def handle(self, instance, field_value, event, *args, **kwargs):
        try:
            value = self._dependor.value_from_object(instance)
        except (KeyError, AttributeError) as e:
            # necessary for pre_init
            value = None
        custom_event_handler = getattr(self, "_%s" % event, None)
        if callable(custom_event_handler):
            custom_event_handler(value, instance, self.field, field_value, *args, **kwargs)
        elif isinstance(custom_event_handler, six.string_types):
            custom_event_handler = getattr(instance, custom_event_handler, None)
            if callable(custom_event_handler):
                custom_event_handler(value, self.field, field_value, *args, **kwargs)
        event_handler = getattr(self, event, None)
        if callable(event_handler):
            event_handler(value, instance, field_value, *args, **kwargs)


    def set_value(self, instance, value, is_default=False):
        if self.name == self.field.name:
            # for self dependency ommit setting through descriptor
            # to prevent infinite recursive processing
            instance.__dict__[self.name] = value
        else:
            setattr(instance, self.name, value)

    def get_value(self, instance):
        return getattr(instance, self.name)

    def process(self, instance, field_value, progress_setter=None):
        if callable(self._processor):
            value = self._dependor.value_from_object(instance)
            if isinstance(value, files.FieldFile) and not value._committed:
                value.save(value.name, value, save=False)
            if self.async:
                self._processor.progress_setter = progress_setter
                progress_setter(self._processor, 0)
            try:
                value = self._processor(
                    value, instance=instance, field=self.field, field_value=field_value, 
                    **self._processor_params
                )
            finally:
                if self.async:
                    delattr(self._processor, 'progress_setter')
            if self.async:
                progress_setter(self._processor, 1)
            self.set_value(instance, value)


class FileDependency(Dependency):
    """
    `default` has to be a static file
    
    """
    @property
    def attr_class(self):
        cls = getattr(self._processor, 'field_file_class', None)
        if cls is None:
            from smartfields.fields import FieldFile
            cls = FieldFile
        return cls

    @property
    def descriptor_class(self):
        return getattr(self._processor, 'descriptor_class', files.FileDescriptor)
    
    def __init__(self, upload_to='', storage=None, keep_orphans=KEEP_ORPHANS, **kwargs):
        self.storage = storage or default_storage
        self.upload_to = upload_to
        self.keep_orphans = keep_orphans
        super(FileDependency, self).__init__(**kwargs)

    def __eq__(self, other):
        return (super(FileDependency, self).__eq__(other) and 
                self.storage is other.storage and
                self.upload_to == other.upload_to and
                self.keep_orphans == other.keep_orphans)
        
    def cleanup_stash(self):
        if self.has_stashed_value and self._stashed_value:
            if isinstance(self._stashed_value, FieldFile):
                if not self._stashed_value.field.keep_orphans:
                    self._stashed_value.delete(instance_update=False)
            elif isinstance(self._stashed_value, files.FieldFile) and not self.keep_orphans:
                stashed_value = FieldFile(self._stashed_value.instance, 
                                          self._stashed_value.field,
                                          self._stashed_value.name)
                self._stashed_value.close()
                stashed_value.delete(instance_update=False)
        super(FileDependency, self).cleanup_stash()

    def restore_stash(self, instance):
        file = self.get_value(instance)
        if file and file._committed:
            file.delete(instance_update=False)
        super(FileDependency, self).restore_stash(instance)
            
    def cleanup(self, instance):
        # do not cleanup self dependency, it will be cleaned up by the manager
        if self._dependee is not self.field:
            file = self.get_value(instance)
            if file and not getattr(file.field, 'keep_orphans', KEEP_ORPHANS):
                file.delete(save=False)

    def contribute_to_model(self, model):
        super(FileDependency, self).contribute_to_model(model)
        if self._dependee is None:
            # mimic normal django behavior, while using dependency instance instead of 
            # creating a new field for the descriptor.
            setattr(model, self.name, self.descriptor_class(self))
        else:
            assert isinstance(self._dependee, files.FileField), \
                "FileDependency can not set file like attributes on non file like fields."

    def post_init(self, value, instance, field_value, *args, **kwargs):
        if self._dependee is None and self._processor and value \
            and isinstance(value, files.FieldFile):
            # regenerate the dependent filename and reattach it.
            self.set_value(instance, self.generate_filename(instance, value.name))
        else:
            if self._dependee is None:
                self.set_value(instance, None)
            super(FileDependency, self).post_init(value, instance, field_value)

    def post_delete(self, value, instance, field_value, *args, **kwargs):
        self.cleanup(instance)

    def process(self, instance, *args, **kwargs):
        # skip processing if there is no file
        file = self._dependor.value_from_object(instance)
        if file:
            if not file._committed:
                # commit the file, in case processing was invoked from model instance
                file.save(file.name, file, save=False)
            super(FileDependency, self).process(instance, *args, **kwargs)

    def get_directory_name(self, upload_to):
        return os.path.normpath(
            force_text(datetime.datetime.now().strftime(force_str(upload_to))))

    def get_filename(self, filename):
        name, ext = os.path.splitext(filename)
        if self._processor and hasattr(self._processor, 'get_ext'):
            new_ext = self._processor.get_ext(**self._processor_params)
            if new_ext is not None:
                ext = new_ext
        if self._dependee is None:
            filename_suffix = self._suffix or self._attname
            if filename_suffix:
                name = "%s_%s" % (name, filename_suffix)
        return "%s%s" % (name, ext)

    def generate_filename(self, instance, filename):
        upload_to, filename = os.path.split(filename)
        if self.upload_to:
            upload_to = self.get_directory_name(self.upload_to)
        return os.path.join(upload_to, self.get_filename(filename))

    def set_value(self, instance, value, is_default=False):
        if is_default:
            value = self.attr_class(instance, self, value, is_static=True)
        elif isinstance(value, File) and not isinstance(value, files.FieldFile):
            if isinstance(self._dependor, files.FileField):
                field_file = self._dependor.value_from_object(instance)
                name = field_file.name
                if not field_file._committed:
                    name = self._dependor.generate_filename(instance, name)
            else:
                name = self.get_filename(self._dependor.name)
            if self._dependee is None:
                field_file = self.attr_class(instance, self, name)
            else:
                name = self.get_filename(name)
                field_file = self._dependee.attr_class(instance, self._dependee, name)
            field_file.save(name, value, save=False)
            value = field_file
        super(FileDependency, self).set_value(instance, value, is_default=is_default)

