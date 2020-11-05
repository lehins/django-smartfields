import subprocess, time
from six.moves import queue

from smartfields.utils import NamedTemporaryFile, AsynchronousFileReader, \
    ProcessingError, deconstructible, get_model_name

__all__ = [
    'BaseProcessor', 'BaseFileProcessor', 'RenameFileProcessor', 'ExternalFileProcessor'
]

@deconstructible
class BaseProcessor(object):
    task = 'processing'
    task_name = 'Processing'

    def __init__(self, **kwargs):
        """
        Initialize this instance.

        Args:
            self: (todo): write your description
        """
        self.default_params = kwargs

    def __call__(self, value, instance=None, field=None, dependee=None, 
                 stashed_value=None, **kwargs):
        """
        Call a single call with the given value.

        Args:
            self: (todo): write your description
            value: (str): write your description
            instance: (todo): write your description
            field: (todo): write your description
            dependee: (todo): write your description
            stashed_value: (str): write your description
        """
        return self.process(
            value, instance=instance, field=field, dependee=dependee, 
            stashed_value=stashed_value, **self.get_params(**kwargs))

    def __eq__(self, other):
        """
        Returns true if other is the same as other.

        Args:
            self: (todo): write your description
            other: (todo): write your description
        """
        return (type(self) is type(other) and 
                self.default_params == other.default_params)

    def check_params(self, **kwargs):
        """
        Check if all of the params.

        Args:
            self: (todo): write your description
        """
        pass

    def get_params(self, **kwargs):
        """
        Get kwargs dict.

        Args:
            self: (todo): write your description
        """
        params = self.default_params.copy()
        params.update(kwargs)
        return params

    def set_progress(self, progress):
        """
        Sets the progress. progress. progress. progress.

        Args:
            self: (todo): write your description
            progress: (todo): write your description
        """
        # see if dependency has set a progress setter, if so use it.
        progress_setter = getattr(self, 'progress_setter', None)
        if callable(progress_setter):
            progress_setter(self, progress)

    def process(self, value, **kwargs):
        """
        Process the given value.

        Args:
            self: (todo): write your description
            value: (todo): write your description
        """
        return value


class BaseFileProcessor(BaseProcessor):

    def get_ext(self, format=None, **kwargs):
        """Returns new file extension based on a processor's `format` parameter.
        Overwrite if different extension should be set ex: `'.txt'` or `None` if this 
        processor does not change file's extension.
        """
        try:
            format = format or self.default_params['format']
            return ".%s" % format.lower()
        except KeyError: pass


class RenameFileProcessor(BaseFileProcessor):

    def process(self, value, stashed_value=None, **kwargs):
        """
        Process a single field.

        Args:
            self: (todo): write your description
            value: (todo): write your description
            stashed_value: (todo): write your description
        """
        field_file = stashed_value
        if not field_file or not field_file._committed:
            return field_file
        field_file.file.temporary_file_path = lambda: field_file.path
        return field_file.file


class ExternalFileProcessor(BaseFileProcessor):

    cmd_template = None
    # if it is a callable it will be invoked for each line from stdout
    stdout_handler = None
    # if set to None, will ignore stderr, if True, will pipe it to stdout and it will
    # then be handled by stdout handler. If it is callable same as above.
    stderr_handler = True

    def __init__(self, cmd_template=None, sleep_time=1, **kwargs):
        """
        Initialize the template.

        Args:
            self: (todo): write your description
            cmd_template: (todo): write your description
            sleep_time: (float): write your description
        """
        self.cmd_template = cmd_template or self.cmd_template
        if self.cmd_template is None:
            raise ValueError('"cmd_template" is a required argument')
        self.sleep_time = sleep_time
        super(ExternalFileProcessor, self).__init__(**kwargs)

    def __eq__(self, other):
        """
        Determine if two strings.

        Args:
            self: (todo): write your description
            other: (todo): write your description
        """
        return super(ExternalFileProcessor, self).__eq__(other) and \
            self.cmd_template == other.cmd_template

    def get_input_path(self, in_file):
        """
        Get the path of the input file.

        Args:
            self: (todo): write your description
            in_file: (str): write your description
        """
        return in_file.path

    def get_output_path(self, out_file):
        """
        Returns the output path for the output file.

        Args:
            self: (todo): write your description
            out_file: (str): write your description
        """
        return out_file.name

    def get_output_file(self, in_file, instance, field, **kwargs):
        """Creates a temporary file. With regular `FileSystemStorage` it does not 
        need to be deleted, instaed file is safely moved over. With other cloud
        based storage it is a good idea to set `delete=True`."""
        return NamedTemporaryFile(mode='rb', suffix='_%s_%s%s' % (
            get_model_name(instance), field.name, self.get_ext()), delete=False)

    def process(self, in_file, **kwargs):
        """
        Process a process.

        Args:
            self: (todo): write your description
            in_file: (str): write your description
        """
        out_file = self.get_output_file(in_file, **kwargs)
        cmd = self.cmd_template.format(
            input=self.get_input_path(in_file), output=self.get_output_path(out_file),
            **kwargs
        ).split()
        stdout_pipe, stdout_queue, stdout_reader = None, None, None
        stderr_pipe, stderr_queue, stderr_reader = None, None, None
        if callable(self.stdout_handler):
            stdout_pipe = subprocess.PIPE
            stdout_queue = queue.Queue()
        if self.stderr_handler is True:
            stderr_pipe = subprocess.STDOUT
        elif callable(self.stderr_handler):
            stderr_pipe = subprocess.PIPE
            stderr_queue = queue.Queue()
        proc = subprocess.Popen(
            cmd, stdout=stdout_pipe, stderr=stderr_pipe, universal_newlines=True)
        if stdout_queue is not None:
            stdout_reader = AsynchronousFileReader(proc.stdout, stdout_queue)
            stdout_reader.start()
        if stderr_queue is not None:
            stderr_reader = AsynchronousFileReader(proc.stderr, stderr_queue)
            stderr_reader.start()
        if stdout_reader is None and stderr_reader is None:
            proc.wait()
        else:
            stdout_args, stderr_args = () , ()
            try:
                while not (stdout_reader is None or stdout_reader.eof()) or \
                      not (stderr_reader is None or stderr_reader.eof()):
                    if stdout_queue is not None:
                        while not stdout_queue.empty():
                            stdout_args = self.stdout_handler( # pylint: disable=not-callable
                                stdout_queue.get(), *stdout_args) or ()
                    if stderr_queue is not None:
                        while not stderr_queue.empty():
                            stderr_args = self.stderr_handler( # pylint: disable=not-callable
                                stderr_queue.get(), *stderr_args) or ()
                    time.sleep(self.sleep_time)
            except ProcessingError:
                if proc.poll() is None:
                    proc.terminate()
                raise
            finally:
                # wait for process to finish, so we can check the return value
                if proc.poll() is None:
                    proc.wait()
                if stdout_reader is not None:
                    stdout_reader.join()
                    proc.stdout.close()
                if stderr_reader is not None:
                    stderr_reader.join()
                    proc.stderr.close()
        if proc.returncode < 0:
            raise ProcessingError("There was a problem processing this file.")
        return out_file


