import random, time
from django.db import models
from django.contrib.sites.models import Site
from django.utils.text import slugify




class Dependency(object):

    def __init__(self, dependency, persistent=True, forward=True):
        self.forward = forward
        self.persistent = persistent
        self.dependency = dependency


    def handle_dependency(self, instance, this_field):
        this_value = getattr(instance, this_field.attname, None)
        # non persistent dependencies proceed only with an empty field value
        if not self.persistent and this_value: return

        if callable(self.dependency):
            new_value = self.dependency(instance, this_field, this_value)
            setattr(instance, this_field.attname, new_value)
        elif isinstance(self.dependency, basestring):
            other_field = instance._meta.get_field(self.dependency)
            other_value = getattr(instance, self.dependency)
            self.process_dependency(
                instance, (this_field, this_value), (other_field, other_value))
        elif self.dependency is not None:
            raise TypeError(
                "'%s' dependency has to be either a function or a name of a field "
                "attached to the same model." % field.name)


    def process_dependency(self, instance,
                           (this_field, this_value), (other_field, other_value)):
        if self.forward:
            attname = other_field.attname
            new_value = other_field.process_dependency(instance, other_value, this_value)
        else:
            attname = this_field.attname
            new_value = this_field.process_dependency(instance, this_value, other_value)
        setattr(instance, attname, new_value)





class Field(models.Field):
    dependencies = []

    def __init__(self, dependencies=None, *args, **kwargs):
        if dependencies is not None:
            self.dependencies = dependencies
        super(Field, self).__init__(*args, **kwargs)


    def contribute_to_class(self, cls, name):
        if self.dependencies:
            cls.smartfields_dependencies.append(self)
        super(Field, self).contribute_to_class(cls, name)




class SlugField(Field, models.SlugField):

    def __init__(self, default_dependency=None, *args, **kwargs):
        if default_dependency is not None:
            kwargs.update(dependencies=[Dependency(
                default_dependency, forward=False, persistent=False)])
        super(SlugField, self).__init__(*args, **kwargs)

    def process_dependency(self, instance, current_value, dependant_value):
        if dependant_value:
            slug = slugify(dependant_value)
            if self._unique:
                # modify a slug to make sure it's unique by adding a random number
                manager = instance.__class__._default_manager
                unique_slug = slug
                existing = manager.filter(**{self.name: unique_slug})
                while existing.exists():
                    unique_slug = "%s-%s" % (slug, random.randint(0, int(time.time())))
                    existing = manager.filter(**{self.name: unique_slug})
                slug = unique_slug
            return slug
        return current_value


class HTMLField(Field, models.TextField):

    def __init__(self, sanitize=True, dependencies=[]):
        pass