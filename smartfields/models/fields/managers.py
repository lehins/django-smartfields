import threading
from django.core.cache import cache
from django.utils.functional import curry

from smartfields.processors import ProcessingError, BaseProcessor, ImageConverter, VideoConverter

__all__ = [
    "FieldManager", "FileFieldManager", "ImageFieldManager", "VideoFieldManager",
    "ProgressFieldManager"
]


class FieldManager(object):
    processor_class = BaseProcessor

    def __init__(self, field, dependencies, processor_class=None):
        """:class:`FieldManager` is similar to a ModelManager in a sense that it is
        capable of changing the value of a field depending on values form other
        fields related to a model instance as well as modyfing a model instance
        in any way fit.

        :param Field field: field instance that needs some extra managing.

        :params list dependencies: list of :class:`Dependency` instances that
        will be managed by this :class:`FieldManager`.

        :keyword BaseProcessor processor_class: class that will be instantiated
        and used later for field value processing.

        """
        self.field = field
        if processor_class is not None:
            self.processor_class = processor_class
        self.dependencies = list(dependencies)


    def handle(self, instance):
        """Handling is the functionality that will be invoked prior to saving a
        model instance as well as upon any model instantiation. Hence it should
        not be expensive, or should be performed conditionally. For instance
        :class:`FileFieldManager` attaches extra dependant :class:`FieldFile`s
        to the model, but doesn't do any heavy computation. It is also possible
        to skip handling of a dependency by setting ``persistet`` flag to
        `False` on per :class:`Dependency` basis.

        """
        value = getattr(instance, self.field.name)
        for d in self.dependencies:
            d.handle(instance, self.field, value)


    def update(self, instance):
        """Updating will not be invoked automatically and needs to be called
        manually, or like in case of most Fields upon saving a Form, refer to
        individual :class:`Field` for an example.

        """
        value = getattr(instance, self.field.name)
        processor = self.processor_class(value)
        status = {
            'task': self.processor_class.task,
            'task_name': self.processor_class.task_name,
            'state': 'processing'
        }
        self.set_status(instance, status)
        try:
            for d in self.dependencies:
                d.update(instance, self.field, value, processor=processor)
            status['state'] = 'complete'
            self.set_status(instance, status)
        except BaseException, e:
            self.set_error_status(instance, "%s: %s" % (type(e).__name__, str(e)))
            if not isinstance(e, ProcessingError):
                raise
        self.handle(instance)


    def get_status_key(self, instance):
        """Generates a key used to set a status a field"""
        return "%s.%s_%s_%s" % (instance._meta.app_label,
                                instance._meta.model_name,
                                instance.pk,
                                self.field.name)


    def get_status(self, instance):
        """Retrives a status of a field from cache. Fields in state 'error' and
        'complete' will not retain the status after the call.

        """
        status_key = self.get_status_key(instance)
        status = cache.get(status_key, None)
        if status is not None and status['state'] in ['complete', 'error']:
            cache.delete(status_key)
        return status


    def set_status(self, instance, status):
        """Sets the field status for up to 5 minutes."""
        status_key = self.get_status_key(instance)
        # for debugging
        status['key'] = status_key
        cache.set(status_key, status, timeout=300)


    def set_error_status(self, instance, error):
        self.set_status(instance, {
            'state': 'error',
            'messages': [error]
        })




class FileFieldManager(FieldManager):

    def delete(self):
        for d in self.dependencies:
            d.delete()

    def get_status(self, instance):
        status = super(FileFieldManager, self).get_status(instance)
        if status is not None and status['state'] == 'error':
            # cleanup in case of an error
            getattr(instance, self.field.name).delete()
        return status




class ImageFieldManager(FileFieldManager):
    processor_class = ImageConverter




class ManagerProgressHandler(threading.Thread):

    def __init__(self, manager, instance):
        self.manager, self.instance = manager, instance
        super(ManagerProgressHandler, self).__init__()


    def run(self):
        for d in self.manager.dependencies:
            try: # remove any cached progress setters
                del d.extra_kwargs['progress_setter']
            except KeyError: pass
        responsive = self.manager.get_responsive()
        multiplier = 1.0/len(responsive)
        for idx, d in enumerate(responsive):
            d.extra_kwargs['progress_setter'] = curry(
                self.manager.progress_setter, self.instance, multiplier, idx,
                subprocessor_class=d.processor_class)
        # calling managers update method
        super(ProgressFieldManager, self.manager).update(self.instance)




class ProgressFieldManager(FileFieldManager):

    def __init__(self, *args, **kwargs):
        self.async = kwargs.pop('async', True)
        super(ProgressFieldManager, self).__init__(*args, **kwargs)


    def get_responsive(self):
        if self.processor_class.responsive:
            non_responsive = {d for d in self.dependencies
                              if d.processor_class is not None and
                              not d.processor_class.responsive}
            return [d for d in self.dependencies if not d in non_responsive]
        return [d for d in self.dependencies
                if d.processor_class is not None and
                d.processor_class.responsive]


    def progress_setter(self, instance, multiplier, index, progress,
                        subprocessor_class=None):
        processor_class = subprocessor_class or self.processor_class
        print "progress: %s, multiplier: %s" % (progress, multiplier)
        try:
            progress = multiplier * (index + progress)
        except TypeError, e:
            raise ProcessingError("Problem setting progress: %s" % e)
        self.set_status(instance, {
            'task': processor_class.task,
            'task_name': processor_class.task_name,
            'state': 'in_progress',
            'progress': progress
        })


    def update(self, instance):
        if self.async:
            progress_handler = ManagerProgressHandler(self, instance)
            progress_handler.start()
        else:
            super(ProgressFieldManager, self).update(instance)




class VideoFieldManager(ProgressFieldManager):
    processor_class = VideoConverter
