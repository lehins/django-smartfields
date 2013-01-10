from django import forms
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape, format_html
from django.utils.translation import ugettext_lazy
from django.utils.encoding import force_text
from django.forms.util import flatatt
from django.conf import settings

import os, json

__all__ = (
    "ButtonInput", "PluploadFileInput", "PluploadImageFileInput",
)

PLUPLOAD_SETTINGS = getattr(settings, 'PLUPLOAD_SETTINGS', {})

PLUPLOAD_JS = tuple([os.path.join('js/plupload/', x) for x in [
            'plupload.js', 'plupload.gears.js', 'plupload.silverlight.js', 
            'plupload.flash.js', 'plupload.browserplus.js', 'plupload.html4.js', 
            'plupload.html5.js']])

class ButtonInput(forms.widgets.Input):
    input_type = 'submit'

class PluploadFileInput(forms.ClearableFileInput):
    media_type = "file"
    browse_input = ButtonInput()
    browse_input_text = ugettext_lazy('Browse')
    upload_input = ButtonInput()
    upload_input_text = ugettext_lazy('Upload')
    clear_input = forms.CheckboxInput()
    clear_checkbox_label = ugettext_lazy('Delete')
    no_initial_text = ugettext_lazy('No file has been uploaded')
    container_template = '<div %(attrs)s><div id="%(name)s_initial">%(initial)s</div> %(file_container)s %(browse)s %(upload)s</div>%(script)s'
    initial_template = '<a href="%(url)s" target="_blank">%(initial_content)s</a><br/>%(clear)s'
    clear_template = '<label for="%(clear_checkbox_id)s">%(clear_checkbox)s %(clear_checkbox_label)s</label>'

    plupload_settings = {
        'runtimes': 'gears,html5,flash,silverlight,browserplus',
        'multi_selection': False,
        'max_file_size': "10mb",
        'flash_swf_url': static("js/plupload/plupload.flash.swf"),
        'silverlight_xap_url': static("js/plupload/plupload.silverlight.xap")
        }
    plupload_filters = {
        'file': [],
        'image': [{'title': "Image files", 'extensions': "jpg,gif,png"},],
        'audio': [],
        'video': [],
        }

    def get_plupload_settings(self, name, value):
        plupload_settings = {}
        if PLUPLOAD_SETTINGS:
            plupload_settings.update(PLUPLOAD_SETTINGS)
        if self.plupload_settings:
            plupload_settings.update(self.plupload_settings)
        filters = self.plupload_filters.get(self.media_type, None)
        if filters:
            plupload_settings.update({'filters': filters})
        plupload_settings.update({
	    'browse_button': "%s_browse_btn" % name,
	    'container': "%s_container" % name,
	    'file_data_name': name,
            })
        return plupload_settings
    
    def render_clear(self, name, value):
        if not value:
            return ''
        checkbox_name = conditional_escape(self.clear_checkbox_name(name))
        checkbox_id = conditional_escape(self.clear_checkbox_id(checkbox_name))
        substitutions = {
            'clear_checkbox': self.clear_input.render(
                checkbox_name, False, attrs={'id': checkbox_id}),
            'clear_checkbox_id': checkbox_id,
            'clear_checkbox_label': self.clear_checkbox_label
            }
        return self.clear_template % substitutions

    def render_initial_content(self, value):
        return force_text(os.path.basename(value.url))

    def render_initial(self, name, value):
        if not (value and value.url):
            return self.no_initial_text
        substitutions = {
            'url': value.url,
            'initial_content': self.render_initial_content(value),
            'clear': self.render_clear(name, value)
            }
        return mark_safe(self.initial_template % substitutions)
    
    def render_script(self, name, value):
        template = "multimedia/plupload_script.html"
        plupload_settings = self.get_plupload_settings(name, value)
        context = {
            'name': name,
            'no_initial_text': self.no_initial_text,
            'plupload_settings': mark_safe(json.dumps(plupload_settings))
            }
        return mark_safe(render_to_string(template, context))
                   
    def render_browse_btn(self, name):
        return ButtonInput().render(
            "%s_browse_btn" % name, self.browse_input_text, attrs={
                'id': "%s_browse_btn" % name})

    def render_upload_btn(self, name):
        return ButtonInput().render(
            "%s_upload_btn" % name, self.upload_input_text, attrs={
                'id': "%s_upload_btn" % name})

    def render(self, name, value, attrs=None):
        substitutions = {
            'attrs': flatatt(self.build_attrs(attrs)),
            'initial': conditional_escape(self.render_initial(name, value)),
            'file_container': '<div id="%s_container"></div>' % name,
            'browse': self.render_browse_btn(name),
            'upload': self.render_upload_btn(name),
            'script': self.render_script(name, value),
            'name': name
            }
        return mark_safe(self.container_template % substitutions)
        
    class Media:
        js = PLUPLOAD_JS


class PluploadImageFileInput(PluploadFileInput):
    media_type = 'image'
    plupload_filters = {
        'image': [{'title': "Image files", 
                   'extensions': "jpg,jpeg,tiff,gif,png"},],
        }

    def render_initial_content(self, value):
        return format_html(
            '<img src="{0}" style="max-width:320px;max-height:200px;"/>', value.url)

