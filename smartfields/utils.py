import os, errno, importlib

from django.core.files import base, temp


class NamedTemporaryFile(base.File):
    """This class is required for FileStorage to make an attempt in moving the
    file, instead of copying it by chunks in memory

    """
    def __init__(self, **kwargs):
        file = temp.NamedTemporaryFile(**kwargs)
        super(NamedTemporaryFile, self).__init__(file)

    def temporary_file_path(self):
        """
        Returns the full path of this file.
        """
        return self.file.name

    def close(self):
        # caching the size before closing for proper file moving and saving
        self._size = self._get_size()
        try:
            return self.file.close()
        except OSError as e:
            if e.errno != errno.ENOENT:
                # Means the file was moved or deleted before the tempfile
                # could unlink it.  Still sets self.file.close_called and
                # calls self.file.file.close() before the exception
                raise


def from_string_import(string):
    """
    Returns the attribute from a module, specified by a string.
    """
    module, attrib = string.rsplit('.', 1)
    return getattr(importlib.import_module(module), attrib)


def create_dirs(full_path):
    directory = os.path.dirname(full_path)
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
    if not os.path.isdir(directory):
        raise IOError("%s exists and is not a directory." % directory)
