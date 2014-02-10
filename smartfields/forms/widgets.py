import json
from django.forms import widgets
from django.forms.widgets import Media, MediaDefiningClass, Widget

__all__ = (
    'Media', 'MediaDefiningClass', 'Widget', 'TextInput',
    'EmailInput', 'URLInput', 'NumberInput', 'PasswordInput',
    'HiddenInput', 'MultipleHiddenInput', 'ClearableFileInput',
    'FileInput', 'DateInput', 'DateTimeInput', 'TimeInput', 'Textarea', 'CheckboxInput',
    'Select', 'NullBooleanSelect', 'SelectMultiple', 'RadioSelect',
    'CheckboxSelectMultiple', 'MultiWidget', 'SplitDateTimeWidget',
)


class AttrsMixin(object):
    _attrs = {}
    _attrs_classes = set()
    _attrs_styles = {}
    _attrs_data = {}
    _attrs_cached = None

    def _get_attrs(self):
        if self._attrs_cached is not None:
            return self._attrs_cached
        attrs = self._attrs.copy()
        if self._attrs_classes:
            attrs['class'] = ' '.join(self._attrs_classes)
        if self._attrs_styles:
            styles = [':'.join(x) for x in self._attrs_styles.iteritems()]
            attrs['style'] = ';'.join(styles) + ';'
        if self._attrs_data:
            attrs['data'] = json.dumps(self._attrs_data)
        self._attrs_cached = attrs
        return attrs

    def _set_attrs(self, attrs):
        self._attrs_cached = None
        if attrs is None:
            self._attrs = {}
            self._attrs_classes = set()
            self._attrs_styles = {}
            self._attrs_data = {}
        else:
            for name, val in attrs.iteritems():
                if name == 'class':
                    if val is None:
                        self._attrs_classes = set()
                    else:
                        self._attrs_classes = self._attrs_classes.union(val.split())
                elif name == 'style':
                    if val is None:
                        self._attrs_styles = {}
                    else:
                        self._attrs_styles.update(
                            dict([x.split(':') for x in val.split(';') if x]))
                elif name == 'data':
                    if val is None:
                        self._attrs_data = {}
                    else:
                        self._attrs_data.update(val)
                else:
                    self._attrs[name] = val

    def _del_attrs(self):
        del self._attrs
        del self._attrs_classes
        del self._attrs_styles
        del self._attrs_data
        del self._attrs_cached

    attrs = property(_get_attrs, _set_attrs, _del_attrs)

class Label(AttrsMixin):
    def __init__(self, label, attrs=None):
        self.attrs = attrs

class SubWidget(AttrsMixin, widgets.SubWidget):
    pass


class WidgetMixin(AttrsMixin):

    def subwidgets(self, name, value, attrs=None, choices=()):
        """
        Yields all "subwidgets" of this widget. Used only by RadioSelect to
        allow template access to individual <input type="radio"> buttons.

        Arguments are the same as for render().
        """
        yield SubWidget(self, name, value, attrs, choices)

class Input(WidgetMixin, widgets.Input):
    pass


class TextInput(widgets.TextInput, Input):

    def __init__(self, *args, **kwargs):
        self.attrs = {'class': 'form-control'}
        super(TextInput, self).__init__(*args, **kwargs)


class NumberInput(widgets.NumberInput, TextInput):
    def __init__(self, *args, **kwargs):
        self.attrs = {'class': 'form-control'}
        super(NumberInput, self).__init__(*args, **kwargs)


class EmailInput(widgets.EmailInput, TextInput):
    def __init__(self, *args, **kwargs):
        self.attrs = {'class': 'form-control'}
        super(EmailInput, self).__init__(*args, **kwargs)


class URLInput(widgets.URLInput, TextInput):
    def __init__(self, *args, **kwargs):
        self.attrs = {'class': 'form-control'}
        super(URLInput, self).__init__(*args, **kwargs)


class PasswordInput(widgets.PasswordInput, Input):

    def __init__(self, *args, **kwargs):
        self.attrs = {
            'class': 'form-control',
            'autocomplete': 'off'
        }
        super(PasswordInput, self).__init__(*args, **kwargs)


class HiddenInput(widgets.HiddenInput, Input):
    pass


class MultipleHiddenInput(widgets.MultipleHiddenInput, HiddenInput):
    pass


class FileInput(widgets.FileInput, Input):
    # TODO: add progress
    pass


class ClearableFileInput(widgets.ClearableFileInput, FileInput):
    pass


class Textarea(WidgetMixin, widgets.Widget):
    def __init__(self, *args, **kwargs):
        self.attrs = {'class': 'form-control'}
        super(Textarea, self).__init__(*args, **kwargs)


class DateInput(widgets.DateInput, TextInput):
    def __init__(self, *args, **kwargs):
        self.attrs = {'class': 'form-control'}
        super(DateInput, self).__init__(*args, **kwargs)


class DateTimeInput(widgets.DateTimeInput, TextInput):
    def __init__(self, *args, **kwargs):
        self.attrs = {'class': 'form-control'}
        super(DateTimeInput, self).__init__(*args, **kwargs)


class TimeInput(widgets.TimeInput, TextInput):
    def __init__(self, *args, **kwargs):
        self.attrs = {'class': 'form-control'}
        super(TimeInput, self).__init__(*args, **kwargs)


class CheckboxInput(WidgetMixin, widgets.CheckboxInput):

    def __init__(self, *args, **kwargs):
        self.attrs = {'class': 'checkbox'}
        super(CheckboxInput, self).__init__(*args, **kwargs)
    

class Select(WidgetMixin, widgets.Select):
    pass


class NullBooleanSelect(widgets.NullBooleanSelect, Select):
    pass


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


class ChoiceFieldRenderer(AttrsMixin, widgets.ChoiceFieldRenderer):
    pass


class RadioFieldRenderer(widgets.RadioFieldRenderer, ChoiceFieldRenderer):
    choice_input_class = RadioChoiceInput


class CheckboxFieldRenderer(widgets.CheckboxFieldRenderer, ChoiceFieldRenderer):
    choice_input_class = CheckboxChoiceInput


class RadioSelect(widgets.RadioSelect, Select):
    renderer = RadioFieldRenderer


class CheckboxSelectMultiple(widgets.CheckboxSelectMultiple, SelectMultiple):
    renderer = CheckboxFieldRenderer


class MultiWidget(WidgetMixin, widgets.MultiWidget):
    pass


class SplitDateTimeWidget(widgets.SplitDateTimeWidget, MultiWidget):
    pass


class SplitHiddenDateTimeWidget(widgets.SplitHiddenDateTimeWidget, SplitDateTimeWidget):
    pass
