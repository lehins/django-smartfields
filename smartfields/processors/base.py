import subprocess, time
from django.utils import six
from django.utils.deconstruct import deconstructible
from django.utils.text import slugify
from django.utils import six

from smartfields.utils import NamedTemporaryFile, AsynchronousFileReader

__all__ = [
    'BaseProcessor', 'BaseFileProcessor', 'ExternalFileProcessor', 'SlugProcessor'
]

@deconstructible
class BaseProcessor(object):
    task = 'process'
    task_name = 'Processing'

    def __init__(self, **kwargs):
        self.default_params = kwargs

    def __call__(self, value, instance=None, field=None, field_value=None, **kwargs):
        return self.process(value, instance, field, field_value, 
                            **self.get_params(**kwargs))

    def __eq__(self, other):
        return (type(self) is type(other) and 
                self.default_params == other.default_params)

    def get_params(self, **kwargs):
        params = self.default_params.copy()
        params.update(kwargs)
        return params

    def set_progress(self, progress):
        # see if dependency has set a progress setter, if so use it.
        try:
            getattr(self, 'progress_setter')(self, progress)
        except AttributeError: pass

    def process(self, value, instance, field, field_value, **params):
        raise NotImplementedError("process is a required method")


class BaseFileProcessor(BaseProcessor):

    #def __call__(self, file, *args, **kwargs):
    #    if file:
    #        return super(BaseFileProcessor, self).__call__(file, *args, **kwargs)


    def get_ext(self, format=None, **kwargs):
        """Returns new file extension based on a processor's `format` parameter.
        Overwrite if different extension should be set ex: `'.txt'` or `None` if this 
        processor does not change file's extension.
        """
        try:
            format = format or self.default_params['format']
            return ".%s" % format.lower()
        except KeyError: pass


class SlugProcessor(BaseProcessor):

    def process(self, value, *args, **kwargs):
        return slugify(value)


class ExternalFileProcessor(BaseFileProcessor):

    cmd_template = None
    # if it is a callable it will be invoked for each line from stdout
    stdout_handler = None
    # if set to None, will ignore stderr, if True, will pipe it to stdout and it will
    # then be handled by stdout handler. If it is callable same as above.
    stderr_handler = True

    def __init__(self, cmd_template=None, sleep_time=1, **kwargs):
        self.cmd_template = cmd_template or self.cmd_template
        if self.cmd_template is None:
            raise ValueError('"cmd_template" is a required argument')
        self.sleep_time = sleep_time
        super(ExternalFileProcessor, self).__init__(**kwargs)

    def get_out_file(self, in_file, instance, field, field_value, **kwargs):
        return NamedTemporaryFile(mode='rb', suffix='_%s_%s%s' % (
            instance._meta.model_name, field.name, self.get_ext()))

    def process(self, in_file, instance, field, field_value, **kwargs):
        out_file = self.get_out_file(in_file, instance, field, field_value, **kwargs)
        cmd = self.cmd_template.format(
            input=in_file.path, output=out_file.name, **kwargs).split()
        stdout_pipe, stdout_queue, stdout_reader = None, None, None
        stderr_pipe, stderr_queue, stderr_reader = None, None, None
        if callable(self.stdout_handler):
            stdout_pipe = subprocess.PIPE
            stdout_queue = six.moves.queue.Queue()
        if self.stderr_handler is True:
            stderr_pipe = subprocess.STDOUT
        elif callable(self.stderr_handler):
            stderr_pipe = subprocess.PIPE
            stderr_queue = six.moves.queue.Queue()
        _subprocess = subprocess.Popen(
            cmd, stdout=stdout_pipe, stderr=stderr_pipe, universal_newlines=True)
        if stdout_queue is not None:
            stdout_reader = AsynchronousFileReader(_subprocess.stdout, stdout_queue)
            stdout_reader.start()
        if stderr_queue is not None:
            stderr_reader = AsynchronousFileReader(_subprocess.stderr, stderr_queue)
            stderr_reader.start()
        if stdout_reader is None and stderr_reader is None:
            _subprocess.wait()
        else:
            stdout_args, stderr_args = () , ()
            while not (stdout_reader is None or stdout_reader.eof()) or \
                  not (stderr_reader is None or stderr_reader.eof()):
                if stdout_queue is not None:
                    while not stdout_queue.empty():
                        stdout_args = self.stdout_handler(
                            stdout_queue.get(), *stdout_args) or ()
                if stderr_queue is not None:
                    while not stderr_queue.empty():
                        stderr_args = self.stderr_handler(
                            stderr_queue.get(), *stderr_args) or ()
                time.sleep(self.sleep_time)
            if stdout_reader is not None:
                stdout_reader.join()
                _subprocess.stdout.close()
            if stderr_reader is not None:
                stderr_reader.join()
                _subprocess.stderr.close()
        return out_file


