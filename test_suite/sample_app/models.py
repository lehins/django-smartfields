# coding=utf-8
import smartfields

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

from smartfields import processors


class ProcessorTestingModel(models.Model):
    smartfields_order = ['field_1', 'field_3']

    field_1 = smartfields.CharField(max_length=15, dependencies=[
        # testing forward dependency
        smartfields.Dependency(attname='field_2', processor=lambda v, **kwargs: slugify(v)),
        # testing self dependency
        smartfields.Dependency(processor=lambda v, **kwargs: v.title().replace(" ", "_"))
    ])
    field_2 = models.SlugField(max_length=15)
    field_3 = smartfields.SlugField(max_length=15, unique=True, dependencies=[
        # testing regular dependency and SlugProcessor
        smartfields.Dependency('field_1', processor=processors.SlugProcessor())
    ])
    