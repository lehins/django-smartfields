from django.core.files.base import ContentFile
from django.conf import settings

import re, os, subprocess, datetime, time, threading, Queue, logging, string

from xml.dom.minidom import parse, parseString

DEFAULT_PROFILES = getattr(settings, 'SMARTFIELDS_DEFAULT_VIDEO_PROFILES', {
    'mp4': {
        'format': 'mp4',
        'cmd': "%(converter)s -i %(input)s -y -codec:v %(vcodec)s " \
            "-vprofile %(vprofile)s -preset %(preset)s -b:v %(vbitrate)s " \
            "-maxrate %(maxrate)s -bufsize %(bufsize)s " \
            "-vf scale=%(width)s:%(height)s " \
            "-threads %(threads)s -codec:a %(acodec)s -b:a %(abitrate)s %(output)s",
        'converter': 'avconv',
        'vcodec': 'libx264',
        'vprofile': 'main',
        'preset': 'medium',
        'vbitrate': '300k',
        'maxrate': '300k',
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


def resize_image(data, width, height, format='PNG'):
    """
    Resize image to fit it into (width, height) box.
    """
    try:
        import Image
    except ImportError:
        from PIL import Image
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO
    string = StringIO(data.read())
    image = Image.open(string)
    old_dim = image.size
    max_dim = (width, height)
    
    requested_ratio = float(max_dim[0])/float(max_dim[1])
    old_ratio = float(old_dim[0])/float(old_dim[1])
    if old_ratio > requested_ratio:
        new_dimensions =  (max_dim[0], int(round(max_dim[0]*(1/old_ratio))))
    elif old_ratio < requested_ratio:
        new_dimensions = (int(round(max_dim[1]*old_ratio)), max_dim[1])
    else:
        new_dimensions = max_dim
    
    if old_dim[0] <= max_dim[0] and old_dim[1] <= max_dim[1]:
        new_dimensions = old_dim
        import imghdr, decimal
        if imghdr.what(string) == format.lower():
            return string.getvalue()
    image = image.resize(new_dimensions, resample=Image.ANTIALIAS)
    
    string = StringIO()
    if format == 'JPEG' and image.mode != 'RGB':
        image = image.convert('RGB')
    if format == 'PNG' and not (image.mode != 'P' or image.mode != 'RGB'):
        image = image.convert('RGB')
    image.save(string, format=format)
    return ContentFile(string.getvalue())

 
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
        self.progress_setter(self.progress_key, current_progress)


    def construct_command(self, file_out, custom_profile):
        profile = {'input': self.file_in, 'output': file_out}
        default_profile_name = custom_profile.get('default_profile', None)
        if default_profile_name:
            profile.update(DEFAULT_PROFILES.get(default_profile_name, {}))
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

