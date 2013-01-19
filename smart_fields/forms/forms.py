from django import forms
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.conf import settings

from smart_fields import settings

import json

__all__ = (
    "PluploadModelForm",
)

class PluploadModelForm(forms.ModelForm):
    form_template = 'smart_fields/plupload_queue_form.html'
    file_elem_template = '<li id="%(file_id)s" class="plupload_delete"><div class="plupload_file_name"><span data-href="%(url)s" class="plupload_file_link" style="cursor:pointer;">%(filename)s</a></div><div class="plupload_file_action"><a style="display:block;" data-pk=%(pk)s title="Remove File" href="#"></a></div><div class="plupload_file_status">Uploaded</div><div class="plupload_file_size">%(filesize)s</div><div class="plupload_clearer">&nbsp;</div></li>'

    def __init__(self, queryset=None, upload_url=None, *args, **kwargs):
        super(PluploadModelForm, self).__init__(*args, **kwargs)
        self.queryset = queryset
        self.upload_url = upload_url
        opts = self._meta
        fields_error = "%s has to have at least one field specified inside the Meta class. Namely FileField or any other that inherit from it. At most two fields, second being a CharField named 'name'." % self.__class__.__name__
        if len(opts.fields) == 0 or len(opts.fields) > 2:
            raise ValueError(fields_error)
        if len(opts.fields) == 2 and opts.fields[1] != 'name':
            raise ValueError(fields_error)
        self.file_field_name = opts.fields[0]

    @property
    def field_file(self):
        return self.instance._smart_field(self.file_field_name)
    
    def _get_plupload_settings(self):
        plupload_settings = {}
        field_settings = self.instance.smart_fields_settings.get(
            self.file_field_name)
        upload_url = self.upload_url
        field_file = self.field_file
        if upload_url is None:
            if hasattr(field_file.field, 'upload_url') and \
                callable(field_file.field.upload_url):
                try:
                    upload_url = field_file.field.upload_url(self.instance)
                except NotImplementedError:
                    upload_url = ''
            else:
                upload_url = ''
        if settings.PLUPLOAD_SETTINGS:
            plupload_settings.update(settings.PLUPLOAD_SETTINGS)
        if field_settings:
            plupload_settings.update(field_settings.get('plupload_settings', {}))
        form_name = self.__class__.__name__.lower()
        plupload_settings.update({
	    'browse_button': "%s_browse_btn" % self.file_field_name,
	    'container': "%s_plupload" % form_name,
	    'file_data_name': self.file_field_name,
            'rename': len(self._meta.fields) == 2,
            'url': upload_url
            })
        return mark_safe(json.dumps(plupload_settings))

    @classmethod
    def get_file_elem_id(cls, field_name, pk):
        return "%s_%s_%s" % (cls.__name__.lower(), field_name, pk)
    
    def get_file_elem_rendered(self, instance):
        field_file = instance._smart_field(self.file_field_name)
        filename = instance.name if len(self._meta.fields) == 2 else \
            os.path.basename(field_file.name)
        field_elem_id = self.get_file_elem_id(self.file_field_name, instance.pk)
        subs = {
            'pk': instance.pk,
            'url': field_file.url,
            'file_id': field_elem_id,
            'filename': filename,
            'filesize': field_file.size
            }
        return [field_elem_id, field_file.size, 
                mark_safe(self.file_elem_template % subs)]

    def as_plupload(self):
        model = self._meta.model
        form_name = self.__class__.__name__.lower()
        initial_file_elems = []
        if self.queryset:
            for elem in self.queryset:
                file_elem_id = self.get_file_elem_id(self.file_field_name, elem.pk)
                initial_file_elems.append(self.get_file_elem_rendered(elem))
        context = {
            'field_name': self.file_field_name,
            'form_name': form_name,
            'plupload_settings': self._get_plupload_settings(),
            'initial_file_elems': mark_safe(json.dumps(initial_file_elems))
            }
        return mark_safe(
            render_to_string(self.form_template, context))

    class Media:
        css = settings.PLUPLOAD_QUEUE_CSS
        js = settings.PLUPLOAD_JS + settings.PLUPLOAD_QUEUE_JS

