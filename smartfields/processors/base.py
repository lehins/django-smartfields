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
