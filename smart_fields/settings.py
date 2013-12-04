from django.templatetags.static import static
from django.conf import settings

import os

KEEP_ORPHANS = getattr(settings, 'SMARTFIELDS_KEEP_ORPHANS', False)

PLUPLOAD_SETTINGS = getattr(settings, 'SMARTFIELDS_PLUPLOAD_SETTINGS', {
        'runtimes': 'gears,html5,flash,silverlight,browserplus',
        'multi_selection': False,
        'max_file_size': "20mb",
        'flash_swf_url': static("plupload/plupload.flash.swf"),
        'silverlight_xap_url': static("plupload/plupload.silverlight.xap"),
        'filters': [],
        })


PLUPLOAD_JS = getattr(settings, 'SMARTFIELDS_PLUPLOAD_JS', 
                      tuple([os.path.join('plupload/js/', x) for x in [
                'plupload.js', 'plupload.gears.js', 'plupload.silverlight.js', 
                'plupload.flash.js', 'plupload.browserplus.js', 'plupload.html4.js', 
                'plupload.html5.js']]))

PLUPLOAD_QUEUE_JS = getattr(settings, 'SMARTFIELDS_PLUPLOAD_QUEUE_JS', (
        'plupload/js/jquery.plupload.queue/jquery.plupload.queue.js',))

PLUPLOAD_QUEUE_CSS = getattr(settings, 'SMARTFIELDS_PLUPLOAD_QUEUE_CSS', {
        'all': ('plupload/js/jquery.plupload.queue/css/jquery.plupload.queue.css',)})

VIDEO_TAG = getattr(settings, 'SMARTFIELDS_VIDEO_TAG', {
        'form_template': '<video id="video_%(name)s" class="video-js vjs-default-skin" controls="controls" preload="auto" width="320" height="240" data-setup="{}">%(sources)s</video>',
        'instance_template': '<video id="video_%(name)s" class="video-js vjs-default-skin" controls="controls" preload="auto" width="700" height="400" data-setup="{}">%(sources)s</video>',
        'js': ("https://vjs.zencdn.net/c/video.js",),
        'css': {'all': ("https://vjs.zencdn.net/c/video-js.css",)},
        })

VIDEO_TAG_USE_SSL = getattr(settings, 'SMARTFIELDS_VIDEO_TAG_USE_SSL', False)

VIDEO_TAG_DOMAIN = getattr(settings, 'SMARTFIELDS_VIDEO_TAG_DOMAIN', None)

DEFAULT_VIDEO_PROFILES = getattr(settings, 'SMARTFIELDS_DEFAULT_VIDEO_PROFILES', {
    'mp4': {
        'format': 'mp4',
        'cmd': "%(converter)s -i %(input)s -y -codec:v %(vcodec)s " \
            "-vprofile %(vprofile)s -preset %(preset)s -b:v %(vbitrate)s " \
            "-maxrate %(maxrate)s -bufsize %(bufsize)s " \
            #"-vf scale=%(width)s:%(height)s " \
            "-threads %(threads)s -codec:a %(acodec)s -b:a %(abitrate)s %(output)s",
        'converter': 'avconv',
        'vcodec': 'libx264',
        'vprofile': 'main',
        'preset': 'medium',
        'vbitrate': '600k',
        'maxrate': '600k',
        'bufsize': '600k',
        'width': -1,
        'height': 360,
        'threads': 0,
        'acodec': 'libvo_aacenc',
        'abitrate': '96k'
        },
    'webm': {
        'format': 'webm',
        'cmd': "%(converter)s -i %(input)s -y -codec:v %(vcodec)s " \
            "-b:v %(vbitrate)s -qmin 10 -qmax 42 " \
            "-maxrate %(maxrate)s -bufsize %(bufsize)s " \
            "-vf scale=%(width)s:%(height)s " \
            "-threads %(threads)s -codec:a %(acodec)s -b:a %(abitrate)s %(output)s",
        'converter': 'avconv',
        'vcodec': 'libvpx',
        'vbitrate': '300k',
        'maxrate': '300k',
        'bufsize': '600k',
        'width': -1,
        'height': 360,
        'threads': 4,
        'acodec': 'libvorbis',
        'abitrate': '96k'
        }
    })

INSTALLED_APPS = getattr(settings, 'INSTALLED_APPS', ())
