from django.db import models

class Model(models.Model):

    smartfields_dependant = []
    
    def __init__(self, *args, **kwargs):
        super(Model, self).__init__(*args, **kwargs)
        for field in self.smartfields_dependant:
            for d in field.dependants:
                field_file = getattr(self, field.attname)
                d.attach_file(self, field_file)
                

    class Meta:
        abstract = True