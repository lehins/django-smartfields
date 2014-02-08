from django.forms import forms
from django.utils.html import conditional_escape
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils import six


class BaseForm(forms.BaseForm):
    row_css_class_prefix = "col-md-"
    fields_layout = []
    #fields_layout = [(('title', 'slug'), ('image')), (('description',), None)]

    def _render_field(self, bf, template, bf_errors=None):
        bf_errors = bf_errors or self.error_class(
            [conditional_escape(error) for error in bf.errors])
        extra_classes = "form-group"
        if bf_errors:
            extra_classes+= " has-error"
        css_classes = bf.css_classes(extra_classes)
        html_class_attr = ' class="%s"' % css_classes
        if bf.label:
            label = conditional_escape(force_text(bf.label))
            label = bf.label_tag(label) or ''
        else:
            label = ''
        if field.help_text:
            help_text = help_text_html % force_text(field.help_text)
        else:
            help_text = ''
        if bf.errors:
            error_class = 'has-error'
        else:
            error_class = ''
        return template % {
            'errors': force_text(bf_errors),
            'label': force_text(label),
            'field': six.text_type(bf),
            'help_text': help_text,
            'html_class_attr': html_class_attr,
            'error_class': error_class
        }
    
    def html_output(self, full_row, sub_row, error_row, row_ender, help_text_html):
        top_errors = self.non_field_errors()
        output, hidden_fields = [], []

        rendered_names = []

        for row in self.fields_layout:
            column_width = 12/len(row)
            rendered_rows = []
            for column in row:
                if column is None:
                    rows.append('<div class="%soffset-%s"></div>' % (
                        self.row_css_class_prefix, column_width))
                    continue
                sub_rows = []
                for name in column:
                    field = self.fields[name]
                    bf = self[name]
                    assert not bf.is_hidden, \
                        "Hidden fields don't support layout. Field name '%s'." % name
                    sub_rows.append(self._render_field(bf, sub_row))
                    rendered_names.append(name)
                rendered_colum = '\n'.join(sub_rows)
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
                output.append(self._render_field(bf, sub_row, bf_errors))

        if top_errors:
            output.insert(0, error_row % force_text(top_errors))

        if hidden_fields:  # Insert any hidden fields in the last row.
            output.append(''.join(hidden_fields))
        return mark_safe('\n'.join(output))


    def as_bootstrap(self):
        return self.html_output(
            full_row='<div class="row">%s</div>',
            sub_row='<div%(html_class_attr)s">' 
                    '%(label)s%(field)s%(errors)</div>',
            error_row='<div class="alert alert-danger">%s</div>',
            help_text_html='<span class="help-block">%s</span>'
        )