from django.conf import settings

if 'gis' in settings.INSTALLED_APPS:
    from django.contrib.gis.db import models
else:
    from django.db import models

from smart_fields.models.handlers import SmartFieldsHandler

__all__ = (
    "SmartFieldsBaseModel",
)


class SmartFieldsBaseModel(models.Model, SmartFieldsHandler):

    def __init__(self, *args, **kwargs):
        super(SmartFieldsBaseModel, self).__init__(*args, **kwargs)
        self.smart_fields_init()

    def save(self, old=None, *args, **kwargs):
        if old is None:
            try:
                old = self.__class__.objects.get(pk=self.pk)
            except self.__class__.DoesNotExist: pass
        self.smart_fields_presave(old)
        super(SmartFieldsBaseModel, self).save(*args, **kwargs)
        self.smart_fields_save(old)

    def delete(self, *args, **kwargs):
        self.smart_fields_delete()
        super(SmartFieldsBaseModel, self).delete(*args, **kwargs)

    class Meta:
        abstract = True
