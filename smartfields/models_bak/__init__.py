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




class Model(ModelMixin, models.Model):

    class Meta:
        abstract = True