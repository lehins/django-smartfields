import time, random
from django.contrib.sites.models import Site
from django.utils.functional import SimpleLazyObject
from django.utils.text import slugify
from django.utils.encoding import force_text

from smartfields.processors.base import BaseProcessor
from smartfields.utils import apps

try:
    from bs4 import BeautifulSoup, Comment
except ImportError:
    pass

__all__ = [
    'CropProcessor', 'UniqueProcessor', 'SlugProcessor', 'HTMLProcessor', 'HTMLTagProcessor'
]


class CropProcessor(BaseProcessor):
    padding = 0

    def __init__(self, padding=None, **kwargs):
        self.padding = padding or self.padding
        assert self.padding >=0, "padding should not be a negative number"
        super(CropProcessor, self).__init__(**kwargs)

    def process(self, value, dependee=None, padding=None, **kwargs):
        if dependee is None or dependee.max_length is None:
            return value
        padding = padding or self.padding
        assert padding < dependee.max_length, "padding is set too high."
        if len(value) > (dependee.max_length - padding):
            return value[:dependee.max_length - padding]
        return value


class UniqueProcessor(CropProcessor):
    separator = ''
    max_attempts = 100

    def get_random(self, padding):
        if padding is None:
            upper = int(time.time())
        else:
            upper = 10**(padding - len(self.separator)) - 1
        return random.randint(0, upper)

    def get_padding(self, max_length):
        if max_length is not None:
            # use at least 10% of max_length at most 5 chars for random number
            return min(5, int(max_length/10) or 1) + len(self.separator)

    def process(self, value, instance, field, dependee=None, iexact=False, **kwargs):
        # make sure value can at least fit in
        value = super(UniqueProcessor, self).process(
            value, instance=instance, field=field, dependee=dependee, **kwargs)
        if dependee is None or not dependee._unique:
            return value
        manager = instance.__class__._default_manager
        unique_value = value or ""
        filter_key = "%s__iexact" % field.name if iexact else field.name
        existing = manager.filter(**{filter_key: unique_value})
        if instance.pk is not None:
            existing = existing.exclude(pk=instance.pk)
        padding = self.get_padding(dependee.max_length)
        if padding is not None and existing.exists():
            # if value exists already, crop it more so we can add some random numbers
            value = super(UniqueProcessor, self).process(
                value, instance=instance, field=field, dependee=dependee, 
                padding=padding, **kwargs)
        attempt = 0 # just so we can guarantee it doesn't get stuck in infinite loop
        while existing.exists() and attempt < self.max_attempts:
            unique_value = "%s%s%s" % (value, self.separator, self.get_random(padding))
            existing = manager.filter(**{filter_key: unique_value})
            if instance.pk is not None:
                existing = existing.exclude(pk=instance.pk)
            attempt+= 1
        return unique_value


class SlugProcessor(UniqueProcessor):
    separator = '-'

    def process(self, value, **kwargs):
        kwargs.setdefault('iexact', True)
        value = slugify(force_text(value).lower())
        return super(SlugProcessor, self).process(value, **kwargs)


class HTMLProcessor(CropProcessor):
    """Basic HTML processor that stripps out all the tags."""

    parser = "lxml"

    def remove_comments(self, soup):
        for comment in soup.findAll(text=lambda text: isinstance(text, Comment)):
            comment.extract()

    def process_tag(self, tag):
        tag.hidden = True

    def process(self, value, **kwargs):
        soup = BeautifulSoup(value, self.parser)
        self.remove_comments(soup)
        for tag in soup.findAll(True):
            self.process_tag(tag)
        value = soup.renderContents().decode('utf8')
        return super(HTMLProcessor, self).process(value, **kwargs)


class HTMLTagProcessor(BaseProcessor):
    template = None
    base_url = None

    def __init__(self, template=None, base_url=None, **kwargs):
        self.template = template or self.template
        assert self.template is not None, "template is required"
        self.base_url = base_url or self.base_url
        super(HTMLTagProcessor, self).__init__(**kwargs)
        
    def process(self, value, instance, field, **kwargs):
        def renderer():
            context = {
                'value': value,
                'instance': instance,
                'field': field,
            }
            if self.base_url is not None:
                context['base_url'] = self.base_url
            elif apps.is_installed('django.contrib.sites'):
                context['base_url'] = "//%s" % Site.objects.get_current().domain
            context.update(kwargs)
            return self.template.format(**context)
        return SimpleLazyObject(renderer)
