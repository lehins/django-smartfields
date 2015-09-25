from django.db import models
from django.core.files.base import ContentFile

from decimal import Decimal, InvalidOperation

from smartfields import fields, processors
from smartfields.dependencies import Dependency, FileDependency
from smartfields.utils import UploadTo

# PRE PROCESSING

def _decimal_pre_processor(value):
    try:
        return Decimal(value)
    except (TypeError, InvalidOperation):
        return Decimal('0')

def _incrementer(value):
    try:
        return value+1
    except (TypeError, ValueError): pass
    

class PreProcessorTesting(models.Model):
    
    field_1 = fields.DecimalField(decimal_places=1, max_digits=4, dependencies=[
        Dependency(pre_processor=_decimal_pre_processor, processor=_incrementer),
        Dependency(attname='field_2', pre_processor=int)
    ])
    field_2 = fields.IntegerField(dependencies=[
        Dependency(pre_processor=_incrementer)
    ])
    field_3 = fields.SlugField(dependencies=[
        Dependency(pre_processor=processors.SlugProcessor)
    ])

# TEXT PROCESSING TESTING

def _title_getter(value, instance, **kwargs):
    return instance.title


class ToUpperProcessor(processors.BaseProcessor):

    def process(self, value, **kwargs):
        return value.upper()

    
class LoopbackProcessor(processors.BaseProcessor):

    def process(self, value, **kwargs):
        return kwargs['stashed_value']


class TextTesting(models.Model):
    
    title = fields.CharField(max_length=11, unique=True, dependencies=[
        Dependency(processor=processors.UniqueProcessor())
    ])
    slug = fields.SlugField(max_length=9, unique=True, dependencies=[
        Dependency(default=_title_getter, processor=processors.SlugProcessor)
    ])
    summary = fields.TextField(dependencies=[
        Dependency(suffix='plain', processor=processors.HTMLProcessor())
    ])
    summary_plain = fields.TextField(dependencies=[
        Dependency(attname='summary_beginning', processor=processors.CropProcessor())
    ])
    summary_beginning = fields.CharField(max_length=100)
    loopback = fields.CharField(max_length=10, dependencies=[
        Dependency(suffix='foo', processor=LoopbackProcessor),
        Dependency(processor=LoopbackProcessor)
    ])
    loopback_foo = fields.CharField(max_length=10)
    html = fields.TextField(dependencies=[
        Dependency(processor=ToUpperProcessor),
        Dependency(suffix='plain', processor=processors.HTMLProcessor())
    ])
    html_plain = fields.TextField()

# FILE TESTING


def _id(value):
    return value

def _get_foo(value, instance, field, **kwargs):
    return instance.field_1_foo

def _file_to_lower(f): 
    pos = f.tell()
    f.seek(0)
    new_f = ContentFile(f.read().lower())
    f.seek(pos)
    return new_f


class FileTesting(models.Model):
    # test static default
    field_1 = fields.FileField(upload_to='testing', dependencies=[
        FileDependency(suffix='foo', default="defaults/foo.txt", processor=_id),
        FileDependency(attname='bar', default="defaults/bar.txt")
    ])
    # test default FieldFile
    field_2 = fields.FileField(upload_to='testing', dependencies=[
        FileDependency(default=_get_foo, processor=_file_to_lower)
    ])
    # test cleanup without dependencies
    field_3 = fields.FileField(upload_to='testing')
    # test no cleanup
    field_4 = fields.FileField(upload_to='testing', keep_orphans=True)



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
    image_5 = fields.ImageField(upload_to=UploadTo(name='image_5'), dependencies=[
        FileDependency(suffix='jpeg', processor=processors.WandImageProcessor(
            format='JPEG', scale={'max_width': 200, 'max_height': 150}))
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
    

def _name_getter(name, instance):
    return instance.label
    
class RenameFileTesting(models.Model):
    label = fields.CharField(max_length=32, dependencies=[
        FileDependency(attname='dynamic_name_file', 
                       processor=processors.RenameFileProcessor())
    ])
    dynamic_name_file = models.FileField(
        upload_to=UploadTo(name=_name_getter, add_pk=False))
        


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
                height=240, threads=0, acodec='libmp3lame', abitrate='96k')),
        ])

    def has_upload_permission(self, user, field_name=None):
        return (field_name == 'video_1' and 
                user.is_authenticated() and 
                user.username == 'test_user')


