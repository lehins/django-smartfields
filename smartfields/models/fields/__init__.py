import random, time
from django.db import models
from django.contrib.sites.models import Site
from django.utils.text import slugify

from smartfields import forms

#__all__ = [str(x) for x in (
#    'AutoField', 'BLANK_CHOICE_DASH', 'BigIntegerField', 'BinaryField',
#    'BooleanField', 'CharField', 'CommaSeparatedIntegerField', 'DateField',
#    'DateTimeField', 'DecimalField', 'EmailField', 'Empty', 'Field',
#    'FieldDoesNotExist', 'FilePathField', 'FloatField',
#    'GenericIPAddressField', 'IPAddressField', 'IntegerField', 'NOT_PROVIDED',
#    'NullBooleanField', 'PositiveIntegerField', 'PositiveSmallIntegerField',
#    'SlugField', 'SmallIntegerField', 'TextField', 'TimeField', 'URLField',
#)]


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

class Field(models.Field):
    formfield_class = forms.CharField

    def __init__(self, placeholder=None, **kwargs):
        self.placeholder = placeholder
        super(Field, self).__init__(**kwargs)
        
    def formfield(self, **kwargs):
        defaults = {
            'form_class': self.formfield_class,
            'placeholder': self.placeholder
        }
        defaults.update(kwargs)
        return super(Field, self).formfield(**defaults)


class CharField(models.CharField, Field):
    pass


class CommaSeparatedIntegerField(models.CommaSeparatedIntegerField, Field):
    pass


class DateField(models.DateField, Field):
    formfield_class = forms.DateField


class DateTimeField(models.DateTimeField, DateField):
    formfield_class = forms.DateTimeField


class DecimalField(models.DecimalField, Field):
    formfield_class = forms.DecimalField


class EmailField(models.EmailField, CharField):
    formfield_class = forms.EmailField


class FilePathField(models.FilePathField, Field):
    formfield_class = forms.FilePathField



class SlugField(Field, models.SlugField):
    formfield_class = forms.SlugField

    def __init__(self, default_dependency=None, url_prefix=None, **kwargs):
        assert not (default_dependency and kwargs.get('default', None)), \
            "'default' and 'default_dependant' can not be used at the same time."
        self.dependencies = [Dependency(default_dependency)]
        self.url_prefix = url_prefix
        super(SlugField, self).__init__(**kwargs)

    def contribute_to_class(self, cls, name):
        cls.smartfields_dependencies.append(self)
        super(SlugField, self).contribute_to_class(cls, name)

    def process_dependency(self, instance, value):
        cur_value = getattr(instance, self.attname, None)
        if not cur_value and value:
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

    def formfield(self, **kwargs):
        if self.url_prefix is None:
            url_prefix = "%s/%s/" % (
                Site.objects.get_current().domain, self.model._meta.app_label)
        else:
            url_prefix = self.url_prefix
            
        defaults = {'url_prefix': url_prefix}
        defaults.update(kwargs)
        return super(SlugField, self).formfield(**defaults)
