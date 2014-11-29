from django.utils.text import slugify

__all__ = [
    'ProcessingError', 'BaseProcessor', 'SlugProcessor'
]

class ProcessingError(Exception):
    pass


class BaseProcessor(object):
    task = 'process'
    task_name = 'Processing'
    progress_setter = None

    def __call__(self, value, **kwargs):
        return value

    def set_progress(self, progress):
        if callable(self.progress_setter):
            self.progress_setter(self, progress)



class SlugProcessor(BaseProcessor):

    def __call__(self, value, instance=None, field=None, field_value=None, **kwargs):
        return slugify(value)
