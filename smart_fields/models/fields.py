from django.db.models.fields.files import ImageField


class SmartImageField(ImageField):
    def save_form_data(self, instance, data):
        if not data and not data is None:
            instance.smart_fields_cleanup(instance, self.name)
        super(self.__class__, self).save_form_data(instance, data)

