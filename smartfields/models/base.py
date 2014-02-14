from django.db import models

class Model(models.Model):

    smartfields_dependencies = []
    
    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super(Model, self).__init__(*args, **kwargs)
        for field in self.smartfields_dependencies:
            for d in field.dependencies:
                d.handle_dependency(self, field)


    def save(self, *args, **kwargs):
        for field in self.smartfields_dependencies:
            for d in field.dependencies:
                d.handle_dependency(self, field)
        super(Model, self).save(*args, **kwargs)

