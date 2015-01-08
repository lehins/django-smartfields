import os, errno, importlib, uuid, threading

from django.core.files import base, temp
from django.utils.deconstruct import deconstructible
from django.utils.encoding import force_text
from django.utils.six.moves import queue as six_queue

__all__ = [
    'VALUE_NOT_SET', 'ProcessingError', 'NamedTemporaryFile', 'UploadTo', 
    'AsynchronousFileReader'
]

class VALUE_NOT_SET(object):
    pass


class ProcessingError(Exception):
    pass


class NamedTemporaryFile(base.File):
    """This class is required for FileStorage to make an attempt in moving the
    file, instead of copying it by chunks in memory. Borrowed implementation from
    `django.core.files.uploadedfile.TemporaryUploadedFile`

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
        self._size = self._get_size()
        try:
            return self.file.close()
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

@deconstructible
class UploadTo(object):
    """This is an upload filename generator to be used to create a function to be
    passed as an ``upload_to`` keyword argument to the ``models.FileField`` and
    it's derivatives. It will generate the path in the form:
    basefolder/app_label/model_name/parent_pk/subfolder/pk/field_name/filename.ext
    
    :keyword str basefolder: path that will be prepended to the filename.  
    
    :keyword str subfolder: path that will be a container of the model instances

    :keyword str filename: will replace the actual file name completely, ex:
    ``filename='file.ext' -> in_filename='foo.bar' -> out_filename='file.ext'``

    :keyword str name: will replace the name portion of the file, ex:
    ``name='file' -> in_filename='foo.bar' -> out_filename='file.bar'``

    :keyword str ext: will replace the extension portion of the file, ex:
    ``ext='pdf' -> in_filename='foo.bar' -> out_filename='foo.pdf'``

    :keyword str app_label: if ``None`` will insert the ``app_label`` retrieved from
    the model instance (Default). Otherwise specify a string to enforce a
    specific app_label or anything else evaluating to ``False`` except ``None`` 
    in order to skip insertion of an app_label.

    :keyword str model_name: if ``None`` will insert the ``model_name`` retrieved
    from the model instance (Default). Otherwise specify a string to enforce a
    specific model_name or anything else evaluating to ``False`` except ``None`` 
    in order to skip insertion of a model_name.

    :keyword str field_name: if ``None`` will skip insertion of a field_name
    (Default), otherwise ``field_name`` string will be inserted before the subfolder.

    :keyword function generator: function that will generate a new name portion
    of the file in case if it is set to ``True`` default generator :func:`uuid.uuid1`
    will be used.

    :keyword str parent_field_name: name of the ForeignKey or OneToOneField, that 
    is considered a parent for this field's model. Set to an empty string to ignore parent_pk

    """

    def __init__(self, basefolder=None, subfolder=None, filename=None, name=None, ext=None,
                 app_label=None, model_name=None, parent_field_name=None, field_name=None, 
                 generator=None):
        assert filename is None or name is None, \
            "Cannot have 'filename' and 'name' specified at the same time." 
        assert generator is None or (filename is None and name is None), \
            "Cannot specify a name and enforce name generation"
        assert generator is None or generator is True or callable(generator), \
            "Supply a function for a generator or set it to True to use default generator."
        self.basefolder = basefolder
        self.subfolder = subfolder
        self.filename = filename
        self.name = name
        self.ext = ext
        self.app_label = app_label
        self.model_name = model_name
        self.parent_field_name = parent_field_name
        self.field_name = field_name
        self.generator = uuid.uuid1 if generator is True else generator

    def __eq__(self, other):
        return (type(self) is type(other) and
                self.basefolder == other.basefolder and
                self.subfolder == other.subfolder and
                self.filename == other.filename and
                self.name == other.name and
                self.ext == other.ext and
                self.app_label == other.app_label and
                self.model_name == other.model_name and
                self.parent_field_name == other.parent_field_name and
                self.field_name == other.field_name and
                self.generator is other.generator)
        
    def __call__(self, instance, filename):
        structure = []
        if self.basefolder is not None:
            structure.append(self.basefolder)
        if self.app_label is None:
            structure.append(instance._meta.app_label)
        elif self.app_label:
            structure.append(self.app_label)
        if self.model_name is None:
            structure.append(instance._meta.model_name)
        elif self.model_name:
            structure.append(self.model_name)
        parent_pk = self.get_parent_pk(instance)
        if parent_pk is not None:
            structure.append(parent_pk)
        if self.subfolder is not None:
            structure.append(self.subfolder)
        if instance.pk is not None:
            structure.append(force_text(instance.pk))
        if self.field_name is not None:
            structure.append(self.field_name)
        structure.append(self.get_filename(filename))
        return os.path.join(*structure)

    def get_filename(self, filename):
        if self.filename is not None:
            filename = self.filename
        else:
            name, ext = os.path.splitext(filename)
            if ext: # remove a dot, but only if there is an extension
                ext = ext[1:]
            if self.generator is not None:
                name = self.generator()
            elif self.name is not None:
                name = self.name
            if self.ext is not None:
                ext = self.ext
            if ext:
                filename = "%s.%s" % (name, ext)
            else: 
                filename = name
        return filename

    def get_parent_pk(self, instance):
        parent_field_name = None
        if self.parent_field_name is None:
            parent_field_name = getattr(instance, 'parent_field_name', None)
        elif self.parent_field_name:
            parent_field_name = self.parent_field_name
        if parent_field_name is not None:
            parent = getattr(instance, parent_field_name)
            if parent is not None:
                return force_text(parent.pk)


class AsynchronousFileReader(threading.Thread):
    '''
    Helper class to implement asynchronous reading of a file
    in a separate thread. Pushes read lines on a queue to
    be consumed in another thread.
    source: http://stefaanlippens.net/python-asynchronous-subprocess-pipe-reading
    '''

    def __init__(self, fd, queue):
        assert isinstance(queue, six_queue.Queue)
        assert callable(fd.readline)
        super(AsynchronousFileReader, self).__init__()
        self._fd = fd
        self._queue = queue

    def run(self):
        '''The body of the tread: read lines and put them on the queue.'''
        for line in iter(self._fd.readline, ''):
            self._queue.put(line)

    def eof(self):
        '''Check whether there is no more content to expect.'''
        return not self.is_alive() and self._queue.empty()
