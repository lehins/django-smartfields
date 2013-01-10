from django.db.models.fields.files import FileField, ImageField

__all__ = (
    "SmartImageField", "SmartImageField", "SmartAudioField", "SmartVideoField",
    "SmartPdfField",
)


def save_form_data(self, instance, data):
    if not data and not data is None:
        instance.smart_fields_cleanup(instance, self.name)
    super(self.__class__, self).save_form_data(instance, data)


class SmartFileField(FileField):
    save_form_data = save_form_data


class SmartImageField(ImageField):
    save_form_data = save_form_data


class SmartPdfField(SmartFileField):
    pass

class SmartAudioField(SmartFileField):
    pass

class SmartVideoField(SmartFileField):
    pass
