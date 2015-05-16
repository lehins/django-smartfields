import os
from django.test import TestCase

from smartfields.utils import NamedTemporaryFile, UploadTo

from test_app.models import FileTesting

class UtilsTestCase(TestCase):

    def test_temp_file_removes(self):
        foo = NamedTemporaryFile(suffix='foo.txt', delete=True)
        full_path = foo.temporary_file_path()
        path, name = os.path.split(full_path)
        self.assertRegexpMatches(name, r'\w+foo.txt')
        foo.close()
        self.assertFalse(os.path.isfile(full_path))

    def test_temp_file_keeps(self):
        foo = NamedTemporaryFile(suffix='foo.txt', delete=False)
        full_path = foo.temporary_file_path()
        foo.close()
        self.assertTrue(os.path.isfile(full_path))
        
    def test_temp_file_removes_manually(self):
        foo = NamedTemporaryFile(suffix='foo.txt', delete=False)
        full_path = foo.temporary_file_path()
        os.remove(full_path)
        self.assertFalse(os.path.isfile(full_path))
        # although removed, shouldn't raise an error
        foo.close()

    def test_upload_to_1(self):
        upload_to = UploadTo(basefolder='base', subfolder='subfolder', name='foo', 
                             ext='txt', app_label='app_label', model_name='model_name')
        self.assertEqual(upload_to, 
                         UploadTo(basefolder='base', subfolder='subfolder', name='foo', 
                                  ext='txt', app_label='app_label', model_name='model_name'))
        instance = FileTesting()
        self.assertEqual(upload_to(instance, 'bar.jpg'), 
                         'base/app_label/model_name/subfolder/foo.txt')

    def test_upload_to_2(self):
        upload_to = UploadTo(filename='foo.txt', field_name='field_1')
        instance = FileTesting()
        instance_parent = FileTesting()
        instance_parent.pk = 45
        instance.parent_field_name = 'foo_bar'
        instance.foo_bar = instance_parent
        self.assertEqual(upload_to(instance, 'bar.jpg'), 
                         'test_app/filetesting/45/field_1/foo.txt')

    def test_upload_to_3(self):
        upload_to = UploadTo(filename='foo.txt', parent_field_name='foo_bar')
        instance = FileTesting()
        instance_parent = FileTesting()
        instance_parent.pk = 46
        instance.foo_bar = instance_parent
        self.assertEqual(upload_to(instance, 'bar.jpg'), 'test_app/filetesting/46/foo.txt')

    def test_upload_to_4(self):
        upload_to = UploadTo(name='foo', ext='')
        instance = FileTesting()
        self.assertEqual(upload_to(instance, 'bar.jpg'), 'test_app/filetesting/foo')

    def test_upload_to_5(self):
        upload_to = UploadTo(generator=lambda: 'foo')
        instance = FileTesting()
        self.assertEqual(upload_to(instance, 'bar.jpg'), 'test_app/filetesting/foo.jpg')

    def test_upload_to_6(self):
        upload_to = UploadTo(generator=True)
        instance = FileTesting()
        self.assertRegexpMatches(
            upload_to(instance, 'bar.jpg'), 
            r'test_app/filetesting/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}.jpg')
