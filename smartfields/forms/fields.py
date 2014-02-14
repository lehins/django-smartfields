from django.forms import fields

from smartfields.forms.widgets import (
    TextInput, NumberInput, EmailInput, URLInput, HiddenInput,
    MultipleHiddenInput, ClearableFileInput, CheckboxInput, Select,
    NullBooleanSelect, SelectMultiple, DateInput, DateTimeInput, TimeInput,
    SplitDateTimeWidget, SplitHiddenDateTimeWidget, SlugInput, TextareaLimited
)

class Field(fields.Field):
    widget = TextInput
    hidden_widget = HiddenInput

    def __init__(self, placeholder=None, **kwargs):
        self.placeholder = placeholder
        super(Field, self).__init__(**kwargs)

    def widget_attrs(self, widget):
        if self.placeholder is not None:
            widget.attrs['placeholder'] = self.placeholder
        return super(Field, self).widget_attrs(widget)


class CharField(fields.CharField, Field):

    def widget_attrs(self, widget):
        if self.max_length is not None and isinstance(widget, TextareaLimited):
            widget.attrs['data-maxlength'] = self.max_length
        attrs = super(CharField, self).widget_attrs(widget)
        return attrs

class IntegerField(fields.IntegerField, Field):
    widget = NumberInput


class FloatField(fields.FloatField, IntegerField):
    pass
    

class DecimalField(fields.DecimalField, IntegerField):
    pass


class DateField(fields.DateField, Field):
    widget = DateInput


class TimeField(fields.TimeField, Field):
    widget = TimeInput


class DateTimeField(fields.DateTimeField, Field):
    widget = DateTimeInput


class RegexField(fields.RegexField, CharField):
    pass


class EmailField(fields.EmailField, CharField):
    widget = EmailInput


class FileField(fields.FileField, Field):
    widget = ClearableFileInput


class ImageField(fields.ImageField, FileField):
    pass


class URLField(fields.URLField, CharField):
    widget = URLInput


class BooleanField(fields.BooleanField, Field):
    widget = CheckboxInput


class NullBooleanField(fields.NullBooleanField, BooleanField):
    widget = NullBooleanSelect


class ChoiceField(fields.ChoiceField, Field):
    widget = Select


class TypedChoiceField(fields.TypedChoiceField, ChoiceField):
    pass

class MultipleChoiceField(fields.MultipleChoiceField, ChoiceField):
    widget = SelectMultiple
    hidden_widget = MultipleHiddenInput


class TypedMultipleChoiceField(fields.TypedMultipleChoiceField, MultipleChoiceField):
    pass


class ComboField(fields.ComboField, Field):
    pass


class MultiValueField(fields.MultiValueField, Field):
    pass


class FilePathField(fields.FilePathField, ChoiceField):
    pass


class SplitDateTimeField(fields.SplitDateTimeField, MultiValueField):
    widget = SplitDateTimeWidget
    hidden_widget = SplitHiddenDateTimeWidget
    


class IPAddressField(fields.IPAddressField, CharField):
    pass


class GenericIPAddressField(fields.GenericIPAddressField, CharField):
    pass


class SlugField(fields.SlugField, CharField):
    widget = SlugInput

    def __init__(self, url_prefix=None, **kwargs):
        super(SlugField, self).__init__(**kwargs)
        self.widget.url_prefix = url_prefix




class A(object):
    def __init__(self, x, y):
        print "class A"
        print x
        print y


class B(A):
    def __init__(self, x):
        print "class B"
        print x
        super(B, self).__init__(x, 5)

class C(A):
    def __init__(self, x):
        print "class C"
        print x
        super(C, self).__init__(0)

class D(C, B):
    def __init__(self, x):
        print "class D"
        print x
        super(D, self).__init__(x+1)
        #super(B, self).__init__(x, 4)
        #B.__init__(self, x)

    