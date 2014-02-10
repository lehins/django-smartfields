from django.forms import fields

from smartfields.forms.widgets import (
    TextInput, NumberInput, EmailInput, URLInput, HiddenInput,
    MultipleHiddenInput, ClearableFileInput, CheckboxInput, Select,
    NullBooleanSelect, SelectMultiple, DateInput, DateTimeInput, TimeInput,
    SplitDateTimeWidget, SplitHiddenDateTimeWidget
)

class Field(fields.Field):
    widget = TextInput
    hidden_widget = HiddenInput


class CharField(fields.CharField, Field):
    widget = TextInput
    
    def __init__(self, placeholder=None, **kwargs):
        self.placeholder = placeholder
        super(CharField, self).__init__(**kwargs)

    def widget_attrs(self, widget):
        if self.placeholder is not None:
            widget.attrs = {'placeholder': self.placeholder}
        return super(CharField, self).widget_attrs(widget)


class IntegerField(fields.IntegerField, Field):
    widget = NumberInput
    
    def __init__(self, placeholder=None, **kwargs):
        self.placeholder = placeholder
        super(IntegerField, self).__init__(**kwargs)

    def widget_attrs(self, widget):
        if self.placeholder is not None:
            widget.attrs = {'placeholder': self.placeholder}
        return super(IntegerField, self).widget_attrs(widget)

class FloatField(fields.FloatField, IntegerField):
    widget = NumberInput
    

class DecimalField(fields.DecimalField, IntegerField):
    widget = NumberInput

class DateField(fields.DateField, Field):
    widget = DateInput










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

    