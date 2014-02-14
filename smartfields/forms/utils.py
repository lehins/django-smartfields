import copy, json
from django.utils import six


class AttrsDict(dict):
    """None values don't make sence in HTML attributes, so we will exploit this to
    remove particular items or completely clear out the dictionary.

    """

    def __init__(self, mapping=(), **kwargs):
        if isinstance(mapping, dict):
            mapping = mapping.iteritems()
        if mapping:
            for key, value in mapping:
                self[key] = value
        for key, value in kwargs.iteritems():
            self[key] = value

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__,
                             super(AttrsDict, self).__repr__())

    def __getitem__(self, key):
        value = super(AttrsDict, self).__getitem__(key)
        if key == 'class' and value:
            value = ' '.join(value)
        elif key == 'style':
            values = [':'.join(x) for x in value.iteritems()]
            value = ';'.join(values) + ';'
        return value
        
    def __setitem__(self, key, value):
        if value is None:
            try:
                if key.startswith('data-'):
                    sub_key = key[5:]
                    del super(AttrsDict, self).__getitem__('data')[sub_key]
                else:
                    super(AttrsDict, self).__delitem__(key)
            except KeyError: pass
        else:
            try:
                old_value = super(AttrsDict, self).__getitem__(key)
            except KeyError:
                old_value = None
            if key == 'class':
                old_value = old_value or set()
                if isinstance(value, basestring):
                    value = value.split()
                super(AttrsDict, self).__setitem__(key, old_value.union(value))
            elif key  == 'style':
                old_value = old_value or {}
                if isinstance(value, basestring):
                    value = dict([x.split(':') for x in value.split(';') if x])
                for sub_key, sub_value in value.iteritems():
                    old_value[sub_key] = sub_value
                    if sub_value is None:
                        del old_value[sub_key]
                super(AttrsDict, self).__setitem__(key, old_value)
            elif key == 'data':
                for sub_key, sub_value in value.iteritems():
                    new_key = "%s-%s" % (key, sub_key)
                    self[new_key] = sub_value
                    if sub_value is None:
                        del self[new_key]
                super(AttrsDict, self).__setitem__(key, old_value)
            else:
                super(AttrsDict, self).__setitem__(key, value)

    def __copy__(self):
        return self.__class__(super(AttrsDict, self).copy())

    def __deepcopy__(self, memo=None):
        if memo is None:
            memo = {}
        result = self.__class__()
        memo[id(self)] = result
        for key, value in dict.items(self):
            dict.__setitem__(result, copy.deepcopy(key, memo),
                             copy.deepcopy(value, memo))
        return result

    def copy(self):
        """Returns a shallow copy of this object."""
        return copy.copy(self)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def getattr(self, key, default=None):
        try:
            return super(AttrsDict, self).get(key, default)
        except KeyError:
            return default
            

    def _iteritems(self):
        for key in self:
            yield key, self[key]

    def _itervalues(self):
        for key in self:
            yield self[key]

    if six.PY3:
        items = _iteritems
        values = _itervalues
    else:
        iteritems = _iteritems
        itervalues = _itervalues

        def items(self):
            return list(self.iteritems())

        def values(self):
            return list(self.itervalues())

    def update(self, *args, **kwargs):
        if len(args) > 1:
            raise TypeError("update expected at most 1 arguments, got %d" % len(args))
        if args:
            other_dict = args[0]
            for key in other_dict:
                self[key] = other_dict[key]
        for key, value in six.iteritems(kwargs):
            self[key] = value