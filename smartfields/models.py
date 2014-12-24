
class SmartfieldsModelMixin(object):

    @property
    def smartfields_managers(self):
        if hasattr(self, '_smartfields_managers_list'):
            return getattr(self, '_smartfields_managers_list')
        managers = []
        for field in self._meta.fields:
            if field.name in self._smartfields_managers:
                managers.append(self._smartfields_managers[field.name])
        self._smartfields_managers_list = managers
        return self._smartfields_managers_list

    def __init__(self, *args, **kwargs):
        self.smartfields_handle('pre_init', *args, **kwargs)
        super(SmartfieldsModelMixin, self).__init__(*args, **kwargs)
        self.smartfields_handle('post_init', *args, **kwargs)

    def save(self, *args, **kwargs):
        fresh_keys = None
        if self.pk is None:
            fresh_keys = []
            for manager in self.smartfields_managers:
                if manager.should_process and manager.has_stashed_value:
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

    def smartfields_handle(self, event, *args, **kwargs):
        for manager in self.smartfields_managers:
            manager.handle(self, event, *args, **kwargs)

    def smartfields_process(self, field_names=None):
        if field_names is None:
            for manager in self.smartfields_managers:
                manager.process(self, force=True)
        else:
            for field_name in field_names:
                self._smartfields_managers[field_name].process(self, force=True)
    smartfields_process.alters_data = True

    def smartfields_get_field_status(self, field_name):
        """A way to find out a status of a filed."""
        manager = self._smartfields_managers.get(field_name, None)
        if manager is not None:
            return manager.get_status(self)
        return {'state': 'ready'}