from django.db import models

class Model(models.Model):

    smartfields_managers = None

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super(Model, self).__init__(*args, **kwargs)
        self.smartfields_handle()


    def save(self, *args, **kwargs):
        self.smartfields_handle()
        super(Model, self).save(*args, **kwargs)


    def delete(self, *args, **kwargs):
        if self.smartfields_managers is not None:
            for manager in self.smartfields_managers:
                delete_handle = getattr(manager.field, 'delete', None)
                if callable(delete_handle):
                    delete_handle(self)
        return super(Model, self).delete(*args, **kwargs)
                    


    def smartfields_handle(self):
        if self.smartfields_managers is not None:
            for manager in self.smartfields_managers:
                manager.handle(self)


    def smartfield_status(self, field_name):
        """A way to find out a status a filed."""
        field = self._meta.get_field(field_name)
        if hasattr(field, 'get_status'):
            return field.get_status(self)