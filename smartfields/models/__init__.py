from django.conf import settings
from django.db import models
from smartfields.models.fields import *
from smartfields.models.fields.files import *
from smartfields.models.fields.managers import *
from smartfields.models.fields.dependencies import *

if 'south' in settings.INSTALLED_APPS:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ['^smartfields\.models\.fields\.files\.FileField',
                                 '^smartfields\.models\.fields\.files\.ImageField',
                                 '^smartfields\.models\.fields\.files\.VideoField',
                                 '^smartfields\.models\.fields\.SlugField',
                                 '^smartfields\.models\.fields\.HTMLField'])


class ModelMixin(object):

    smartfields_managers = None

    def __init__(self, *args, **kwargs):
        super(ModelMixin, self).__init__(*args, **kwargs)
        self.smartfields_handle()


    def save(self, *args, **kwargs):
        self.smartfields_handle()
        super(ModelMixin, self).save(*args, **kwargs)


    def delete(self, *args, **kwargs):
        if self.smartfields_managers is not None:
            for manager in self.smartfields_managers:
                delete_handle = getattr(manager.field, 'delete', None)
                if callable(delete_handle):
                    delete_handle(self)
        return super(ModelMixin, self).delete(*args, **kwargs)
                    


    def smartfields_handle(self):
        if self.smartfields_managers is not None:
            for manager in self.smartfields_managers:
                manager.handle(self)


    def smartfields_update(self, field_names=None):
        if self.smartfields_managers is not None:
            if field_names is not None:
                field_names = set(field_names)
            for manager in self.smartfields_managers:
                if not field_names or manager.field.name in field_names:
                    manager.update(self)


    def smartfield_status(self, field_name):
        """A way to find out a status a filed."""
        field = self._meta.get_field(field_name)
        if hasattr(field, 'get_status'):
            return field.get_status(self)



class Model(ModelMixin, models.Model):

    class Meta:
        abstract = True