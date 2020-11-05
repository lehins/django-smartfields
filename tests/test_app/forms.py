from django import forms

try:
    from django.core.urlresolvers import reverse
except ImportError:
    from django.urls import reverse

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout

from smartfields.crispy.layout import ImageField, VideoField, LimitedField
from smartfields.processors.image import supported_formats

from .models import TextTesting, ImageTesting, VideoTesting


class TextTestingForm(forms.ModelForm):

    class Meta:
        model = TextTesting
        fields = ('title',)

    def __init__(self, *args, **kwargs):
        """
        Initialize layout

        Args:
            self: (todo): write your description
        """
        super(TextTestingForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(LimitedField('title'))


class ImageTestingForm(forms.ModelForm):

    class Meta:
        model = ImageTesting
        fields = ('image_2',)

    def __init__(self, *args, **kwargs):
        """
        Initialize layout.

        Args:
            self: (todo): write your description
        """
        super(ImageTestingForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            ImageField('image_2', plupload_options={
                'url': reverse('smartfields:upload', kwargs={
                    'app_label': 'tests',
                    'model': 'imagetesting',
                    'field_name': 'image_2'
                }),
                'filters': {
                    'max_file_size': "20mb",
                    'mime_types': [{'title': "Image Files",
                                    'extensions': supported_formats.input_exts}]
                }}))


class VideoTestingForm(forms.ModelForm):

    class Meta:
        model = VideoTesting
        fields = ('video_1',)

    def __init__(self, *args, **kwargs):
        """
        Initialize the upload metrics.

        Args:
            self: (todo): write your description
        """
        super(VideoTestingForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            VideoField('video_1', plupload_options={
                'url': reverse('smartfields:upload', kwargs={
                    'app_label': 'tests',
                    'model': 'videotesting',
                    'field_name': 'video_1'
                }),
                'filters': {
                    'max_file_size': "1024mb",
                    'mime_types': [{'title': "Video Files",
                                    'extensions': "avi,mp4,mpg,mpeg,wmv,mov,webm"}]
                }}))
