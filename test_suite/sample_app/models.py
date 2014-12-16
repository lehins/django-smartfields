# coding=utf-8
import smartfields

from django.db import models
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.utils.text import slugify

from smartfields import processors, Dependency, FileDependency
from smartfields.managers import VALUE_NOT_SET
from smartfields.utils import UploadTo


def _slugify(v, **kwargs): return slugify(v)

def _to_tile_underscores(v, **kwargs): return v.title().replace(" ", "_")

class ProcessorTestingModel(models.Model):

    field_1 = smartfields.CharField(max_length=15, dependencies=[
        # testing forward dependency
        Dependency(attname='field_2', processor=_slugify),
        # testing self dependency
        Dependency(processor=_to_tile_underscores)
    ])
    # testing with no direct dependencies
    field_2 = smartfields.SlugField(max_length=15)
    field_3 = smartfields.SlugField(max_length=15, unique=True, dependencies=[
        # testing regular dependency and SlugProcessor
        Dependency('field_1', processor=processors.SlugProcessor())
    ])
    field_4 = smartfields.SlugField(max_length=15, unique=True, dependencies=[
        # testing default dependency
        Dependency('field_1', default=processors.SlugProcessor())
    ])

def _file_to_lower(f, **kwargs): return ContentFile(f.read().lower())

class FilesTestingModel(models.Model):
    # test static
    field_1 = smartfields.FileField(dependencies=[
        FileDependency(default='defaults/foo.txt')
    ])
    field_2 = smartfields.FileField(dependencies=[
        FileDependency(suffix='foo', default='defaults/foo.txt'),
        FileDependency(attname='bar', default='defaults/bar.txt',
                       processor=_file_to_lower)
    ])

class ImageTestingModel(models.Model):
    image_1 = models.ImageField(
        upload_to='image_1', width_field='image_1_width', height_field='image_1_height')
    image_1_width = models.IntegerField(null=True)
    image_1_height = models.IntegerField(null=True)
    image_2 = smartfields.ImageField(
        upload_to='image_2', width_field='image_2_width', height_field='image_2_height')
    image_2_width = models.IntegerField(null=True)
    image_2_height = models.IntegerField(null=True)
    image_3 = smartfields.ImageField(upload_to=UploadTo(name='image_3'), dependencies=[
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
    image_4 = smartfields.ImageField(upload_to=UploadTo(name='image_4'), dependencies=[
        FileDependency(suffix='jpeg2000', 
                       processor=processors.ImageProcessor(format='JPEG2000')),
    ])


class DependencyTestingModel(models.Model):
    # test automatic palette conversion
    image_1 = smartfields.ImageField(upload_to=UploadTo(name='image_1'), dependencies=[
        # convert self to palette mode, and than to a different pallete mode
        FileDependency(processor=processors.ImageProcessor(
            format=processors.ImageFormat('BMP', mode='P'), scale={'width':50})),
        FileDependency(suffix='gif', processor=processors.ImageProcessor(
            format=processors.ImageFormat('GIF', mode='P')))
    ])
    image_2 = smartfields.ImageField(upload_to=UploadTo(name='image_2'), dependencies=[
        # testing setting a dependency on another FileField
        FileDependency(attname='image_3', processor=processors.ImageProcessor(
            format=processors.ImageFormat('PNG'), scale={'width':100})),
        FileDependency(attname='image_4', processor=processors.ImageProcessor(
            format=processors.ImageFormat('PNG'), scale={'width':150})),
    ])
    # TODO: make sure regular ImageField doesn't get it's first file removed
    image_3 = models.ImageField(upload_to=UploadTo(name='image_3'))
    image_4 = smartfields.ImageField(upload_to=UploadTo(name='image_4'))
    

def test_handler(value, instance, field, field_value, event):
    setattr(instance, "%s_event" % event[0], 
            "%s_%s.%s=%s" % (event[0], event[1], field.name, value))
    if value is VALUE_NOT_SET:
        return
    value+= 1
    setattr(instance, field.name, value)
    
def pre_init_handler(*args, **kwargs):
    return test_handler(*args, event=('pre', 'init'))

def post_init_handler(*args, **kwargs):
    return test_handler(*args, event=('post', 'init'))

def pre_save_handler(*args, **kwargs):
    return test_handler(*args, event=('pre', 'save'))

def post_save_handler(*args, **kwargs):
    return test_handler(*args, event=('post', 'save'))

def pre_delete_handler(*args, **kwargs):
    return test_handler(*args, event=('pre', 'delete'))

def post_delete_handler(*args, **kwargs):
    return test_handler(*args, event=('post', 'delete'))


class HandlersTestingModel(models.Model):
    pre_event = None
    post_event = None

    field_1 = smartfields.IntegerField(null=True, dependencies=[
        Dependency(pre_init=pre_init_handler,
                   post_init=post_init_handler,
                   pre_save=pre_save_handler,
                   post_save=post_save_handler,
                   pre_delete=pre_delete_handler,
                   post_delete=post_delete_handler)
    ])

    def save(self):
        self.field_1 = 117
        super(HandlersTestingModel, self).save()

    def delete(self):
        self.field_1 = 217
        super(HandlersTestingModel, self).delete()

        
class InstanceHandlersTestingModel(models.Model):
    pre_event = None
    post_event = None

    field_1 = smartfields.IntegerField(null=True, dependencies=[
        Dependency(pre_init='pre_init',
                   post_init='post_init',
                   pre_save='pre_save',
                   post_save='post_save',
                   pre_delete='pre_delete',
                   post_delete='post_delete')
    ])

    def pre_init(self, value, *args, **kwargs):
        return test_handler(value, self, *args, event=('pre', 'init'))

    def post_init(self, value, *args, **kwargs):
        return test_handler(value*10, self, *args, event=('post', 'init'))

    def pre_save(self, value, *args, **kwargs):
        return test_handler(value*10, self, *args, event=('pre', 'save'))

    def post_save(self, value, *args, **kwargs):
        return test_handler(value*10, self, *args, event=('post', 'save'))

    def pre_delete(self, value, *args, **kwargs):
        return test_handler(value*10, self, *args, event=('pre', 'delete'))

    def post_delete(self, value, *args, **kwargs):
        return test_handler(value*10, self, *args, event=('post', 'delete'))


class VideoTestingModel(models.Model):
    
    video_1 = smartfields.FileField(
        upload_to=UploadTo(name='video_1'), dependencies=[
            # example of conversion to webm
            FileDependency(suffix='webm', async=True, processor=processors.FFMPEGProcessor(
                format='webm', vcodec='libvpx', vbitrate='128k', maxrate='128k',
                bufsize='256k', width='trunc(oh*a/2)*2', height=240,
                threads=4, acodec='libvorbis', abitrate='96k')),
            FileDependency(suffix='mp4', async=True, processor=processors.FFMPEGProcessor(
                format='mp4', vcodec='libx264', vbitrate='128k',
                maxrate='128k', bufsize='256k', width='trunc(oh*a/2)*2',
                height=240, threads=0, acodec='libfdk_aac', abitrate='96k'))
        ])