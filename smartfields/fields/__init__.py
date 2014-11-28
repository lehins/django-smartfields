from django.db import models
from django.conf import settings

from smartfields.dependencies import Dependency
from smartfields.managers import FieldManager
from smartfields.models import SmartfieldsModelMixin

__all__ = [
    'Field', 'CharField'
]

class Field(models.Field):
    FAIL_SILENTLY = getattr(settings, 'SMARTFIELDS_FAIL_SILENTLY', True)
    manager_class = FieldManager
    
    def __init__(self, dependencies=None, *args, **kwargs):
        self.manager = self.manager_class(self, dependencies=dependencies)
        super(Field, self).__init__(*args, **kwargs)


    def contribute_to_class(self, cls, name):
        super(Field, self).contribute_to_class(cls, name)
        if not issubclass(cls, SmartfieldsModelMixin):
            cls.smartfields_managers = []
            cls.__bases__ = (SmartfieldsModelMixin,) + cls.__bases__
            print name
        cls.smartfields_managers.append(self.manager)


    def deconstruct(self):
        name, path, args, kwargs = super(Field, self).deconstruct()
        if self.manager.dependencies:
            kwargs['dependencies'] = self.manager.dependencies
        return name, path, args, kwargs


    def get_status(self, instance):
        return self.manager.get_status(instance)


class CharField(Field, models.CharField):
    pass