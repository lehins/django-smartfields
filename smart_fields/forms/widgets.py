from django import forms
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape, format_html
from django.utils.translation import ugettext_lazy
from django.utils.encoding import force_text
from django.forms.util import flatatt
from django.contrib.sites.models import Site

from smart_fields import settings

import os, json

__all__ = (
    "ButtonInput", "PluploadFileInput", "PluploadImageInput", "PluploadVideoInput",
)

class ButtonInput(forms.widgets.Input):
    input_type = 'submit'

class PluploadFileInput(forms.ClearableFileInput):
    browse_input = ButtonInput()
    browse_input_text = ugettext_lazy('Browse')
    upload_input = ButtonInput()
    upload_input_text = ugettext_lazy('Upload')
    clear_input = ButtonInput()
    clear_input_text = ugettext_lazy('Delete')
    no_initial_text = u"No file has been uploaded"
    script_template = '$(function(){var name="%(name)s";var remove_btn_id="%(remove_btn_id)s";var settings=%(plupload_settings)s;settings[\'multipart_params\']={\'csrfmiddlewaretoken\': $("input[name=\'csrfmiddlewaretoken\']").val()};var uploader=new smartfields.DjangoUploader(name, remove_btn_id, settings);});'

    container_template = '<div%(attrs)s><div id="%(name)s_initial">%(initial)s</div> %(file_container)s <p>%(browse)s %(upload)s %(clear)s</p></div><script type="text/javascript">%(script)s</script>'
    initial_template = '<p><a href="%(url)s" target="_blank">%(initial_content)s</a></p>'
    plupload_filters = []

    def _get_plupload_settings(self, name, value):
        plupload_settings = {'filters': self.plupload_filters}
        if settings.PLUPLOAD_SETTINGS:
            plupload_settings.update(settings.PLUPLOAD_SETTINGS)
        field_settings = value.instance.smart_fields_settings.get(value.field.name)
        plupload_settings.update(field_settings.get('plupload_settings', {}))
        plupload_settings.update({
	    'browse_button': "%s_browse_btn" % name,
	    #'container': "%s_container" % name,
	    'file_data_name': name,
            'url': value.field.upload_url(value.instance)
            })
        return plupload_settings
    
    def render_initial_content(self, value):
        return force_text(os.path.basename(value.url))

    def render_initial(self, name, value):
        if not (value and value.url):
            return self.no_initial_text
        substitutions = {
            'url': value.url,
            'initial_content': self.render_initial_content(value),
            }
        return mark_safe(self.initial_template % substitutions)
    
    def render_script(self, name, value, clear_id):
        plupload_settings = self._get_plupload_settings(name, value)
        context = {
            'name': name,
            'no_initial_text': self.no_initial_text,
            'plupload_settings': mark_safe(json.dumps(plupload_settings)),
            'remove_btn_id': clear_id
            }
        return mark_safe(self.script_template % context)
                   
    def render_browse_btn(self, name):
        return self.browse_input.render(
            "%s_browse_btn" % name, self.browse_input_text, attrs={
                'id': "%s_browse_btn" % name})

    def render_upload_btn(self, name):
        return self.upload_input.render(
            "%s_upload_btn" % name, self.upload_input_text, attrs={
                'id': "%s_upload_btn" % name})

    def render_clear_btn(self, clear_name, clear_id):
        return self.clear_input.render(
            clear_name, self.clear_input_text, attrs={'id': clear_id})

    def render(self, name, value, attrs=None):
        clear_name = conditional_escape(self.clear_checkbox_name(name))
        clear_id = conditional_escape(self.clear_checkbox_id(clear_name))
        substitutions = {
            'attrs': flatatt(self.build_attrs(attrs)),
            'initial': conditional_escape(self.render_initial(name, value)),
            'file_container': '<div id="%s_container"></div>' % name,
            'browse': self.render_browse_btn(name),
            'upload': self.render_upload_btn(name),
            'clear': self.render_clear_btn(clear_name, clear_id),
            'script': self.render_script(name, value, clear_id),
            'name': name
            }
        return mark_safe(self.container_template % substitutions)
        
    class Media:
        js = settings.PLUPLOAD_JS  + ("js/smartfields.js",)


class PluploadImageInput(PluploadFileInput):
    plupload_filters = {
        'image': [{'title': "Image files", 
                   'extensions': "jpg,jpeg,tiff,gif,png"},],
        }

    def render_initial_content(self, value):
        return format_html(
            '<img src="{0}" style="max-width:320px;max-height:200px;"/>', value.url)

class PluploadVideoInput(PluploadFileInput):
    initial_template = '<p>%(initial_content)s</p>'

    @classmethod
    def _get_full_url(cls, url, use_ssl=None):
        domain = settings.VIDEO_TAG_DOMAIN
        if domain is None:
            if 'django.contrib.sites' in settings.INSTALLED_APPS:
                domain = Site.objects.get_current().domain
            else:
                return url
        if use_ssl is None:
            use_ssl = settings.VIDEO_TAG_USE_SSL
        protocol = 'https://' if use_ssl else 'http://'
        return protocol + domain + url

    def render_initial_content(self, value, video_tag=None):
        content_template = video_tag
        if content_template is None:
            content_template = settings.VIDEO_TAG.get('form_template', None)
            if content_template is None:
                return super(PluploadVideoInput, self).render_initial_content(value)
        source_template = '<source type="%(media_type)s/%(format)s" src="%(full_url)s"/>'
        fields = value.instance.smart_fields[value.field.name]
        profile = value.instance.smart_fields_settings[value.field.name]['profile']
        sources = []
        for key, field in fields.iteritems():
            if field:
                use_ssl = profile[key].get('use_ssl', None)
                sub = {'media_type': value.field.media_type,
                       'format': profile[key]['format'],
                       'full_url': self._get_full_url(field.url, use_ssl=use_ssl)}
                sources.append(source_template % sub)
        return mark_safe(content_template % {
                'name': value.field.name,
                'sources': ' '.join(sources)})

    class Media:
        css = settings.VIDEO_TAG.get('css', {})
        js = settings.VIDEO_TAG.get('js', ())
