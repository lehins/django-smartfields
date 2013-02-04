from django.utils import six
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

def format_html(format_string, *args, **kwargs):
    """
    Similar to str.format, but passes all arguments through conditional_escape,
    and calls 'mark_safe' on the result. This function should be used instead
    of str.format or % interpolation to build up small HTML fragments.
    """
    args_safe = map(conditional_escape, args)
    kwargs_safe = dict([(k, conditional_escape(v)) for (k, v) in
                        six.iteritems(kwargs)])
    return mark_safe(format_string.format(*args_safe, **kwargs_safe))
