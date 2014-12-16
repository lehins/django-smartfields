
from django.utils import six

class SmartfieldsModelMixin(object):

    def __init__(self, *args, **kwargs):
        self.smartfields_handle('pre_init', *args, **kwargs)
        super(SmartfieldsModelMixin, self).__init__(*args, **kwargs)
        self.smartfields_handle('post_init', *args, **kwargs)

    def save(self, *args, **kwargs):
        fresh_keys = None
        if self.pk is None:
            fresh_keys = []
            for name, manager in six.iteritems(self._smartfields_managers):
                if manager.has_processors and manager.has_stashed_value:
                    fresh_keys.append((manager.get_status_key(self), manager))
        self.smartfields_handle('pre_save', *args, **kwargs)
        super(SmartfieldsModelMixin, self).save(*args, **kwargs)
        if fresh_keys is not None:
            for key, manager in fresh_keys:
                cur_status = manager._get_status(self, status_key=key)[1]
                if cur_status is not None:
                    manager.set_status(self, cur_status)
        self.smartfields_handle('post_save', *args, **kwargs)
    save.alters_data = True

    def delete(self, *args, **kwargs):
        self.smartfields_handle('pre_delete', *args, **kwargs)
        super(SmartfieldsModelMixin, self).delete(*args, **kwargs)
        self.smartfields_handle('post_delete', *args, **kwargs)
    delete.alters_data = True

    def _smartfields_get_managers(self):
        if hasattr(self, 'smartfields_order'):
            managers = []
            for field_name in self.smartfields_order:
                managers.append(self._smartfields_managers[field_name])
            for field_name, manager in self._smartfields_managers.items():
                if field_name not in self.smartfields_order:
                    managers.append(manager)
        else:
            managers = self._smartfields_managers.values()
        return managers

    def smartfields_handle(self, event, *args, **kwargs):
        for manager in self._smartfields_get_managers():
            manager.handle(self, event, *args, **kwargs)

    def smartfields_process(self, field_names=None):
        if field_names is None:
            for manager in self._smartfields_get_managers():
                manager.process(self, force=True)
        else:
            for field_name in field_names:
                self._smartfields_managers[field_name].process(self, force=True)


    def smartfields_get_field_status(self, field_name):
        """A way to find out a status a filed."""
        field = self._meta.get_field(field_name)
        if hasattr(field, 'get_status'):
            return field.get_status(self)
