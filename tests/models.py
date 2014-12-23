from django.db import models
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.utils.text import slugify

from smartfields import fields, processors
from smartfields.dependencies import Dependency, FileDependency
from smartfields.utils import UploadTo, VALUE_NOT_SET


def _test_handler(value, instance, field, event):
    setattr(instance, "%s_event" % event[0], 
            "%s_%s.%s=%s" % (event[0], event[1], field.name, value))
    if value is VALUE_NOT_SET:
        return
    value+= 1
    setattr(instance, field.name, value)
    
def pre_init_handler(*args, **kwargs):
    return _test_handler(*args, event=('pre', 'init'))

def post_init_handler(*args, **kwargs):
    return _test_handler(*args, event=('post', 'init'))

def pre_save_handler(*args, **kwargs):
    return _test_handler(*args, event=('pre', 'save'))

def post_save_handler(*args, **kwargs):
    return _test_handler(*args, event=('post', 'save'))

def pre_delete_handler(*args, **kwargs):
    return _test_handler(*args, event=('pre', 'delete'))

def post_delete_handler(*args, **kwargs):
    return _test_handler(*args, event=('post', 'delete'))


class HandlingTesting(models.Model):
    pre_event = None
    post_event = None

    field_1 = fields.IntegerField(null=True, dependencies=[
        Dependency(pre_init=pre_init_handler,
                   post_init=post_init_handler,
                   pre_save=pre_save_handler,
                   post_save=post_save_handler,
                   pre_delete=pre_delete_handler,
                   post_delete=post_delete_handler)
    ])

    def save(self):
        self.field_1 = 117
        super(HandlingTesting, self).save()

    def delete(self):
        self.field_1 = 217
        super(HandlingTesting, self).delete()


class InstanceHandlingTesting(models.Model):
    pre_event = None
    post_event = None

    field_1 = fields.IntegerField(null=True, dependencies=[
        Dependency(pre_init='pre_init',
                   post_init='post_init',
                   pre_save='pre_save',
                   post_save='post_save',
                   pre_delete='pre_delete',
                   post_delete='post_delete')
    ])

    def pre_init(self, value, *args, **kwargs):
        return _test_handler(value, self, *args, event=('pre', 'init'))

    def post_init(self, value, *args, **kwargs):
        return _test_handler(value*10, self, *args, event=('post', 'init'))

    def pre_save(self, value, *args, **kwargs):
        return _test_handler(value*10, self, *args, event=('pre', 'save'))

    def post_save(self, value, *args, **kwargs):
        return _test_handler(value*10, self, *args, event=('post', 'save'))

    def pre_delete(self, value, *args, **kwargs):
        return _test_handler(value*10, self, *args, event=('pre', 'delete'))

    def post_delete(self, value, *args, **kwargs):
        return _test_handler(value*10, self, *args, event=('post', 'delete'))


# TEXT PROCESSING TESTING

def _title_getter(value, instance, **kwargs):
    return instance.title


class TextTesting(models.Model):
    
    title = fields.CharField(max_length=11, unique=True, dependencies=[
        Dependency(processor=processors.UniqueProcessor())
    ])
    slug = fields.SlugField(max_length=9, unique=True, dependencies=[
        Dependency(default=_title_getter, processor=processors.SlugProcessor())
    ])
    summary = fields.TextField(dependencies=[
        Dependency(suffix='plain', processor=processors.HTMLProcessor())
    ])
    summary_plain = fields.TextField(dependencies=[
        Dependency(attname='summary_beginning', processor=processors.CropProcessor())
    ])
    summary_beginning = models.CharField(max_length=100)


# FILE TESTING


def _id(value, **kwargs):
    return value

def _get_foo(value, instance, field, **kwargs):
    return instance.field_1_foo

def _file_to_lower(f, **kwargs): 
    pos = f.tell()
    f.seek(0)
    new_f = ContentFile(f.read().lower())
    f.seek(pos)
    return new_f


class FileTesting(models.Model):
    # test static default
    field_1 = fields.FileField(dependencies=[
        FileDependency(suffix='foo', default="defaults/foo.txt", processor=_id),
        FileDependency(attname='bar', default="defaults/bar.txt")
    ])
    # test default FieldFile
    field_2 = fields.FileField(dependencies=[
        FileDependency(default=_get_foo, processor=_file_to_lower)
    ])
    # test cleanup without dependencies
    field_3 = fields.FileField()
    # test no cleanup
    field_4 = fields.FileField(keep_orphans=True)



class ImageTesting(models.Model):
    image_1 = models.ImageField(
        upload_to='image_1', width_field='image_1_width', height_field='image_1_height')
    image_1_width = models.IntegerField(null=True)
    image_1_height = models.IntegerField(null=True)
    image_2 = fields.ImageField(
        upload_to='image_2', width_field='image_2_width', height_field='image_2_height')
    image_2_width = models.IntegerField(null=True)
    image_2_height = models.IntegerField(null=True)
    image_3 = fields.ImageField(upload_to=UploadTo(name='image_3'), dependencies=[
        FileDependency(suffix='png', processor=processors.ImageProcessor(
            format=processors.ImageFormat('PNG', mode='P'), 
            scale={'max_width': 200, 'max_height':150})),
        FileDependency(suffix='bmp', processor=processors.ImageProcessor(
            format='BMP', scale={'width': 50})),
        FileDependency(suffix='eps', processor=processors.ImageProcessor(
            format='EPS', scale={'width': 50})),
        FileDependency(suffix='gif', processor=processors.ImageProcessor(
            format='GIF', scale={'width': 50})),
        FileDependency(suffix='im', processor=processors.ImageProcessor(
            format='IM', scale={'width': 50})),
        FileDependency(suffix='jpeg', processor=processors.ImageProcessor(
            format=processors.ImageFormat('JPEG', save_kwargs={'quality':95}),
            scale={'width': 50})),
        FileDependency(suffix='msp', processor=processors.ImageProcessor(
            format='MSP', scale={'width': 50})),
        FileDependency(suffix='pcx', processor=processors.ImageProcessor(
            format='PCX', scale={'width': 50})),
        FileDependency(suffix='ppm', processor=processors.ImageProcessor(
            format='PPM', scale={'width': 50})),
        FileDependency(suffix='tiff', processor=processors.ImageProcessor(
            format=processors.ImageFormat('TIFF', mode='P'))),
        FileDependency(suffix='resized', processor=processors.ImageProcessor(
            scale={'width': 50})),

    ])
    # test problematic format
    image_4 = fields.ImageField(upload_to=UploadTo(name='image_4'), dependencies=[
        FileDependency(suffix='jpeg2000', 
                       processor=processors.ImageProcessor(format='JPEG2000')),
    ])


class DependencyTesting(models.Model):
    # test automatic palette conversion
    image_1 = fields.ImageField(upload_to=UploadTo(name='image_1'), dependencies=[
        # convert self to palette mode, and than to a different pallete mode
        FileDependency(processor=processors.ImageProcessor(
            format=processors.ImageFormat('BMP', mode='P'), scale={'width':50})),
        FileDependency(suffix='gif', processor=processors.ImageProcessor(
            format=processors.ImageFormat('GIF', mode='P')))
    ])
    image_2 = fields.ImageField(upload_to=UploadTo(name='image_2'), dependencies=[
        # testing setting a dependency on another FileField
        FileDependency(attname='image_3', processor=processors.ImageProcessor(
            format=processors.ImageFormat('PNG'), scale={'width':100})),
        FileDependency(attname='image_4', processor=processors.ImageProcessor(
            format=processors.ImageFormat('PNG'), scale={'width':150})),
    ])
    image_3 = models.ImageField(upload_to=UploadTo(name='image_3'))
    image_4 = fields.ImageField(upload_to=UploadTo(name='image_4'))
    

        


video_tag_processor = processors.HTMLTagProcessor(template=
    '<video id="video_{field.name}" controls="controls" preload="auto" width="320" height="240">'
    '<source type="video/webm" src="{base_url}{instance.video_1_webm.url}"/>'
    '<source type="video/mp4" src="{base_url}{instance.video_1_mp4.url}"/></video>')


class VideoTesting(models.Model):
    
    video_1 = fields.FileField(
        upload_to=UploadTo(name='video_1'), dependencies=[
            # testing html tag setter
            Dependency(suffix='html_tag', default=video_tag_processor),
            # testing conversion to webm
            FileDependency(suffix='webm', async=True, processor=processors.FFMPEGProcessor(
                format='webm', vcodec='libvpx', vbitrate='128k', maxrate='128k',
                bufsize='256k', width='trunc(oh*a/2)*2', height=240,
                threads=4, acodec='libvorbis', abitrate='96k')),
            # testing conversion to mp4
            FileDependency(suffix='mp4', async=True, processor=processors.FFMPEGProcessor(
                format='mp4', vcodec='libx264', vbitrate='128k',
                maxrate='128k', bufsize='256k', width='trunc(oh*a/2)*2',
                height=240, threads=0, acodec='libfdk_aac', abitrate='96k')),
        ])

    def has_upload_permission(self, user, field_name=None):
        return (field_name == 'video_1' and 
                user.is_authenticated() and 
                user.username == 'test_user')


