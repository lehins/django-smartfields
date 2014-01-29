import os, errno, importlib

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
