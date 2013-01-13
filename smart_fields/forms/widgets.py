from django import forms
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape, format_html
from django.utils.translation import ugettext_lazy
from django.utils.encoding import force_text
from django.forms.util import flatatt
from django.contrib.sites.models import Site
from django.conf import settings

import os, json

__all__ = (
    "ButtonInput", "PluploadFileInput", "PluploadImageInput", "PluploadVideoInput",
)

PLUPLOAD_SETTINGS = getattr(settings, 'SMARTFIELDS_PLUPLOAD_SETTINGS', {})

PLUPLOAD_JS = getattr(settings, 'SMARTFIELDS_PLUPLOAD_JS', 
                      tuple([os.path.join('js/plupload/', x) for x in [
                'plupload.js', 'plupload.gears.js', 'plupload.silverlight.js', 
                'plupload.flash.js', 'plupload.browserplus.js', 'plupload.html4.js', 
                'plupload.html5.js']]))

PLUPLOAD_FLASH = getattr(settings, 'SMARTFIELDS_PLUPLOAD_FLASH', 
                         static("js/plupload/plupload.flash.swf"))
PLUPLOAD_SILVERLIGHT = getattr(settings, 'SMARTFIELDS_PLUPLOAD_SILVERLIGHT', 
                               static("js/plupload/plupload.silverlight.xap"))

USE_SSL = getattr(settings, 'SMARTFIELDS_VIDEOFIELD_USE_SSL', False)

DOMAIN = getattr(settings, 'SMARTFIELDS_DOMAIN', None)

INSTALLED_APPS = getattr(settings, 'INSTALLED_APPS')

VIDEO_TAG = getattr(settings, 'SMARTFIELDS_VIDEO_FORM_TAG', '<video id="video_%(name)s" class="video-js vjs-default-skin" controls="controls" preload="auto" width="320" height="240" data-setup="{}">%(sources)s</video>')

class ButtonInput(forms.widgets.Input):
    input_type = 'submit'

class PluploadFileInput(forms.ClearableFileInput):
    browse_input = ButtonInput()
    browse_input_text = ugettext_lazy('Browse')
    upload_input = ButtonInput()
    upload_input_text = ugettext_lazy('Upload')
    clear_input = forms.CheckboxInput()
    clear_checkbox_label = ugettext_lazy('Delete')
    no_initial_text = ugettext_lazy('No file has been uploaded')
    script_template = "smart_fields/plupload_script.html"
    container_template = '<div %(attrs)s><div id="%(name)s_initial">%(initial)s</div> %(file_container)s <p>%(browse)s %(upload)s</p></div>%(script)s'
    initial_template = '%(clear)s<p><a href="%(url)s" target="_blank">%(initial_content)s</a></p>'
    clear_template = '<label for="%(clear_checkbox_id)s">%(clear_checkbox)s %(clear_checkbox_label)s</label>'

    plupload_settings = {
        'runtimes': 'gears,html5,flash,silverlight,browserplus',
        'multi_selection': False,
        'max_file_size': "20mb",
        'flash_swf_url': PLUPLOAD_FLASH,
        'silverlight_xap_url': PLUPLOAD_SILVERLIGHT
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
        filters = self.plupload_filters.get(value.field.media_type, None)
        if filters:
            plupload_settings.update({'filters': filters})
        plupload_settings.update({
	    'browse_button': "%s_browse_btn" % name,
	    'container': "%s_container" % name,
	    'file_data_name': name,
            'rename': True,
            'url': value.field.upload_url(value.instance)
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
        plupload_settings = self.get_plupload_settings(name, value)
        context = {
            'name': name,
            'no_initial_text': self.no_initial_text,
            'plupload_settings': mark_safe(json.dumps(plupload_settings))
            }
        return mark_safe(render_to_string(self.script_template, context))
                   
    def render_browse_btn(self, name):
        return self.browse_input.render(
            "%s_browse_btn" % name, self.browse_input_text, attrs={
                'id': "%s_browse_btn" % name})

    def render_upload_btn(self, name):
        return self.upload_input.render(
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


class PluploadImageInput(PluploadFileInput):
    plupload_filters = {
        'image': [{'title': "Image files", 
                   'extensions': "jpg,jpeg,tiff,gif,png"},],
        }

    def render_initial_content(self, value):
        return format_html(
            '<img src="{0}" style="max-width:320px;max-height:200px;"/>', value.url)

class PluploadVideoInput(PluploadFileInput):
    initial_template = '%(clear)s<p>%(initial_content)s</p>'

    def _get_full_url(self, url, use_ssl=None):
        if DOMAIN is None and 'django.contrib.sites' not in INSTALLED_APPS:
            return url
        domain = DOMAIN or Site.objects.get_current().domain
        if use_ssl is None:
            use_ssl = USE_SSL
        protocol = 'https://' if use_ssl else 'http://'
        return protocol + domain + url

    def render_initial_content(self, value, video_tag=None):
        content_template = video_tag
        if content_template is None:
            content_template = VIDEO_TAG
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
        css = {'all': ("https://vjs.zencdn.net/c/video-js.css",)}
        js = ("https://vjs.zencdn.net/c/video.js",)
