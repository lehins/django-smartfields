__all__ = [
    "ProcessingError", "BaseProcessor"
]

class ProcessingError(Exception):
    pass


class BaseProcessor(object):
    task = 'process'
    task_name = 'Processing'
    responsive = False

    def __init__(self, data):
        self.data = data

    def process(self, **kwargs):
        return self.data
