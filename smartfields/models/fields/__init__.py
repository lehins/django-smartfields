import random, time
from django.db import models
from django.utils.text import slugify

__all__ = ["SlugField"]

class Dependency(object):

    def __init__(self, dependency):
        self.dependency = dependency

    def handle_dependency(self, instance, field):
        if callable(self.dependency):
            value = self.dependency(instance)
            setattr(instance, field.attname, value)
            return value
        elif isinstance(self.dependency, basestring):
            value = getattr(instance, self.dependency)
            return field.process_dependency(instance, value)
        elif self.dependency is not None:
            raise TypeError(
                "'%s' dependency has to be either a function or a name of a field "
                "attached to the same model." % field.name)


class SlugField(models.SlugField):

    def __init__(self, default_dependency=None, **kwargs):
        assert bool(default_dependency) ^ bool(kwargs.get('default', None)), \
            "'default' and 'default_dependant' can not be used at the same time."
        self.dependencies = [Dependency(default_dependency)]
        super(SlugField, self).__init__(**kwargs)

    def contribute_to_class(self, cls, name):
        cls.smartfields_dependencies.append(self)
        super(SlugField, self).contribute_to_class(cls, name)

    def process_dependency(self, instance, value):
        if not self and value:
            slug = slugify(value)
            if self._unique:
                manager = instance.__class__._default_manager
                unique_slug = slug
                existing = manager.filter(**{self.name: unique_slug})
                while existing.exists():
                    unique_slug = "%s-%s" % (slug, random.randint(0, int(time.time())))
                    existing = manager.filter(**{self.name: unique_slug})
                slug = unique_slug
            setattr(instance, self.attname, slug)