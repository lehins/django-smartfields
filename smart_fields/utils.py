from django.core.cache import cache
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.conf import settings

import re, os, subprocess, datetime, time, threading, Queue, logging, string

from xml.dom.minidom import parse, parseString



logger = logging.getLogger('crowdsite.errors')

def get_size(start_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def rm_dir(dir_path):
    try: #best attempt to clean up
        for path in (os.path.join(dir_path, f) for f in os.listdir(dir_path)):
            if os.path.isdir(path):
                rm_dir(path)
            else:
                os.unlink(path)
        os.rmdir(dir_path)
    except: pass



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
    def __init__(self, f, path, fname, cache_key=None, user=None,
                 exts=("mp4", "webm")):
        self.f = f
        self.path = path
        self.fname = fname
        self.exts = exts
        self.user = user
        self.duration = None
        self.cache_key = cache_key
        super(VideoConverter, self).__init__()

    def save(self):
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        self.tmp_path = os.path.join(self.path, self.f.name)
        tmp_file = open(self.tmp_path, 'wb+')
        for chunk in self.f.chunks():
            tmp_file.write(chunk)
        tmp_file.close()
        try:
            info = None
            try:
                # best attempt to get video info
                info = self.video_info(self.tmp_path)
            except Exception, e:
                logger.error("user: %s, error: %s", self.user, repr(e))
            self.configure(info)
            self.start()
        except Exception, e:
            logger.error("user: %s, error: %s", self.user, repr(e))
            cache.set(self.cache_key, {
                    'task': "Error",
                    'code_name': "error",
                    'description': "Problem converting the video. Possibly unsupported video format. Incident was reported and we will look into the cause of the problem.",
                    }, timeout=300)
            raise
        
    def run(self):
        count = 1
        for ext in self.exts:
            try:
                self.convert_to(self.tmp_path, ext, count, len(self.exts))
            except Exception, e:
                logger.error("user: %s, error: %s", self.user, repr(e))
                cache.set(self.cache_key, {
                        'task': "Error",
                        'code_name': "error",
                        'description': "Problem converting the video. Incident was reported and we will look into the cause of the problem.",
                        }, timeout=300)
                raise
            count += 1
            #if cache.get(self.cache_key)['task'] != 'Error':
        os.unlink(self.tmp_path)
        if self.cache_key:
            cache.set(self.cache_key, {
                    'task': "Finished",
                    'code_name': "finished",
                    }, timeout=300)
        
    def configure(self, info=None):
        height = 360
        vbitrate = 300
        maxrate = 300
        abitrate = 96
        bufsize = maxrate * 2
        if info and height > info['height']:
            height = info['height']
            if vbitrate > info['bit_rate']:
                vbitrate = info['bit_rate']
        self.conf = {
            '-b:v': "%sk" % vbitrate,
            '-maxrate': "%sk" % maxrate,
            '-bufsize': "%sk" % bufsize,
            '-vf': "scale=-1:%s" % height,
            '-b:a': "%sk" % abitrate,
            }
        
         
    def convert_to(self, orig_path, ext, current, total):
        dest_name = os.path.join(self.path, "%s.%s" % (self.fname, ext))
        dur_re = "Duration: (?P<hours>\d{2}):(?P<minutes>\d{2}):(?P<seconds>\d{2})"
        p_re = "time=(?P<seconds>\d+)"
        # ffmpeg
        # p_re = "time=(?P<hours>\d{2}):(?P<minutes>\d{2}):(?P<seconds>\d{2})"
        if ext == "mp4":
            command = ['avconv', '-i', orig_path, '-y', 
                       '-codec:v', 'libx264', 
                       '-vprofile', 'main', 
                       '-preset', 'medium', 
                       '-b:v', self.conf['-b:v'], 
                       '-maxrate', self.conf['-maxrate'], 
                       '-bufsize', self.conf['-bufsize'], 
                       '-vf', self.conf['-vf'], 
                       '-threads', '0', 
                       '-codec:a', 'libvo_aacenc', 
                       '-b:a', self.conf['-b:a'], dest_name]
        elif ext == "webm":
            command = ['avconv', '-i', orig_path, '-y', 
                       '-codec:v', 'libvpx', 
                       '-b:v', self.conf['-b:v'], 
                       '-qmin', '10', 
                       '-qmax', '42', 
                       '-maxrate', self.conf['-maxrate'], 
                       '-bufsize', self.conf['-bufsize'], 
                       '-threads', '4', 
                       '-vf', self.conf['-vf'], 
                       '-codec:a', 'libvorbis', 
                       '-b:a', self.conf['-b:a'], dest_name]
        else:
            raise NotImplementedError()
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
        if not self.cache_key:
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
                    dur = re.search(dur_re, line)
                    if dur:
                        self.duration = 3600*int(dur.group('hours'))
                        self.duration += 60*int(dur.group('minutes'))
                        self.duration += int(dur.group('seconds'))
                else:
                    prog = re.search(p_re, line)
                    if prog:
                        progress = int(prog.group('seconds'))
                        progress = progress*100/self.duration
                        cache.set(self.cache_key, {
                                'task': "Converting (step %s of %s)" % (
                                    current, total),
                                'code_name': "converting",
                                'progress': progress,
                                }, timeout=5)
            time.sleep(1)
 
        stdout_reader.join()
        stderr_reader.join()
 
        process.stdout.close()
        process.stderr.close()

    def video_info(self, path):
        # TODO convert to using regex instead of xml
        command = ["mediainfo", "--Output=XML", path]
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        result = parseString(stdout)
        height = int(result.getElementsByTagName("Height")[0].firstChild.data.split()[0])
        width = int(result.getElementsByTagName("Width")[0].firstChild.data.split()[0])
        duration = result.getElementsByTagName("Duration")[0].firstChild.data.split()
        total_dur = 0
        for d in duration:
            try:
                total_dur+= time.strptime(d, "%Hh").tm_hour*3600
            except ValueError: pass
            try:
                total_dur+= time.strptime(d, "%Mmn").tm_min*60
            except ValueError: pass
            try:
                total_dur+= time.strptime(d, "%Ss").tm_sec #ms
            except ValueError: pass
        bit_rate = result.getElementsByTagName("Overall_bit_rate")[0].firstChild.data
        bit_rate = int(float(''.join(bit_rate.replace("Kbps", '').split())))
        return {'width': width, 'height': height, 
                'duration': total_dur, 'bit_rate': bit_rate}


