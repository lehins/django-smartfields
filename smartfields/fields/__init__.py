from django.db import models
from django.conf import settings

from smartfields.managers import FieldManager
from smartfields.models import SmartfieldsModelMixin

__all__ = [
    'Field', 'CharField', 'SlugField'
]

class Field(models.Field):
    FAIL_SILENTLY = getattr(settings, 'SMARTFIELDS_FAIL_SILENTLY', True)
    manager_class = FieldManager
    manager = None
    
    def __init__(self, dependencies=None, *args, **kwargs):
        if dependencies is not None:
            self.manager = self.manager_class(self, dependencies)
        super(Field, self).__init__(*args, **kwargs)


    def contribute_to_class(self, cls, name):
        super(Field, self).contribute_to_class(cls, name)
        if not issubclass(cls, SmartfieldsModelMixin):
            cls.__bases__ = (SmartfieldsModelMixin,) + cls.__bases__
        if not hasattr(cls, '_smartfields_managers'):
            cls._smartfields_managers = {}
        if self.manager is not None:
            cls._smartfields_managers[name] = self.manager


    def deconstruct(self):
        name, path, args, kwargs = super(Field, self).deconstruct()
        if self.manager is not None:
            kwargs['dependencies'] = self.manager.dependencies
        return name, path, args, kwargs


    def get_status(self, instance):
        return self.manager.get_status(instance)


class CharField(Field, models.CharField):
    pass


class SlugField(Field, models.SlugField):
    pass