# coding=utf-8
import smartfields

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify, force_unicode

lookup = {
    'ru': {
        "Snatch": "Спиздили",
        "Waterworld": "Водный Mир"
    }
}

def get_foreign_title(title_en, language=None, max_length=None):
    # some expensive API call that retrieves foreign versions of movie titles
    try:
        title = lookup[language][title_en]
    except KeyError:
        return ""
    if max_length is not None:
        return title[:max_length]
    return title


class Movie(models.Model):
    moderator = models.ForeignKey(User, null=True)
    title = smartfields.CharField(max_length=60, dependencies=[
        # testing self dependency
        smartfields.Dependency(processor=lambda t, **kwargs: t.title()),
        # testing forward dependency
        smartfields.Dependency(attname='russian_title', 
                               processor=get_foreign_title, 
                               processor_kwargs={
                                   'language': 'ru', 'max_length': 60
                               })
    ])
    russian_title = models.CharField(max_length=60)
    #slug = smartfields.SlugField(unique=True, dependencies=[
    #    smartfields.Dependency(processor=lambda t, **kwargs: slugify(t))
    #])
    #poster = smartfields.ImageField()
    #trailer = smartfields.VideoField()


    def __init__(self, *args, **kwargs):
        self.bar = 'bar'
        super(Movie, self).__init__(*args, **kwargs)