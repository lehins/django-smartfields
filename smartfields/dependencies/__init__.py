

class Dependency(object):

    def __init__(self, field_name=None, attname=None, suffix=None, processor=None,
                 async=False, handler=None, pre_init=None, post_init=None,
                 pre_save=None, post_save=None, pre_delete=None, post_delete=None,
                 processor_kwargs=None):
        """if field_name is None and attname or suffix are also None, this
        dependency becomes a forward dependency. All async=True will run last.

        """
        self._field_name = field_name
        assert attname is None or suffix is None, \
            "It is invalid to set both attname and suffix at the same time."
        self._attname = attname
        self._suffix = suffix
        self._processor = processor
        # check if this field depends on itself or another field.
        is_dependent = field_name is not None or (attname is None and suffix is None)
        self.async = async
        assert not self.async or is_dependent, \
            "Asynchronous processing is not possible when field depends on other values."
        self._handler = handler
        self._pre_init, self._post_init = pre_init, post_init
        self._pre_save, self._post_save = pre_save, post_save
        self._pre_delete, self._post_delete = pre_delete, post_delete
        self._processor_kwargs = processor_kwargs or {}


    def handle(self, instance, field, field_value, event):
        if self._field_name is not None:
            value = getattr(instance, self._field_name)
        else:
            value = field_value
        custom_event_handler = getattr(self, "_%s" % event, None)
        if callable(custom_event_handler):
            new_value = custom_event_handler(value, instance, field, field_value)
            if new_value is not None:
                value = new_value
        event_handler = getattr(self, event, None)
        if callable(event_handler):
            event_handler(value, instance, field, field_value)


    def attach_dependency(self, value, instance, field, field_value, attname=None):
        attname = attname or self._attname
        if not attname and self._suffix:
            attname = "%s_%s" % (field.name, self._suffix)
        else:
            attname = field.attname
        setattr(instance, attname, value)


    def post_init(self, value, instance, field, field_value):
        # make sure all dependencies are initialized together with the model
        self.attach_dependency(value, instance, field, field_value)


    def pre_save(self, value, instance, field, field_value):
        # make sure all dependencies are attached before saving the model
        self.attach_dependency(value, instance, field, field_value)


    def process(self, instance, field, field_value, progress_setter=None):
        if self._field_name is not None:
            value = getattr(instance, self._field_name)
        else:
            value = field_value
        if callable(self._processor):
            if self.async:
                self._processor.progress_setter = progress_setter
                progress_setter(self._processor, 0)
            value = self._processor(
                value, instance=instance, field=field, field_value=field_value, 
                **self._processor_kwargs
            )
            if self.async:
                self._processor.progress_setter = None
                progress_setter(self._processor, 0)
        self.attach_dependency(value, instance, field, field_value)
        return value