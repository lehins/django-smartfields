from django.forms import widgets
from django.forms.widgets import Media, MediaDefiningClass, Widget
from django.utils.safestring import mark_safe

from smartfields.forms.utils import AttrsDict

__all__ = (
    'Media', 'MediaDefiningClass', 'Widget', 'TextInput',
    'EmailInput', 'URLInput', 'NumberInput', 'PasswordInput',
    'HiddenInput', 'MultipleHiddenInput', 'ClearableFileInput',
    'FileInput', 'DateInput', 'DateTimeInput', 'TimeInput', 'Textarea', 'CheckboxInput',
    'Select', 'NullBooleanSelect', 'SelectMultiple', 'RadioSelect',
    'CheckboxSelectMultiple', 'MultiWidget', 'SplitDateTimeWidget',
    'TextareaLimited', 'SlugInput'
)


class SubWidget(widgets.SubWidget):
    def __init__(self, parent_widget, name, value, attrs, choices):
        super(SubWidget, self).__init__(
            parent_widget, name, value, AttrsDict(attrs), choices)
    

class Widget(Widget):

    def __init__(self, attrs=None):
        self.attrs = AttrsDict(attrs)

    def subwidgets(self, name, value, attrs=None, choices=()):
        yield SubWidget(self, name, value, attrs, choices)

    def build_attrs(self, extra_attrs=None, **kwargs):
        attrs = AttrsDict(self.attrs, **kwargs)
        if extra_attrs:
            attrs.update(extra_attrs)
        return attrs


class Input(widgets.Input, Widget):
    pass


class TextInput(widgets.TextInput, Input):

    def __init__(self, *args, **kwargs):
        super(TextInput, self).__init__(*args, **kwargs)
        self.attrs['class'] = 'form-control'


class NumberInput(widgets.NumberInput, TextInput):
    pass


class EmailInput(widgets.EmailInput, TextInput):
    pass


class URLInput(widgets.URLInput, TextInput):
    pass


class PasswordInput(widgets.PasswordInput, TextInput):

    def __init__(self, *args, **kwargs):
        super(PasswordInput, self).__init__(*args, **kwargs)
        self.attrs['autocomplete'] = self.attrs.get('autocomplete', 'off')


class HiddenInput(widgets.HiddenInput, Input):
    pass


class MultipleHiddenInput(widgets.MultipleHiddenInput, HiddenInput):
    pass

class FileInput(widgets.FileInput, Input):
    pass

class ClearableFileInput(widgets.ClearableFileInput, FileInput):
    pass


class Textarea(widgets.Textarea, Widget):
    def __init__(self, *args, **kwargs):
        super(Textarea, self).__init__(*args, **kwargs)
        self.attrs['class'] = 'form-control'


class TextareaLimited(Textarea):
    def __init__(self, *args, **kwargs):
        super(TextareaLimited, self).__init__(*args, **kwargs)
        self.attrs['class'] = 'textarea-limited'


# possibly import/implement DateTimeBaseInput, will depend on render

class DateInput(widgets.DateInput, TextInput):
    def __init__(self, attrs={}, **kwargs):
        super(DateInput, self).__init__(attrs=attrs, **kwargs)


class DateTimeInput(widgets.DateTimeInput, TextInput):
    def __init__(self, attrs={}, **kwargs):
        super(DateTimeInput, self).__init__(attrs=attrs, **kwargs)


class TimeInput(widgets.TimeInput, TextInput):
    def __init__(self, attrs={}, **kwargs):
        super(TimeInput, self).__init__(attrs={}, **kwargs)


class CheckboxInput(widgets.CheckboxInput, Widget):
    def __init__(self, attrs={}, **kwargs):
        super(CheckboxInput, self).__init__(attrs=attrs, **kwargs)


class Select(widgets.Select, Widget):
    def __init__(self, attrs={}, **kwargs):
        super(Select, self).__init__(attrs=attrs, **kwargs)
    

class NullBooleanSelect(widgets.NullBooleanSelect, Select):
    def __init__(self, attrs={}, **kwargs):
        super(NullBooleanSelect, self).__init__(attrs=attrs, **kwargs)


class SelectMultiple(widgets.NullBooleanSelect, Select):
    pass



class ChoiceInput(widgets.ChoiceInput, SubWidget):
    pass


class RadioChoiceInput(widgets.RadioChoiceInput, SubWidget):
    pass


class RadioInput(widgets.RadioInput, RadioChoiceInput):
    pass


class CheckboxChoiceInput(widgets.CheckboxChoiceInput, ChoiceInput):
    pass


class ChoiceFieldRenderer(widgets.ChoiceFieldRenderer):
    def __init__(self, name, value, attrs, choices):
        super(ChoiceFieldRenderer, self).__init__(
            name, value, AttrsDict(attrs), choices)

class RadioFieldRenderer(widgets.RadioFieldRenderer, ChoiceFieldRenderer):
    choice_input_class = RadioChoiceInput


class CheckboxFieldRenderer(widgets.CheckboxFieldRenderer, ChoiceFieldRenderer):
    choice_input_class = CheckboxChoiceInput


class RadioSelect(widgets.RadioSelect, Select):
    renderer = RadioFieldRenderer


class CheckboxSelectMultiple(widgets.CheckboxSelectMultiple, SelectMultiple):
    renderer = CheckboxFieldRenderer


class MultiWidget(widgets.MultiWidget, Widget):
    def __init__(self, attrs={}, *args, **kwargs):
        super(MultiWidget, self).__init__(attrs=attrs, *args, **kwargs)


class SplitDateTimeWidget(widgets.SplitDateTimeWidget, MultiWidget):
    def __init__(self, attrs={}, *args, **kwargs):
        super(SplitDateTimeWidget, self).__init__(attrs=attrs, *args, **kwargs)


class SplitHiddenDateTimeWidget(widgets.SplitHiddenDateTimeWidget, SplitDateTimeWidget):
    def __init__(self, attrs={}, *args, **kwargs):
        super(SplitHiddenDateTimeWidget, self).__init__(attrs=attrs, *args, **kwargs)




class SlugInput(TextInput):
    url_prefix = None
    template = '<div class="input-group">\n<span class="input-group-addon">' \
               '%(url_prefix)s</span>\n%(widget)s</div>'

    def render(self, *args, **kwargs):
        widget = super(SlugInput, self).render(*args, **kwargs)
        if self.url_prefix:
            return mark_safe(self.template % {
                'url_prefix': self.url_prefix,
                'widget': widget
            })
        return widget