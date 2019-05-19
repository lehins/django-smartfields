import threading

from django.core.cache import cache

from smartfields.utils import ProcessingError, VALUE_NOT_SET, get_model_name

__all__ = [
    'FieldManager',
]

class AsyncHandler(threading.Thread):

    def __init__(self, manager, instance):
        self.manager, self.instance = manager, instance
        super(AsyncHandler, self).__init__()

    def get_progress_setter(self, multiplier, index):
        def progress_setter(processor, progress):
            try:
                progress = multiplier * (index + progress)
            except TypeError as e:
                raise ProcessingError("Problem setting progress: %s" % e)
            self.manager.set_status(self.instance, {
                'task': getattr(processor, 'task', 'processing'),
                'task_name': getattr(processor, 'task_name', "Processing"),
                'state': 'in_progress',
                'progress': progress
            })
        return progress_setter

    def run(self):
        dependencies = list(filter(lambda d: d.async_, self.manager.dependencies))
        multiplier = 1.0/len(dependencies)
        try:
            for idx, d in enumerate(dependencies):
                self.manager._process(
                    d, self.instance,
                    progress_setter=self.get_progress_setter(multiplier, idx)
                )
            self.manager.finished_processing(self.instance)
        except BaseException as e:
            self.manager.failed_processing(self.instance, error=e)
            if not isinstance(e, ProcessingError):
                raise


class FieldManager(object):
    _stashed_value = VALUE_NOT_SET

    def __init__(self, field, dependencies):
        self.field = field
        self.dependencies = dependencies
        self.has_async = False
        self.should_process = False
        for d in self.dependencies:
            d.set_field(self.field)
            if not self.has_async:
                self.has_async = d.async_
            if not self.should_process:
                self.should_process = d.should_process()

    @property
    def has_stashed_value(self):
        return self._stashed_value is not VALUE_NOT_SET

    def get_stashed_value(self):
        if self.has_stashed_value:
            return self._stashed_value
        return self.field.get_default()

    def stash_previous_value(self, value):
        if not self.has_stashed_value:
            self._stashed_value = value

    def handle(self, instance, event, *args, **kwargs):
        if event == 'pre_init':
            instance.__dict__[self.field.name] = VALUE_NOT_SET
            field_value = None
        else:
            field_value = self.field.value_from_object(instance)
            if event == 'post_init':
                # mark manager for processing by stashing default value
                if instance.pk is None and self.field.name in kwargs:
                    self.stash_previous_value(self.field.get_default())
            elif event == 'post_delete' and field_value:
                self.delete_value(field_value)
        for d in self.dependencies:
            d.handle(instance, event, *args, **kwargs)

    def failed_processing(self, instance, error=None, is_async=False):
        self.restore_stash(instance)
        if is_async:
            instance.save()
        if error is not None:
            self.set_error_status(instance, "%s: %s" % (type(error).__name__, str(error)))

    def finished_processing(self, instance):
        if self.has_stashed_value:
            self.cleanup_stash()
        self.set_status(instance, {'state': 'complete'})

    def cleanup(self, instance):
        for d in self.dependencies:
            d.cleanup(instance)

    def delete_value(self, value):
        if hasattr(value, 'delete') and hasattr(value, 'field') \
           and value and not value.field.keep_orphans:
            value.delete(instance_update=False)

    def cleanup_stash(self):
        self.delete_value(self._stashed_value)
        self._stashed_value = VALUE_NOT_SET
        for d in self.dependencies:
            if d.has_stashed_value:
                d.cleanup_stash()

    def restore_stash(self, instance):
        if self.has_stashed_value:
            self.delete_value(self.field.value_from_object(instance))
            instance.__dict__[self.field.name] = self._stashed_value
            self._stashed_value = VALUE_NOT_SET
        for d in self.dependencies:
            if d.has_stashed_value:
                d.restore_stash(instance)

    def _process(self, dependency, instance, progress_setter=None):
        # process single dependency
        value = self.field.value_from_object(instance)
        dependency.process(instance, value, progress_setter=progress_setter)

    def process(self, instance, force=False):
        """Processing is triggered by field's pre_save method. It will be
        executed if field's value has been changed (known through descriptor and
        stashing logic) or if model instance has never been saved before,
        i.e. no pk set, because there is a chance that field was initialized
        through model's `__init__`, hence default value was stashed with
        pre_init handler.

        """
        if self.should_process and (force or self.has_stashed_value):
            self.set_status(instance, {'state': 'busy'})
            for d in filter(lambda d: d.has_processor(), self.dependencies):
                d.stash_previous_value(instance, d.get_value(instance))
            try:
                if self.has_async:
                    for d in filter(lambda d: not d.async_ and d.should_process(),
                                    self.dependencies):
                        self._process(d, instance)
                    async_handler = AsyncHandler(self, instance)
                    async_handler.start()
                else:
                    for d in filter(lambda d: d.should_process(), self.dependencies):
                        self._process(d, instance)
                    self.finished_processing(instance)
            except BaseException as e:
                self.failed_processing(instance, e)
                if not isinstance(e, ProcessingError):
                    raise
        elif self.has_stashed_value:
            self.cleanup_stash()

    def pre_process(self, instance, value):
        for d in filter(lambda d: d.has_pre_processor(), self.dependencies):
            new_value = d.pre_process(instance, value)
            if new_value is not VALUE_NOT_SET:
                value = new_value
        return value


    def get_status_key(self, instance):
        """Generates a key used to set a status on a field"""
        key_id = "inst_%s" % id(instance) if instance.pk is None else instance.pk
        return "%s.%s-%s-%s" % (instance._meta.app_label,
                                get_model_name(instance),
                                key_id,
                                self.field.name)

    def _get_status(self, instance, status_key=None):
        status_key = status_key or self.get_status_key(instance)
        status = {
            'app_label': instance._meta.app_label,
            'model_name': get_model_name(instance),
            'pk': instance.pk,
            'field_name': self.field.name,
            'state': 'ready'
        }
        current_status = cache.get(status_key, None)
        if current_status is not None:
            status.update(current_status)
        return status_key, status

    def get_status(self, instance):
        """Retrives a status of a field from cache. Fields in state 'error' and
        'complete' will not retain the status after the call.

        """
        status_key, status = self._get_status(instance)
        if status['state'] in ['complete', 'error']:
            cache.delete(status_key)
        return status

    def set_status(self, instance, status):
        """Sets the field status for up to 5 minutes."""
        status_key = self.get_status_key(instance)
        cache.set(status_key, status, timeout=300)

    def set_error_status(self, instance, error):
        self.set_status(instance, {
            'state': 'error',
            'messages': [error]
        })

    def contribute_to_model(self, model, name):
        model._smartfields_managers[name] = self
        for d in self.dependencies:
            d.contribute_to_model(model)
