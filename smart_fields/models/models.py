from django.db import models

from smart_fields.models.handlers import SmartFieldsHandler

__all__ = (
    "SmartFieldsBaseModel",
)

class SmartFieldsBaseModel(models.Model, SmartFieldsHandler):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.smart_fields_init()

    def save(self, *args, **kwargs):
        try:
            old = self.__class__.objects.get(pk=self.pk)
        except self.__class__.DoesNotExist:
            old = None
        super(self.__class__, self).save(*args, **kwargs);
        self.smart_fields_save(old)
    
    class Meta:
        abstract = True
