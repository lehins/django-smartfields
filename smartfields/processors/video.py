import re
from django.utils import six

from smartfields.processors.base import ExternalFileProcessor
from smartfields.utils import ProcessingError

__all__ = [
    'FFMPEGProcessor'
]

class FFMPEGProcessor(ExternalFileProcessor):
    duration_re = re.compile(r'Duration: (?P<hours>\d+):(?P<minutes>\d+):(?P<seconds>\d+)')
    progress_re = re.compile(r'time=(?P<hours>\d+):(?P<minutes>\d+):(?P<seconds>\d+)')
    error_re = re.compile(r'Invalid data found when processing input')
    cmd_template = "ffmpeg -i {input} -y -codec:v {vcodec} -b:v {vbitrate} " \
                   "-maxrate {maxrate} -bufsize {bufsize} -vf " \
                   "scale={width}:{height} -threads {threads} -c:a {acodec} {output}"
    
    def stdout_handler(self, line, duration=None):
        if duration is None:
            duration_time = self.duration_re.search(line)
            if duration_time:
                duration = self.timedict_to_seconds(duration_time.groupdict())
        elif duration != 0:
            current_time = self.progress_re.search(line)
            if current_time:
                seconds = self.timedict_to_seconds(current_time.groupdict())
                progress = float(seconds)/duration
                progress = progress if progress < 1 else 0.99
                self.set_progress(progress)
        elif self.error_re.search(line):
            raise ProcessingError("Invalid video file or unknown video format.")
        return (duration,)

    def timedict_to_seconds(self, timedict):
        seconds = 0
        for key, t in six.iteritems(timedict):
            if key == 'seconds':
                seconds+= int(t)
            elif key == 'minutes':
                seconds+= int(t)*60
            elif key == 'hours':
                seconds+= int(t)*3600
        return seconds
