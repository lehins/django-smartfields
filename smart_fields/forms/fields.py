from django import forms
from smart_fields.forms.widgets import SmartTextInput, SmartTextarea

class SmartCharField(forms.CharField):
    widget=SmartTextInput

    def to_python(self, value):
        # new-line chars are length of 2 when submitted, this hack fixes that issue.
        return '\n'.join(value.splitlines())

    def widget_attrs(self, widget):
        attrs = super(SmartCharField, self).widget_attrs(widget)
        if self.max_length is not None and isinstance(widget, forms.TextInput):
            # The HTML attribute is maxlength, not max_length.
            attrs.update({'maxlength': str(self.max_length)})
        elif isinstance(widget, forms.Textarea):
            # Will enforce it using JS
            attrs.update({'class': 'sf-limit-length'})
            if self.max_length is not None:
                attrs.update({'data-maxlength': str(self.max_length)})
            if self.min_length is not None:
                attrs.update({'data-minlength': str(self.min_length)})
        return attrs

    class Media:
        js = ('js/smartfields.js',)

class SmartTextField(SmartCharField):
    widget=SmartTextarea
