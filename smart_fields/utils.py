from smart_fields import settings

import re, subprocess, time, threading, Queue

try:
    import Image
except ImportError:
    from PIL import Image
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

__all__ = (
    "ImageConverter", "VideoConverter",
)
# syntax
# FORMAT: ([extensions], [read_modes], [write_modes])
SUPPORTED_IMAGE_FORMATS = {
    "BMP": (['bmp', 'dib'], ['1', 'L', 'P', 'RGB'], ['1', 'L', 'P', 'RGB']),
    #"DCX": (['dcx'], ['1', 'L', 'P', 'RGB'], None), - Intel fax format
    #"EPS": (['eps', 'ps'], None, ['L', 'RGB']), - No read support
    "GIF": (['gif'], ['P'], ['P']),	 
    "IM": (['im'], [], []),
    "JPEG": (['jpg', 'jpe', 'jpeg'], ['L', 'RGB', 'CMYK'], ['L', 'RGB', 'CMYK']),
    "PCD": (['pcd'], ['RGB'], None),
    "PCX": (['pcx'], ['1', 'L', 'P', 'RGB'], ['1', 'L', 'P', 'RGB']),
    # "PDF": (['pdf'], None, ['1', 'RGB']), - No read support
    "PNG": (
        ['png'], ['1', 'L', 'P', 'RGB', 'RGBA'], ['1', 'L', 'P', 'RGB', 'RGBA']),
    "PPM": (['pbm', 'pgm', 'ppm'], ['1', 'L', 'RGB'], ['1', 'L', 'RGB']),	 
    "PSD": (['psd'], ['P'], None),
    "TIFF": (
        ['tif', 'tiff'], ['1', 'L', 'RGB', 'CMYK'], ['1', 'L', 'RGB', 'CMYK']),
    "XBM": (['xbm'], ['1'], ['1']),
    "XPM": (['xpm'], ['P'], None),
    "SGI": (['sgi'], ['L', 'RGB'], None),
    "TGA": (['tga', 'tpic'], ['RGB', 'RGBA'], None)
}

class ImageConverter(object):
    preference_mode_list = ['RGBA', 'RGB', 'P', 'CMYK', 'L', '1']
    browser_format_support = ['JPEG', 'GIF', 'PNG']

    def __init__(self, data):
        self.data = data

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
            

    def convert(self, max_dim=None, format=None, mode=None):
        """
        Resize image to fit it into (width, height) box.
        """
        cur_pos = self.data.tell()
        self.data.seek(0)
        string = StringIO(self.data.read())
        self.data.seek(cur_pos)
        if not (max_dim or format or mode):
            # nothing to do, just return copy of the data
            return string.getvalue()
        image = Image.open(string)
        format = format or image.format

        support = SUPPORTED_IMAGE_FORMATS.get(format, None)
        if support is None or support[2] is None:
            raise TypeError("Unsupported output format: '%s'" % format)
        supported_modes = support[2]
        if mode and mode not in supported_modes:
            raise TypeError("Unsupported output mode: '%s' for format: '%s'" % (
                    mode, format))
        if mode:
            image = image.convert(mode)
        elif not image.mode in supported_modes:
            if not supported_modes:
                image = image.convert(PREFERENCE_MODES_LIST[0])
            else:
                for mode in self.preference_mode_list:
                    if mode in supported_modes:
                        image = image.convert(mode)
                    break;

        old_dim = image.size
        if not max_dim is None:
            requested_ratio = float(max_dim[0])/float(max_dim[1])
            old_ratio = float(old_dim[0])/float(old_dim[1])
            if old_ratio > requested_ratio:
                new_dimensions = (max_dim[0], int(round(max_dim[0]*(1/old_ratio))))
            elif old_ratio < requested_ratio:
                new_dimensions = (int(round(max_dim[1]*old_ratio)), max_dim[1])
            else:
                new_dimensions = max_dim

            if old_dim[0] <= max_dim[0] and old_dim[1] <= max_dim[1]:
                new_dimensions = old_dim
                if image.format == format and image.mode == mode:
                    return string.getvalue()
            image = image.resize(new_dimensions, resample=Image.ANTIALIAS)
        string = StringIO()
        image.save(string, format=format)
        return string.getvalue()

 
class AsynchronousFileReader(threading.Thread):
    '''
    Helper class to implement asynchronous reading of a file
    in a separate thread. Pushes read lines on a queue to
    be consumed in another thread.
    source: http://stefaanlippens.net/python-asynchronous-subprocess-pipe-reading
    '''
 
    def __init__(self, fd, queue):
        assert isinstance(queue, Queue.Queue)
        assert callable(fd.readline)
        threading.Thread.__init__(self)
        self._fd = fd
        self._queue = queue
 
    def run(self):
        '''The body of the tread: read lines and put them on the queue.'''
        for line in iter(self._fd.readline, ''):
            self._queue.put(line)
 
    def eof(self):
        '''Check whether there is no more content to expect.'''
        return not self.is_alive() and self._queue.empty()

class VideoConverter(threading.Thread):
    def __init__(self, file_in, files_out, progress_setter=None, progress_key=None):
        self.file_in = file_in
        self.files_out = files_out
        self.total = len(self.files_out)
        self.report_progress = True
        self.duration = None
        if progress_key:
            self.progress_key = progress_key
        else:
            self.report_progress = False
        if progress_setter and callable(progress_setter):
            self.progress_setter = progress_setter
        else:
            self.report_progress = False
        if self.report_progress:
            self.progress_setter(self.progress_key, 0)

        super(VideoConverter, self).__init__()

    def run(self):
        current = 1
        for f_out in self.files_out:
            cmd, p_parser, d_parser = self.construct_command(f_out[0], f_out[1])
            self.convert(cmd, p_parser, d_parser, current)
            current+= 1
        self.progress_setter(self.progress_key, 100)
        
    def set_progress(self, progress, current):
        single = 100.00/self.total
        current_progress = (current-1)*single
        current_progress+= progress*single
        current_progress = current_progress if current_progress < 100 else 99.99
        self.progress_setter(self.progress_key, current_progress)


    def construct_command(self, file_out, custom_profile):
        profile = {'input': self.file_in, 'output': file_out}
        default_profile_name = custom_profile.get('default_profile', None)
        if default_profile_name:
            profile.update(
                settings.DEFAULT_VIDEO_PROFILES.get(default_profile_name, {}))
        profile.update(custom_profile)
        cmd = profile['cmd']
        converter = profile.get('converter', None)
        progress_parser = None
        duration_parser = "Duration: (?P<hours>\d+):(?P<minutes>\d+):(?P<seconds>\d+)"
        if self.report_progress:
            if converter == 'avconv':
                progress_parser = "time=(?P<seconds>\d+)"
            elif converter == 'ffmpeg':
                progress_parser = "time=(?P<hours>\d{2}):(?P<minutes>\d{2}):(?P<seconds>\d{2})"
            else:
                progress_parser = profile.get('progress_parser', None)
                duration_parser = profile.get('duration_parser', None)
        return ((cmd % profile).split(), progress_parser, duration_parser)

    def time_to_seconds(self, groupdict):
        result_list = []
        for key, result in groupdict.iteritems():
            if key == 'hours':
                result_list.append(int(result)*3600)
            if key == 'minutes':
                result_list.append(int(result)*60)
            if key == 'seconds':
                result_list.append(int(result))
        return sum(result_list)
        
         
    def convert(self, cmd, progress_parser, duration_parser, current):
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
        if not self.report_progress or not (progress_parser and duration_parser):
            stdout, stderr = process.communicate()
            return None
        stdout_queue = Queue.Queue()
        stdout_reader = AsynchronousFileReader(process.stdout, stdout_queue)
        stdout_reader.start()
        stderr_queue = Queue.Queue()
        stderr_reader = AsynchronousFileReader(process.stderr, stderr_queue)
        stderr_reader.start()
        while not stdout_reader.eof() or not stderr_reader.eof():
            while not stdout_queue.empty():
                line = stdout_queue.get()
 
            while not stderr_queue.empty():
                line = stderr_queue.get()
                if not self.duration:
                    dur = re.search(duration_parser, line)
                    if dur:
                        self.duration = self.time_to_seconds(dur.groupdict())
                else:
                    prog = re.search(progress_parser, line)
                    if prog:
                        seconds = self.time_to_seconds(prog.groupdict())
                        try:
                            progress = float(seconds)/self.duration
                            self.set_progress(progress, current)
                        # Problem with output parsing. 
                        # Continue, but don't set the progress
                        except ZeroDivisionError: pass 
            time.sleep(1)
 
        stdout_reader.join()
        stderr_reader.join()
 
        process.stdout.close()
        process.stderr.close()

