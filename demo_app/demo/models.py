from django.db import models
from django.contrib.sessions.models import Session

from smartfields import fields, processors
from smartfields.dependencies import Dependency, FileDependency

class SlugModel(models.Model):

    title = fields.CharField(max_length=32, dependencies=[
        Dependency(attname='slug', processor=processors.SlugProcessor())
    ])
    slug = models.SlugField(max_length=16, unique=True)
