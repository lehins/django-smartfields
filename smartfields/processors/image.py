import warnings
from django.conf import settings
from django.core.files.base import ContentFile
import six

from smartfields.fields import ImageFieldFile
from smartfields.processors.base import BaseFileProcessor
from smartfields.utils import ProcessingError

try:
    from PIL import Image
except ImportError:
    Image = None
try:
    from wand.image import Image as WandImage
except ImportError:
    WandImage = None

__all__ = [
    'ImageProcessor', 'ImageFormat', 'supported_formats', 'WandImageProcessor'
]

PILLOW_MODES = [
    '1',      # (1-bit pixels, black and white, stored with one pixel per byte)
    'L',      # (8-bit pixels, black and white)
    'LA',     # greyscale with alpha
    'P',      # (8-bit pixels, mapped to any other mode using a color palette)
    'RGB',    # (3x8-bit pixels, true color)
    'RGBA',   # (4x8-bit pixels, true color with transparency mask)
    'CMYK',   # (4x8-bit pixels, color separation)
    'YCbCr',  # (3x8-bit pixels, color video format)
    'LAB',    # (3x8-bit pixels, the L*a*b color space)
    'HSV',    # (3x8-bit pixels, Hue, Saturation, Value color space)
    'I',      # (32-bit signed integer pixels)
    'F',      # (32-bit floating point pixels)
]

PILLOW_IMAGE_SUPPORT = {
    'BMP': (
        ['bmp', 'dib'], ['RGB', 'P', 'L', '1'],  ['RGB', 'P', 'L', '1']),
    'EPS': (
        ['eps', 'ps'], ['RGB', 'LAB', 'L'], ['CMYK', 'RGB', 'L']), # - No read support
    'GIF': (
        ['gif'], ['P', 'L'], ['P', 'L', '1']),
    'IM': (
        ['im'], ['YCbCr', 'CMYK', 'RGBA', 'RGB', 'P', 'LA', 'L', '1'],
        ['F', 'I', 'YCbCr', 'CMYK', 'RGBA', 'RGB', 'P', 'LA', 'L', '1']),
    'JPEG': (
        ['jpg', 'jpe', 'jpeg', 'jfif'], ['CMYK', 'RGB', 'L'], ['CMYK', 'RGB', 'L']),
    'JPEG2000': (
        ['jp2', 'j2k', 'jpc', 'jpf', 'jpx', 'j2c'], 
        ['RGBA', 'RGB', 'LA', 'L'], ['RGBA', 'RGB', 'LA', 'L']),
    'MSP': (
        ['msp'], ['1'], ['1']),
    'PCX': (['pcx'], ['RGB', 'P', 'L', '1'], ['RGB', 'P', 'L', '1']),
    'PNG': (['png'], ['RGBA', 'RGB', 'P', 'L', '1'], ['RGBA', 'RGB', 'P', 'L', '1']),
    'PPM': (['ppm', 'pgm', 'pbm'], ['RGB', 'L', '1'], ['RGB', 'L', '1']),
    'SPIDER': (['spi'], ['F;32F'], ['F;32F']),
    'TIFF': (['tif', 'tiff'], 
        ['F', 'I', 'YCbCr', 'CMYK', 'RGBA', 'RGB', 'P', 'LA', 'L', '1'],
        ['F', 'I', 'LAB', 'YCbCr', 'CMYK', 'RGBA', 'RGB', 'P', 'LA', 'L', '1']),
    'WEBP': (['webp'], ['RGBA', 'RGB'], ['RGBA', 'RGB']),
    'XBM': (['xbm'], ['1'], ['1']),

    'DCX': (['dcx'], ['1', 'L', 'P', 'RGB'], None), # - Intel fax format
    # PCD format segfaults: https://github.com/python-pillow/Pillow/issues/568
    # 'PCD': (['pcd'], ['RGB'], None),
    'PDF': (['pdf'], None, ['1', 'RGB']),
    'PSD': (['psd'], ['P'], None),
    'XPM': (['xpm'], ['P'], None),
    'SGI': (['sgi'], ['L', 'RGB'], None),
    'TGA': (['tga', 'tpic'], ['RGB', 'RGBA'], None)
}


def _round(val):
    """
    Round val to int.

    Args:
        val: (float): write your description
    """
    # emulate python3 way of rounding toward the even choice
    new_val = int(round(val))
    if abs(val - new_val) == 0.5 and new_val % 2 == 1:
        return new_val - 1
    return new_val


class ImageFormat(object):

    def __init__(self, format, mode=None, ext=None, save_kwargs=None):
        """
        Initialize input files.

        Args:
            self: (todo): write your description
            format: (str): write your description
            mode: (todo): write your description
            ext: (str): write your description
            save_kwargs: (dict): write your description
        """
        self.format = format
        self.mode = mode
        self.ext = ext
        self.exts, self.input_modes, self.output_modes = PILLOW_IMAGE_SUPPORT[format]
        assert mode is None or (self.can_write and mode in self.output_modes), \
            "Pillow cannot write \"%s\" in this mode: \"%s\"" % (self.format, mode)
        self.save_kwargs = save_kwargs or {}
        
    def __str__(self):
        """
        : return : class

        Args:
            self: (todo): write your description
        """
        return self.format

    def __eq__(self, other):
        """
        Returns true if other is equal false otherwise.

        Args:
            self: (todo): write your description
            other: (todo): write your description
        """
        return str(self) == str(other)

    @property
    def can_read(self):
        """
        Returns true if the input can be read or not.

        Args:
            self: (todo): write your description
        """
        return self.input_modes is not None

    @property
    def can_write(self):
        """
        Returns true if the output can be written.

        Args:
            self: (todo): write your description
        """
        return self.output_modes is not None

    def get_ext(self):
        """
        Return the extension of the file.

        Args:
            self: (todo): write your description
        """
        if self.ext is not None:
            return self.ext
        return self.exts[0]

    def get_exts(self):
        """Returns a string of comma separated known extensions for this format"""
        return ','.join(self.exts)

    def get_mode(self, old_mode=None):
        """Returns output mode. If `mode` not set it will try to guess best
        mode, or next best mode comparing to old mode

        """
        if self.mode is not None:
            return self.mode
        assert self.can_write, "This format does not have a supported output mode."
        if old_mode is None:
            return self.output_modes[0]
        if old_mode in self.output_modes:
            return old_mode
        # now let's get best mode available from supported
        try:
            idx = PILLOW_MODES.index(old_mode)
        except ValueError:
            # maybe some unknown or uncommon mode
            return self.output_modes[0]
        for mode in PILLOW_MODES[idx+1:]:
            if mode in self.output_modes:
                return mode
        # since there is no better one, lets' look for closest one in opposite direction
        opposite = PILLOW_MODES[:idx]
        opposite.reverse()
        for mode in opposite:
            if mode in self.output_modes:
                return mode



class ImageFormats(dict):

    def __init__(self, formats):
        """
        Initialize formats.

        Args:
            self: (todo): write your description
            formats: (str): write your description
        """
        super(ImageFormats, self).__init__([(f, ImageFormat(f)) for f in formats])

    @property
    def input_exts(self):
        """
        Return a list of all input extensions.

        Args:
            self: (todo): write your description
        """
        return ','.join([f.get_exts() for _, f in six.iteritems(self) if f.can_read])


supported_formats = ImageFormats(getattr(settings, 'SMARTFIELDS_IMAGE_FORMATS', [
    'PCX', 'XPM', 'TIFF', 'JPEG', 'XBM', 'GIF', 'IM', 'PSD', 'PPM', 'SGI', 'BMP', 
    'TGA', 'PNG', # 'DCX', 'EPS', 'PCD', 'PDF' - not useful or buggy formats
]))


class ImageProcessor(BaseFileProcessor):
    field_file_class = ImageFieldFile
    supported_formats = supported_formats

    @property
    def resample(self):
        """
        Resample the image.

        Args:
            self: (todo): write your description
        """
        # resampling was renamed from Image.ANTIALIAS to Image.LANCZOS
        return getattr(Image, 'LANCZOS', getattr(Image, 'ANTIALIAS')) 

    def get_params(self, **kwargs):
        """
        Get parameters.

        Args:
            self: (todo): write your description
        """
        params = super(ImageProcessor, self).get_params(**kwargs)
        if 'format' in params:
            format = params['format']
            if not isinstance(format, ImageFormat):
                format = ImageFormat(format)
            assert format.can_write, \
                "This format: \"%s\" is not supported for output." % format
            params['format'] = format
        return params

    def check_params(self, **kwargs):
        """
        Method to make sure all parameters have been set.

        Args:
            self: (todo): write your description
        """
        params = self.get_params(**kwargs)
        scale = params.get('scale', None)
        if scale is not None:
            self._check_scale_params(**scale)

    def get_ext(self, **kwargs):
        """
        Get the extension of a file extension.

        Args:
            self: (todo): write your description
        """
        try:
            format = self.get_params(**kwargs)['format']
            ext = format.get_ext()
            if ext:
                return ".%s" % ext
            elif ext is not None:
                return ext
        except KeyError: pass

    def _check_scale_params(self, width=None, height=None, min_width=None, min_height=None, 
                            max_width=None, max_height=None, preserve=True):
        """
        Check that the scale parameters.

        Args:
            self: (todo): write your description
            width: (int): write your description
            height: (int): write your description
            min_width: (float): write your description
            min_height: (int): write your description
            max_width: (int): write your description
            max_height: (int): write your description
            preserve: (todo): write your description
        """
        assert width is None or (min_width is None and max_width is None), \
            "min_width or max_width don't make sence if width cannot be changed"
        assert height is None or (min_height is None and max_height is None), \
            "min_height or max_height don't make sence if height cannot be changed"
        assert min_width is None or max_width is None or min_width < max_width, \
            "min_width should be smaller than max_width"
        assert min_height is None or max_height is None or min_height < max_height, \
            "min_height should be smaller than max_height"
        if preserve:
            assert width is None or height is None, \
                "cannot preserve ratio when both width and height are set"
            assert width is None or (min_height is None and max_height is None), \
                "cannot preserve ratio when width is set and there are restriction on height"
            assert height is None or (min_width is None and max_width is None), \
                "cannot preserve ratio when height is set and there are restriction on width"
            assert min_width is None or max_height is None
            assert max_width is None or min_height is None
            
    def get_dimensions(self, old_width, old_height, width=None, height=None, 
                       min_width=None, min_height=None, 
                       max_width=None, max_height=None, preserve=True):
        """
        Get the width and height of a new dimensions.

        Args:
            self: (todo): write your description
            old_width: (int): write your description
            old_height: (int): write your description
            width: (int): write your description
            height: (int): write your description
            min_width: (int): write your description
            min_height: (float): write your description
            max_width: (int): write your description
            max_height: (int): write your description
            preserve: (str): write your description
        """
        self._check_scale_params(
            width, height, min_width, min_height, max_width, max_height, preserve)
        ratio = float(old_width)/old_height
        new_width, new_height = old_width, old_height
        if width is not None:
            new_width = width
            if preserve:
                new_height = _round(new_width/ratio)
        if height is not None:
            new_height = height
            if preserve:
                new_width = _round(new_height*ratio)
        if min_width and min_width > new_width:
            new_width = min_width
            if preserve:
                new_height = _round(new_width/ratio)
        if min_height and min_height > new_height:
            new_height = min_height
            if preserve:
                new_width = _round(new_height*ratio)
        if max_width and max_width < new_width:
            new_width = max_width
            if preserve:
                new_height = _round(new_width/ratio)
        if max_height and max_height < new_height:
            new_height = max_height
            if preserve:
                new_width = _round(new_height*ratio)
        return new_width, new_height

    def resize(self, image, scale=None, **kwargs):
        """
        Resize the image.

        Args:
            self: (todo): write your description
            image: (array): write your description
            scale: (float): write your description
        """
        if scale is not None:
            new_size = self.get_dimensions(*image.size, **scale)
            if image.size != new_size:
                return image.resize(new_size, resample=self.resample)
        return image

    def convert(self, image, format=None, **kwargs):
        """
        Convert the image to image.

        Args:
            self: (todo): write your description
            image: (array): write your description
            format: (todo): write your description
        """
        if format is None:
            return None
        new_mode = format.get_mode(old_mode=image.mode)
        if new_mode != image.mode:
            if new_mode == 'P':
                # TODO: expiremental, need some serious testing
                palette_size = 256
                if image.palette:
                    palette_size = len(image.palette.getdata()[1]) // 3
                image = image.convert(
                    new_mode, palette=Image.ADAPTIVE, colors=palette_size)
            else:
                image = image.convert(new_mode)
        if format != image.format:
            stream_out = six.BytesIO()
            image.save(stream_out, format=str(format), **format.save_kwargs)
            return stream_out

    def get_image(self, stream, **kwargs):
        """
        Get an image from file.

        Args:
            self: (int): write your description
            stream: (str): write your description
        """
        with warnings.catch_warnings():
            if not settings.DEBUG:
                warnings.simplefilter("error", Image.DecompressionBombWarning)
            image = Image.open(stream)
        return image

    def process(self, value, scale=None, format=None, **kwargs):
        """
        Process the image.

        Args:
            self: (todo): write your description
            value: (todo): write your description
            scale: (float): write your description
            format: (str): write your description
        """
        cur_pos = value.tell()
        value.seek(0)
        stream = six.BytesIO(value.read())
        stream_out = None
        value.seek(cur_pos)
        try:
            image = self.get_image(stream, scale=scale, format=format, **kwargs)
            image = self.resize(image, scale=scale, format=format, **kwargs)
            stream_out = self.convert(image, scale=scale, format=format, **kwargs)
            if stream_out is not None:
                content = stream_out.getvalue()
            else:
                content = stream.getvalue()
        except (IOError, OSError, Image.DecompressionBombWarning) as e:
            raise ProcessingError(
                "There was a problem with image conversion: %s" % e)
        finally:
            if stream_out is not None:
                stream_out.close()
            stream.close()
        return ContentFile(content)


class WandImageProcessor(ImageProcessor):

    def resize(self, image, scale=None, **kwargs):
        """
        Resize the image.

        Args:
            self: (todo): write your description
            image: (array): write your description
            scale: (float): write your description
        """
        if scale is not None:
            new_size = self.get_dimensions(*image.size, **scale)
            if image.size != new_size:
                image.resize(*new_size)
        return image

    def convert(self, image, format=None, **kwargs):
        """
        Convert image to image.

        Args:
            self: (todo): write your description
            image: (array): write your description
            format: (str): write your description
        """
        if format is not None:
            image.format = str(format)
            stream_out = six.BytesIO()
            image.save(file=stream_out)
            return stream_out
        
    def get_image(self, stream, **kwargs):
        """
        Return image object corresponding to stream.

        Args:
            self: (int): write your description
            stream: (str): write your description
        """
        return WandImage(file=stream)
        
