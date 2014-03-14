import json
from crispy_forms.layout import Field, TEMPLATE_PACK
from crispy_forms.utils import render_field
from django import forms

from smartfields import settings


class FileField(Field):

    template = "%s/filefield.html" % TEMPLATE_PACK

    def __init__(self, *args, **kwargs):
        options = settings.PLUPLOAD_OPTIONS.copy()
        options.update(kwargs.pop('plupload_options', {}))
        options['multi_selection'] = False
        kwargs['data_plupload'] = json.dumps(options)
        kwargs['wrapper_class'] = kwargs.get('wrapper_class', 'smartfields-filefield')
        super(FileField, self).__init__(*args, **kwargs)


class ImageField(FileField):
    template = "%s/imagefield.html" % TEMPLATE_PACK

    def __init__(self, *args, **kwargs):
        kwargs['wrapper_class'] = kwargs.get('wrapper_class', 'smartfields-imagefield')
        super(ImageField, self).__init__(*args, **kwargs)


class VideoField(FileField):
    template = "%s/videofield.html" % TEMPLATE_PACK

    def __init__(self, *args, **kwargs):
        kwargs['wrapper_class'] = kwargs.get('wrapper_class', 'smartfields-imagefield')
        super(VideoField, self).__init__(*args, **kwargs)



class LimitedField(Field):
    template = "%s/limitedfield.html" % TEMPLATE_PACK

    def __init__(self, field, feedback_text=None, *args, **kwargs):
        self.field = field
        kwargs['wrapper_class'] = kwargs.get('wrapper_class', '') + ' smartfields-limitedfield'
        self.minimum = kwargs.pop('minimum', None)
        self.maximum = kwargs.pop('maximum', None)
        self.feedback_text = feedback_text
        kwargs['css_class'] = "smartfield"
        super(LimitedField, self).__init__(field, *args, **kwargs)


    def render(self, form, form_style, context, **kwargs):
        try:
            feedback_text = ''
            maximum, minimum = self.maximum, self.minimum
            field_instance = form.fields[self.field]
            if isinstance(field_instance, forms.CharField):
                maximum = field_instance.max_length or maximum
                minimum = field_instance.min_length or minimum
                if maximum and isinstance(field_instance.widget, forms.Textarea):
                    # django doesn't add it for some reason
                    self.attrs.update({'maxlength': maximum})
                if maximum:
                    feedback_text = "/%s %s" % (
                        maximum, self.feedback_text or 'characters remaining')
            elif maximum is not None:
                self.attrs['data-maximum'] = maximum

            if minimum is not None:
                self.attrs['data-minimum'] = minimum
            if feedback_text:
                context.update({'wrapper_class': self.wrapper_class,
                                'feedback_text': feedback_text})
        except KeyError: pass

        return render_field(self.field, form, form_style, context,
                            template=self.template, attrs=self.attrs, **kwargs)
