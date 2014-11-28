__all__ = [
    "ProcessingError", "BaseProcessor"
]

class ProcessingError(Exception):
    pass


class BaseProcessor(object):
    task = 'process'
    task_name = 'Processing'
    responsive = False

    def __init__(self, data, field=None, instance=None):
        self.data = data
        self.field = field
        self.instance = instance
        
    def process(self, **kwargs):
        return self.data



class Processor(object):
    task = 'process'
    task_name = 'Processing'
    progress_setter = None

    def __call__(self, value, **kwargs):
        return value

    def set_progress(self, progress):
        if callable(self.progress_setter):
            self.progress_setter(self, progress)
