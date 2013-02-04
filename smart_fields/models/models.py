from django.db import models

from smart_fields.models.handlers import SmartFieldsHandler

__all__ = (
    "SmartFieldsBaseModel",
)

class SmartFieldsBaseModel(models.Model, SmartFieldsHandler):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.smart_fields_init()

    def save(self, old=None, *args, **kwargs):
        try:
            old = self.__class__.objects.get(pk=self.pk)
        except self.__class__.DoesNotExist: pass
        super(self.__class__, self).save(*args, **kwargs)
        self.smart_fields_save(old)

    def delete(self, *args, **kwargs):
        self.smart_fields_delete()
        super(self.__class__, self).delete(*args, **kwargs)

    class Meta:
        abstract = True
