import os, datetime, inspect
from django.core.files.base import File
from django.core.files.storage import default_storage
from django.db.models.fields import files, NOT_PROVIDED, FieldDoesNotExist
from django.utils.encoding import force_text, force_str
from django.utils import six

from smartfields.fields import FieldFile, FileField
from smartfields.settings import KEEP_ORPHANS
from smartfields.processors.base import BaseProcessor
from smartfields.utils import VALUE_NOT_SET, deconstructible, apps, AppRegistryNotReady, \
    get_empty_values

__all__ = [
    'Dependency', 'FileDependency'
]


@deconstructible
class Dependency(object):
    _stashed_value = VALUE_NOT_SET
    field = None
    model = None

    def __init__(self, attname=None, suffix=None, processor=None, pre_processor=None,
                 async=False, default=NOT_PROVIDED, processor_params=None, uid=None):
        """
        Every Dependency depends on a field, either itself or another field specified
        by a ``field_name``.
        if field_name is None and attname or suffix are also None, this
        dependency becomes a forward dependency. All ``async=True`` will run last.

        """
        assert attname is None or suffix is None, \
            "It is invalid to set both attname and suffix at the same time."
        self._attname = attname
        self._suffix = suffix
        self._processor = processor
        self._pre_processor = pre_processor
        self._default = default
        self._processor_params = processor_params or {}
        if self.has_pre_processor():
            if inspect.isclass(pre_processor) and issubclass(pre_processor, BaseProcessor):
                self._pre_processor = pre_processor()
            assert callable(self._pre_processor), "pre_processor has to be a function"
            if hasattr(self._pre_processor, 'check_params'):
                self._pre_processor.check_params(**self._processor_params)
        if self.has_processor():
            if inspect.isclass(processor) and issubclass(processor, BaseProcessor):
                self._processor = processor()
            assert callable(self._processor), "processor has to be a function"
            if hasattr(self._processor, 'check_params'):
                self._processor.check_params(**self._processor_params)
        self.async = async
        assert not async or self.has_processor(), \
            "Asynchrounous processing doesn't make sense without a processor."
        self._uid = uid

    def __eq__(self, other):
        return (type(self) is type(other) and
                self._attname == other._attname and
                self._suffix == other._suffix and
                self._processor == other._processor and
                self._default == other._default and
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
        except (FieldDoesNotExist, AppRegistryNotReady): pass

    @property
    def has_stashed_value(self):
        return self._stashed_value is not VALUE_NOT_SET

    def get_stashed_value(self, instance, value):
        if self._dependee is self.field:
            return self.field.manager.get_stashed_value()
        if self.has_stashed_value:
            return self._stashed_value
        return self.get_default(instance, value)

    def stash_previous_value(self, instance, value):
        if self._stashed_value is VALUE_NOT_SET and self._dependee is not self.field:
            self._stashed_value = value
            instance.__dict__[self.name] = None

    def restore_stash(self, instance):
        if self.has_stashed_value:
            instance.__dict__[self.name] = self._stashed_value
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
        #assert not(type(self) is Dependency and self.has_processor and self._dependee is None), \
        #    "Regular Dependency doesn't make sense with non-field type dependee and a " \
        #    "specified processor. Dependee attname: %s " % self.name

    def set_field(self, field):
        assert self.field is None, \
            "This %s is already handling a field: %s. Create a new instance." % (
                self.__class__.__name__, self.field.name)
        self.field = field

    def should_process(self):
        return self.has_processor() or self.has_default()

    def has_processor(self):
        return self._processor is not None

    def has_pre_processor(self):
        return self._pre_processor is not None

    def has_default(self):
        return self._default is not NOT_PROVIDED
        
    def get_default(self, instance, value):
        if self.has_default():
            if callable(self._default):
                return self._default(
                    value, instance=instance, field=self.field, 
                    dependee=self._dependee, **self._processor_params
                )
            return self._default
        return VALUE_NOT_SET

    def set_default(self, instance, value):
        dependee = self._dependee
        if dependee is None or \
           dependee.value_from_object(instance) in get_empty_values(dependee):
            default_value = self.get_default(instance, value)
            if default_value is not VALUE_NOT_SET:
                self.set_value(instance, default_value, is_default=True)
                return True
        return False

    def pre_init(self, instance, value, *args, **kwargs):
        pass

    def post_init(self, instance, value, *args, **kwargs):
        self.set_default(instance, value)

    def pre_save(self, instance, value, *args, **kwargs):
        pass

    def post_save(self, instance, value, *args, **kwargs):
        pass

    def pre_delete(self, instance, value, *args, **kwargs):
        pass

    def post_delete(self, instance, value, *args, **kwargs):
        self.cleanup(instance)

    def handle(self, instance, event, *args, **kwargs):
        value = self.field.value_from_object(instance)
        event_handler = getattr(self, event)
        event_handler(instance, value, *args, **kwargs)

    def set_value(self, instance, value, is_default=False):
        if not is_default and self._dependee is self.field:
            # for self dependency ommit setting through descriptor
            # to prevent infinite processing, unless it is default value
            # and it does in fact needs processing
            instance.__dict__[self.name] = value
        else:
            setattr(instance, self.name, value)

    def get_value(self, instance):
        return getattr(instance, self.name)

    def process(self, instance, value, progress_setter=None):
        field = self.field
        if value in get_empty_values(field) or not self.has_processor():
            if self.set_default(instance, value) and self.has_processor():
                value = self.get_value(instance)
                field = self._dependee
        if self.has_processor():  #(field is None or value not in get_empty_values(field)) and
            if self.async:
                self._processor.progress_setter = progress_setter
                progress_setter(self._processor, 0)
            try:
                if isinstance(self._processor, BaseProcessor):
                    new_value = self._processor(
                        value, instance=instance, field=self.field, dependee=self._dependee,
                        stashed_value=self.get_stashed_value(instance, value),
                        **self._processor_params
                    )
                else:
                    new_value = self._processor(value)
            finally:
                if self.async:
                    delattr(self._processor, 'progress_setter')
            if self.async:
                progress_setter(self._processor, 1)
            if new_value is not VALUE_NOT_SET:
                self.set_value(instance, new_value)

    def pre_process(self, instance, value):
        if self.has_pre_processor():
            if isinstance(self._pre_processor, BaseProcessor):
                new_value = self._pre_processor(
                    value, instance=instance, field=self.field, 
                    dependee=self._dependee, **self._processor_params
                )
            else:
                new_value = self._pre_processor(value)
            if self._dependee is self.field:
                return new_value
            else:
                self.set_value(instance, new_value)
        return VALUE_NOT_SET


@deconstructible
class FileDependency(Dependency):
    descriptor_class = files.FileDescriptor

    @property
    def attr_class(self):
        return getattr(self._processor, 'field_file_class', FieldFile)

    def __init__(self, upload_to="", storage=None, keep_orphans=KEEP_ORPHANS, **kwargs):
        # `default` has to be a static file
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
                if self._stashed_value._committed and \
                   not self._stashed_value.field.keep_orphans:
                    self._stashed_value.delete(instance_update=False)
            elif isinstance(self._stashed_value, files.FieldFile) and \
                 self._stashed_value._committed and not self.keep_orphans:
                stashed_value = FieldFile(self._stashed_value.instance, 
                                          self._stashed_value.field,
                                          self._stashed_value.name)
                self._stashed_value.close()
                stashed_value.delete(instance_update=False)
        super(FileDependency, self).cleanup_stash()

    def restore_stash(self, instance):
        field_file = self.get_value(instance)
        if field_file and field_file._committed:
            if isinstance(field_file, FieldFile):
                field_file.delete(instance_update=False)
            elif isinstance(field_file, files.FieldFile):
                field_file.delete(save=False)
        super(FileDependency, self).restore_stash(instance)
            
    def cleanup(self, instance):
        # do not cleanup self dependency, it will be cleaned up by the manager
        if self._dependee is not self.field:
            field_file = self.get_value(instance)
            if field_file and not getattr(field_file.field, 'keep_orphans', self.keep_orphans):
                field_file.delete(save=False)

    def contribute_to_model(self, model):
        super(FileDependency, self).contribute_to_model(model)
        if self._dependee is None:
            # mimic normal django behavior, while using dependency instance instead of 
            # creating a new field for the descriptor.
            setattr(model, self.name, self.descriptor_class(self))
        else:
            assert apps.ready or isinstance(self._dependee, files.FileField), \
                "FileDependency can not set file like attributes on non file like fields."

    def post_init(self, instance, value, *args, **kwargs):
        if self._dependee is None and self._processor and \
            value not in get_empty_values(self.field) and isinstance(value, files.FieldFile):
            # regenerate the dependent filename and reattach it.
            self.set_value(instance, self.generate_filename(instance, value.name))
        else:
            if self._dependee is None:
                self.set_value(instance, None)
            super(FileDependency, self).post_init(instance, value, *args, **kwargs)

    def get_directory_name(self):
        if self.upload_to:
            return os.path.normpath(
                force_text(datetime.datetime.now().strftime(force_str(self.upload_to))))
        return ""

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
        if callable(self.upload_to):
            directory_name, filename = os.path.split(self.upload_to(instance, filename))
            filename = self.storage.get_valid_name(filename)
            return os.path.normpath(os.path.join(directory_name, filename))
        return os.path.join(self.get_directory_name(), self.get_filename(filename))

    def set_value(self, instance, value, is_default=False):
        if not value:
            super(FileDependency, self).set_value(instance, value, is_default=is_default)
            return
        dependee = self._dependee
        field_file_class = self.attr_class
        if is_default and dependee is None and isinstance(value, six.string_types):
            # a path to default value is assumed to be a static file
            value = field_file_class(instance, self, value, is_static=True)
        elif isinstance(value, File):
            if isinstance(value, files.FieldFile) and value.field is not None \
               and value.field is not dependee:
                # if it is a file from another FileField, we'll need to copy that file
                value = value.file
            # try to figure out a name for the file 
            if isinstance(self.field, FileField) and self.field.value_from_object(instance):
                # if original value comes from a FileField will use it's file's 
                # name as a base for a new name, of course if one is present
                field_file = self.field.value_from_object(instance)
                name = field_file.name
                if not field_file._committed:
                    # make sure it is a proper name
                    name = self.field.generate_filename(instance, name)
            elif getattr(value, 'name', None) is not None:
                # if file already has some sort of name, use that
                _, name = os.path.split(value.name)
            else:
                # otherwise create a bogus name from dependency's name
                name = self.name
            if dependee is None:
                # if dependee is not a field, create a FieldFile using 
                # this dependency instead of a field
                field_file = field_file_class(instance, self, name)
            else:
                # otherwise make sure file has a proper name with a correct extension
                name = self.get_filename(name)
                field_file = dependee.attr_class(instance, dependee, name)
            cur_pos = value.tell()
            value.seek(0)
            if isinstance(dependee, FileField):
                field_file.save(name, value, instance_update=False)
            else:
                field_file.save(name, value, save=False)
            if not value.closed:
                # in django < 1.7c1 temp files are closed after moving.
                value.seek(cur_pos)
            if hasattr(value, 'temporary_file_path'):
                # make sure temporary files are deleted.
                value.close()
            value = field_file
        super(FileDependency, self).set_value(instance, value, is_default=is_default)
