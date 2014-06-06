from django.core.files.base import ContentFile
from django.utils.image import Image
from django.utils.six import StringIO

from smartfields.processors.base import BaseProcessor, ProcessingError

__all__ = [
    "ImageConverter"
]

# syntax
# pattern: ([extensions], [read_modes], [write_modes])
SUPPORTED_IMAGE_FORMATS = {
    "BMP": (['bmp', 'dib'], ['1', 'L', 'P', 'RGB'], ['1', 'L', 'P', 'RGB']),
    #"DCX": (['dcx'], ['1', 'L', 'P', 'RGB'], None), - Intel fax format
    #"EPS": (['eps', 'ps'], None, ['L', 'RGB']), - No read support
    "GIF": (['gif'], ['P', 'L'], ['P', 'L']),
    "IM": (['im'], [], []),
    "JPEG": (['jpg', 'jpe', 'jpeg'], ['L', 'RGB', 'CMYK'], ['L', 'RGB', 'CMYK']),
    #"PCD": (['pcd'], ['RGB'], None), # segfaults
    "PCX": (['pcx'], ['1', 'L', 'P', 'RGB'], ['1', 'L', 'P', 'RGB']),
    # "PDF": (['pdf'], None, ['1', 'RGB']), - No read support
    "PNG": (['png'], ['1', 'L', 'P', 'RGB', 'RGBA'], ['1', 'L', 'P', 'RGB', 'RGBA']),
    "PPM": (['pbm', 'pgm', 'ppm'], ['1', 'L', 'RGB'], ['1', 'L', 'RGB']),
    "PSD": (['psd'], ['P'], None),
    "TIFF": (['tif', 'tiff'], ['1', 'L', 'RGB', 'CMYK'], ['1', 'L', 'RGB', 'CMYK']),
    "XBM": (['xbm'], ['1'], ['1']),
    "XPM": (['xpm'], ['P'], None),
    "SGI": (['sgi'], ['L', 'RGB'], None),
    "TGA": (['tga', 'tpic'], ['RGB', 'RGBA'], None)
}

class ImageConverter(BaseProcessor):
    preference_mode_list = ['RGBA', 'RGB', 'P', 'CMYK', 'L', '1']
    browser_format_support = ['JPEG', 'GIF', 'PNG']
    responsive = True

    @classmethod
    def browser_exts(cls):
        supported = []
        for format in cls.browser_format_support:
            supported.extend(SUPPORTED_IMAGE_FORMATS.get(format)[0])
        return supported


    @classmethod
    def input_exts(cls):
        supported = []
        for format, support in SUPPORTED_IMAGE_FORMATS.iteritems():
            supported.extend(support[0])
        return supported


    def process(self, max_dim=None, format=None, mode=None, progress_setter=None, **kwargs):
        """
        Resize image to fit it into (width, height) box.
        """
        set_progress = progress_setter or (lambda x: x)
        set_progress(0)
        cur_pos = self.data.tell()
        self.data.seek(0)
        string = StringIO(self.data.read())
        self.data.seek(cur_pos)
        if not (max_dim or format or mode):
            # nothing to do, just return copy of the data
            set_progress(100)
            return ContentFile(string.getvalue())
        image = Image.open(string)
        # decide output format
        format = format or image.format
        support = SUPPORTED_IMAGE_FORMATS.get(format, None)
        if support is None or support[2] is None:
            raise TypeError("Unsupported output format: '%s'" % format)
        supported_modes = support[2]
        # decide output color mode
        if mode and mode not in supported_modes:
            raise TypeError("Unsupported output color mode: '%s' for format: '%s'" %
                            (mode, formt))
        try:
            if mode:
                image = image.convert(mode)
            elif not image.mode in supported_modes:
                for mode in self.preference_mode_list:
                    if mode in supported_modes:
                        image = image.convert(mode)
                    break;
            # decide output dimensions
            new_dim = self.get_dimensions(image.size, max_dim)
            if new_dim is not None:
                image = image.resize(new_dim, resample=Image.ANTIALIAS)
            if format == image.format:
                set_progress(100)
                return ContentFile(string.getvalue())
            string = StringIO()
            image.save(string, format=format)
            set_progress(100)
            return ContentFile(string.getvalue())
        except IOError, e:
            raise ProcessingError(
                "There was a problem with image conversion: %s" % str(e))

    def get_dimensions(self, original, maximum):
        if maximum is None or \
           (original[0] <= maximum[0] and original[1] <= maximum[1]) or \
           (maximum[0] == 0 and original[1] <= maximum[1]) or \
           (maximum[1] == 0 and original[0] <= maximum[0]):
            return None
        maximum = (original[0] if maximum[0] == 0 else maximum[0],
                   original[1] if maximum[1] == 0 else maximum[1])
        requested_ratio = float(maximum[0])/float(maximum[1])
        original_ratio = float(original[0])/float(original[1])
        if original_ratio > requested_ratio:
            return (maximum[0], int(round(maximum[0]*(1/original_ratio))))
        elif original_ratio < requested_ratio:
            return (int(round(maximum[1]*original_ratio)), maximum[1])
        return maximum
