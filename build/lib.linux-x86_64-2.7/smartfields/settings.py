from django.templatetags.static import static
from django.conf import settings


KEEP_ORPHANS = getattr(settings, 'SMARTFIELDS_KEEP_ORPHANS', False)

PLUPLOAD_URL = getattr(settings, 'SMARTFIELDS_PLUPLOAD_URL', static('plupload'))

PLUPLOAD_OPTIONS = getattr(settings, 'SMARTFIELDS_PLUPLOAD_OPTIONS', {
    'runtimes': 'html5,flash,silverlight,html4',
    'multi_selection': False,
    'flash_swf_url': "%s/js/Moxie.swf" % PLUPLOAD_URL,
    'silverlight_xap_url': "%s/js/Moxie.xap" % PLUPLOAD_URL,
})
