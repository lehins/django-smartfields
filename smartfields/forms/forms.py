from django import forms
from django.forms.util import ErrorList
from django.utils.html import conditional_escape
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils import six

from smartfields.forms import widgets

__all__ = ["Form", "ModelForm"]

# add placeholder to all fields
# field inside label, outside label

class DivErrorList(ErrorList):

    def __unicode__(self):
        return self.as_divs()

    def as_divs(self):
        if not self: return u''
        return u'<div class="errorlist">%s</div>' % ''.join([
                u'<div class="alert alert-danger">%s</div>' % 
                e for e in self])


class BoundField(forms.forms.BoundField):
    default_css_classes = []
    
    def as_widget(self, widget=None, attrs=None, only_initial=False):
        return super(BoundField, self).as_widget(
            widget=widget, attrs=attrs, only_initial=only_initial)
            

class FormMixin(object):
    row_css_class_prefix = "col-md-"
    fields_layout = []
    bound_field_class = BoundField
    #fields_layout = [(('title', 'slug'), ('image')), (('description',), None)]

    def __getitem__(self, name):
        "Returns a new version of BoundField with the given name."
        try:
            field = self.fields[name]
        except KeyError:
            raise KeyError('Key %r not found in Form' % name)
        return self.bound_field_class(self, field, name)

    def _render_field(self, bf, template, help_text_html, bf_errors=None):
        bf_errors = bf_errors or self.error_class(
            [conditional_escape(error) for error in bf.errors])
        extra_classes = "form-group"
        if bf_errors:
            extra_classes+= " has-error"
        if isinstance(bf.field.widget, forms.CheckboxInput):
            extra_classes+= " checkbox"
        css_classes = bf.css_classes(extra_classes)
        html_class_attr = ' class="%s"' % css_classes
        field = six.text_type(bf)
        if bf.label:
            contents = conditional_escape(force_text(bf.label))
            label_suffix = None
            attrs = None
            if isinstance(bf.field.widget, forms.CheckboxInput):
                contents = mark_safe("%s %s" % (field, contents))
                label_suffix = ''
                field = ''
            else:
                attrs = {'class': 'control-label'}
            label = bf.label_tag(
                contents, attrs=attrs, label_suffix=label_suffix) or ''
        else:
            label = ''
        if bf.help_text:
            help_text = help_text_html % force_text(bf.help_text)
        else:
            help_text = ''
        if bf.errors:
            error_class = 'has-error'
        else:
            error_class = ''
        return template % {
            'errors': force_text(bf_errors),
            'label': force_text(label),
            'field': field,
            'help_text': help_text,
            'html_class_attr': html_class_attr,
            'error_class': error_class
        }
    
    def _bootstrap_html_output(self, full_row, sub_row, error_row, help_text_html):
        top_errors = self.non_field_errors()
        output, hidden_fields = [], []

        rendered_names = []

        for row in self.fields_layout:
            column_width = 12/len(row)
            rendered_rows = []
            for column in row:
                if column is None:
                    rendered_rows.append('<div class="%soffset-%s"></div>' % (
                        self.row_css_class_prefix, column_width))
                    continue
                sub_rows = []
                for name in column:
                    field = self.fields[name]
                    bf = self[name]
                    assert not bf.is_hidden, \
                        "Hidden fields don't support layout. Field name '%s'." % name
                    sub_rows.append(self._render_field(bf, sub_row, help_text_html))
                    rendered_names.append(name)
                rendered_column = '\n'.join(sub_rows)
                if rendered_column:
                    rendered = '<div class="%s%s">%s</div>' % (
                        self.row_css_class_prefix, column_width, rendered_column)
                    rendered_rows.append(rendered)
            output.append(full_row % '\n'.join(rendered_rows))

        for name, field in self.fields.items():
            if name in rendered_names:
                continue
            bf = self[name]
            # Escape and cache in local variable.
            bf_errors = self.error_class([conditional_escape(error) for error in bf.errors])
            if bf.is_hidden:
                if bf_errors:
                    top_errors.extend([_('(Hidden field %(name)s) %(error)s') % 
                                       {'name': name, 'error': force_text(e)}
                                       for e in bf_errors])
                hidden_fields.append(six.text_type(bf))
            else:
                output.append(self._render_field(
                    bf, sub_row, help_text_html, bf_errors=bf_errors))

        if top_errors:
            output.insert(0, error_row % force_text(top_errors))

        if hidden_fields:  # Insert any hidden fields in the last row.
            output.append(''.join(hidden_fields))
        return mark_safe('\n'.join(output))


    def as_bootstrap(self):
        return self._bootstrap_html_output(
            full_row='<div class="row">%s</div>',
            sub_row='<div%(html_class_attr)s>' 
                    '%(label)s%(field)s%(help_text)s%(errors)s</div>',
            error_row='<div class="alert alert-danger">%s</div>',
            help_text_html='<span class="help-block">%s</span>'
        )




class Form(FormMixin, forms.Form):

    def __init__(self, **kwargs):
        error_class = kwargs.pop('error_class', None) or DivErrorList
        kwargs['error_class'] = error_class
        super(Form, self).__init__(**kwargs)
            

class ModelForm(FormMixin, forms.ModelForm):
    def __init__(self, **kwargs):
        error_class = kwargs.pop('error_class', None) or DivErrorList
        kwargs['error_class'] = error_class
        super(ModelForm, self).__init__(**kwargs)
