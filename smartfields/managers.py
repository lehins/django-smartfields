import threading

from django.core.cache import cache
from django.db.models import FileField

from smartfields.processors import ProcessingError

__all__ = [
    'FieldManager'
]


class AsyncHandler(threading.Thread):

    def __init__(self, manager, instance):
        self.manager, self.instance = manager, instance
        super(ManagerProgressHandler, self).__init__()


    def get_progress_setter(self, multiplier, index):
        def progress_setter(processor, progress):
            try:
                progress = multiplier * (index + progress)
            except TypeError as e:
                raise ProcessingError("Problem setting progress: %s" % e)
            self.manager.set_status(self.instance, {
                'task': getattr(processor, 'task', 'processing'),
                'task_name': getattr(processor, 'task_name', "Processing"),
                'state': 'processing',
                'progress': progress
            })
        return progress_setter


    def run(self):
        dependencies = filter(lambda d: d.async, self.manager.dependencies)
        multiplier = 1.0/len(dependencies)
        try:
            for idx, d in enumerate(dependencies):
                self.manager._process(
                    self.instance, d, 
                    progress_setter=self.get_progress_setter(multiplier, idx)
                )
        except ProcessingError: pass



class FieldManager(object):
    
    def __init__(self, field, dependencies=None):
        self.field = field
        self.dependencies = dependencies or []
        self.async = bool([d for d in self.dependencies if d.async])

    
    def handle(self, instance, event):
        field_value = self.field.value_from_object(instance)
        for d in self.dependencies:
            d.handle(instance, self.field, field_value, event)


    def _process(self, instance, dependency, progress_setter=None):
        # process single dependency
        try:
            field_value = self.field.value_from_object(instance)
            dependency.process(
                instance, self.field, field_value, progress_setter=progress_setter)
        except BaseException as e:
            self.set_error_status(instance, "%s: %s" % (type(e).__name__, str(e)))
            if isinstance(self.field, FileField):
                field_file = self.field.value_from_object(instance)
                field_file.delete()
            raise


    def process(self, instance):
        self.set_status({'state': 'busy'})
        try:
            if self.async:
                for d in filter(lambda d: not d.async, self.dependencies):
                    self._process(instance, d)
                async_handler = AsyncHandler(manager, instance)
                async_handler.start()
            else:
                for d in self.dependencies:
                    self._process(instance, d)
                self.set_status({'state': 'ready'})
        except ProcessingError: pass



    def get_status_key(self, instance):
        """Generates a key used to set a status on a field"""
        return "%s.%s-%s-%s" % (instance._meta.app_label,
                                instance._meta.model_name,
                                instance.pk,
                                self.field.name)


    def get_status(self, instance):
        """Retrives a status of a field from cache. Fields in state 'error' and
        'complete' will not retain the status after the call.

        """
        status = {
            'app_label': instance._meta.app_label,
            'model_name': instance._meta.model_name,
            'pk': instance.pk,
            'field_name': self.field.name,
            'state': 'ready'
        }
        status_key = self.get_status_key(instance)
        current_status = cache.get(status_key, None)
        if current_status is not None:
            status.update(current_status)
            if status['state'] in ['complete', 'error']:
                cache.delete(status_key)
        return status


    def set_error_status(self, instance, error):
        self.set_status(instance, {
            'state': 'error',
            'messages': [error]
        })

