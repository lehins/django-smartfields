from django.apps import apps
from django.contrib.sites.models import Site
from django.utils.functional import SimpleLazyObject

__all__ = [
    'HTMLTagHandler'
]

class HTMLTagHandler(object):
    template = None
    base_url = None

    def __init__(self, template=None, base_url=None, context=None):
        self.template = template or self.template
        assert self.template is not None, "template is required"
        self.base_url = base_url or self.base_url
        self.context = context or {}

    def get_extra_context(self):
        return {}

    def __call__(self, value, instance, field, field_value, *args, **kwargs):
        def renderer():
            if not field_value:
                return ""
            context = {
                'value': value,
                'instance': instance,
                'field': field,
                'field_value': field_value
            }
            if self.base_url is not None:
                self.context['base_url'] = self.base_url
            elif apps.is_installed('django.contrib.sites'):
                self.context['base_url'] = "//%s" % Site.objects.get_current().domain
            context.update(self.context)
            context.update(self.get_extra_context())
            return self.template.format(**context)
        setattr(instance, "%s_html_tag" % field.name, SimpleLazyObject(renderer))