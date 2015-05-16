from django.test import TestCase

from smartfields.fields import FileField, ImageField

class ReconstructionTestCase(TestCase):

    def test_file_field(self):
        old_field = FileField()
        name, path, args, kwargs = old_field.deconstruct()
        new_field = FileField(*args, **kwargs)
        self.assertEqual(old_field._dependencies, new_field._dependencies)

    def test_image_field(self):
        old_field = ImageField()
        name, path, args, kwargs = old_field.deconstruct()
        new_field = ImageField(*args, **kwargs)
        self.assertEqual(old_field._dependencies, new_field._dependencies)
        old_field = ImageField(width_field='width', height_field='height')
        name, path, args, kwargs = old_field.deconstruct()
        new_field = ImageField(*args, **kwargs)
        self.assertEqual(old_field._dependencies, new_field._dependencies)