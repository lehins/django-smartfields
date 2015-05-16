import os, shutil
from django.core.files.base import File
from django.conf import settings
from django.test import TestCase
from django.utils.encoding import force_bytes

from test_app.models import FileTesting, ImageTesting, DependencyTesting, RenameFileTesting


def add_base(path):
    return os.path.join(settings.BASE_PATH, path)


class FileBaseTestCase(TestCase):
    media_path = add_base("media")

    def setUp(self):
        if not os.path.exists(self.media_path): os.makedirs(self.media_path)

    def tearDown(self):
        if os.path.exists(self.media_path): shutil.rmtree(self.media_path)
        pass

class FileTestCase(FileBaseTestCase):

    def test_file_field(self):
        instance = FileTesting.objects.create()
        # test default static
        self.assertEqual(instance.field_1_foo.url, "/static/defaults/foo.txt")
        self.assertEqual(instance.bar.url, "/static/defaults/bar.txt")
        # test default FieldFile set and processed
        self.assertEqual(instance.field_1_foo.read(), force_bytes("FOO\n"))
        self.assertEqual(instance.bar.read(), force_bytes("BAR\n"))
        self.assertEqual(instance.field_2.read(), force_bytes("foo\n"))
        field_2_path = instance.field_2.path
        self.assertTrue(os.path.isfile(field_2_path))
        # test assignment of file
        foo_bar = File(open(add_base("static/defaults/foo-bar.txt"), 'r'))
        instance.field_1 = foo_bar
        instance.save()
        foo_bar.close()
        # make sure default file was not removed
        self.assertTrue(os.path.isfile(field_2_path))
        # check new content
        self.assertEqual(instance.field_1.read(), force_bytes("FOO BAR\n"))
        self.assertEqual(instance.field_1_foo.read(), force_bytes("FOO BAR\n"))
        instance.field_2.seek(0)
        self.assertEqual(instance.field_2.read(), force_bytes("foo\n"))
        # testing setting default value again
        instance.field_2 = None
        instance.save()
        # make sure previous file was removed
        self.assertFalse(os.path.isfile(field_2_path))
        self.assertEqual(instance.field_2.read(), force_bytes("foo bar\n"))
        # test deletion of file together with instance
        field_1_path = instance.field_1.path
        field_1_foo_path = instance.field_1_foo.path
        field_2_path = instance.field_2.path
        self.assertTrue(os.path.isfile(field_1_path))
        self.assertTrue(os.path.isfile(field_1_foo_path))
        self.assertTrue(os.path.isfile(field_2_path))
        instance.delete()
        self.assertFalse(os.path.isfile(field_1_path))
        self.assertFalse(os.path.isfile(field_1_foo_path))
        self.assertFalse(os.path.isfile(field_2_path))
        
    def test_file_cleanup_after_delete(self):
        instance = FileTesting.objects.create()
        foo_bar = File(open(add_base("static/defaults/foo-bar.txt"), 'r'))
        instance.field_3 = foo_bar
        instance.field_4 = foo_bar
        instance.save()
        foo_bar.close()
        field_3_path = instance.field_3.path
        field_4_path = instance.field_4.path
        self.assertTrue(os.path.isfile(field_3_path))
        self.assertTrue(os.path.isfile(field_4_path))
        instance.delete()
        # testing cleanup without dependencies
        self.assertFalse(os.path.isfile(field_3_path))
        # testing keep_orphans=True
        self.assertTrue(os.path.isfile(field_4_path))

    def test_file_cleanup_after_replace(self):
        instance = FileTesting.objects.create()
        foo_bar = File(open(add_base("static/defaults/foo-bar.txt"), 'r'))
        instance.field_3 = foo_bar
        instance.field_4 = foo_bar
        instance.save()
        foo_bar.close()
        field_3_path = instance.field_3.path
        field_4_path = instance.field_4.path
        self.assertTrue(os.path.isfile(field_3_path))
        self.assertTrue(os.path.isfile(field_4_path))
        foo = File(open(add_base("static/defaults/foo.txt"), 'r'))
        instance.field_3 = foo
        instance.field_4 = foo
        instance.save()
        foo.close()
        # testing cleanup without dependencies
        self.assertFalse(os.path.isfile(field_3_path))
        # testing keep_orphans=True
        self.assertTrue(os.path.isfile(field_4_path))


class ImageTestCase(FileBaseTestCase):

    def test_image_field_mimic_django(self):
        instance = ImageTesting.objects.create()
        lenna_rect = File(open(add_base("static/images/lenna_rect.jpg"), 'rb'))
        instance.image_1 = lenna_rect
        instance.image_2 = lenna_rect
        instance.save()
        lenna_rect.close()
        # make sure width and heigth values are correct and same as django's
        self.assertEqual(instance.image_1_width, instance.image_2_width)
        self.assertEqual(instance.image_1_height, instance.image_2_height)
        self.assertEqual(instance.image_2_width, 400)
        self.assertEqual(instance.image_2_height, 225)
        # make sure values are saved properly
        instance = ImageTesting.objects.get(pk=instance.pk)
        self.assertEqual(instance.image_2_width, 400)
        self.assertEqual(instance.image_2_height, 225)
        # make sure image is still there and can properly retrieve dims
        self.assertEqual(instance.image_2.width, 400)
        self.assertEqual(instance.image_2.height, 225)
        self.assertEqual(instance.image_1.url, "/media/image_1/lenna_rect.jpg")
        self.assertEqual(instance.image_2.url, "/media/image_2/lenna_rect.jpg")
        # test image replacing
        lenna_square = File(open(add_base("static/images/lenna_square.png"), 'rb'))
        instance.image_2 = lenna_square
        self.assertTrue(os.path.isfile(add_base("media/image_2/lenna_rect.jpg")))
        instance.save()
        lenna_square.close()
        self.assertFalse(os.path.isfile(add_base("media/image_2/lenna_rect.jpg")))
        self.assertEqual(instance.image_2.width, 512)
        self.assertEqual(instance.image_2.height, 512)
        instance.image_2 = None
        instance.save()
        self.assertIsNone(instance.image_2_width)
        self.assertIsNone(instance.image_2_height)
        # remove django's ImageFieldFile manually
        instance.image_1.delete()
        instance.delete()
        self.assertFalse(os.path.isfile(add_base("media/image_2/lenna_square.png")))

    def test_wand_image_processor(self):
        instance = ImageTesting.objects.create()
        lenna_square = File(open(add_base("static/images/lenna_square.png"), 'rb'))
        instance.image_5 = lenna_square
        instance.save()
        # make sure conversion went through properly
        self.assertEquals(instance.image_5_jpeg.width, 150)
        self.assertEquals(instance.image_5_jpeg.height, 150)
        # save instance, so files get commited to storage
        path = instance.image_5.path
        path_jpeg = instance.image_5_jpeg.path
        # check to see that files got commited
        self.assertTrue(os.path.isfile(path))
        self.assertTrue(os.path.isfile(path_jpeg))

    def test_image_processor(self):
        instance = ImageTesting.objects.create()
        lenna_rect = File(open(add_base("static/images/lenna_rect.jpg"), 'rb'))
        instance.image_3 = lenna_rect
        instance.save()
        # make sure conversion went through properly
        self.assertEquals(instance.image_3_png.width, 200)
        self.assertEquals(instance.image_3_png.height, 112)
        # save instance, so files get commited to storage
        path = instance.image_3.path
        path_png = instance.image_3_png.path
        # check to see that files got commited
        self.assertTrue(os.path.isfile(path))
        self.assertTrue(os.path.isfile(path_png))
        # make sure dependency gets reattached as expected
        instance = ImageTesting.objects.get(pk=instance.pk)
        self.assertEquals(instance.image_3_png.width, 200)
        self.assertEquals(instance.image_3_png.height, 112)
        self.assertTrue(os.path.isfile(path))
        self.assertTrue(os.path.isfile(path_png))
        # test problematic processor (JPEG2000 is missing a required library)
        instance.image_4 = lenna_rect
        instance.save()
        self.assertEqual(instance.smartfields_get_field_status('image_4'), {
            'state': 'error', 
            'messages': [
                'ProcessingError: There was a problem with image conversion: encoder '
                'jpeg2k not available'
            ], 
            'app_label': 'test_app', 
            'pk': 1, 
            'field_name': 'image_4', 
            'model_name': 'imagetesting'
        })
        lenna_rect.close()
        # delete instance and check if everything is cleaned up
        instance.delete()
        self.assertFalse(os.path.isfile(path))
        self.assertFalse(os.path.isfile(path_png))

    def test_self_dependency(self):
        instance = DependencyTesting.objects.create()
        lenna_rect = File(open(add_base("static/images/lenna_rect.jpg"), 'rb'))
        instance.image_1 = lenna_rect
        instance.save()
        lenna_rect.close()
        self.assertEqual(instance.image_1.width, 50)
        self.assertEqual(
            instance.image_1.url,
            "/media/test_app/dependencytesting/%s/image_1.bmp" % instance.pk)
        self.assertEqual(instance.image_1_gif.width, 50)
        self.assertEqual(
            instance.image_1_gif.url,
            "/media/test_app/dependencytesting/%s/image_1_gif.gif" % instance.pk)
        instance.delete()

    def test_value_restoration_1(self):
        lenna_rect = File(open(add_base("static/images/lenna_rect.jpg"), 'rb'))
        text_file = File(open(add_base("static/defaults/foo.txt"), 'rb'))
        instance = DependencyTesting.objects.create()
        instance.image_1 = lenna_rect
        instance.save()
        lenna_rect.close()
        image_1 = instance.image_1
        image_1_gif = instance.image_1_gif
        instance.image_1 = text_file
        instance.save()
        text_file.close()
        self.assertIs(instance.image_1, image_1)
        self.assertIs(instance.image_1_gif, image_1_gif)
        instance.delete()

    def test_value_restoration_2(self):
        lenna_rect = File(open(add_base("static/images/lenna_rect.jpg"), 'rb'))
        text_file = File(open(add_base("static/defaults/foo.txt"), 'rb'))
        instance = DependencyTesting.objects.create()
        instance.image_2 = lenna_rect
        instance.save()
        lenna_rect.close()
        image_3 = instance.image_3
        image_4 = instance.image_4
        # restores values since new file is a text file that cannot be processed
        instance.image_2 = text_file
        instance.save()
        text_file.close()
        self.assertEqual(instance.image_3, image_3)
        self.assertEqual(instance.image_4, image_4)
        self.assertEqual(instance.image_3.path, image_3.path)
        self.assertEqual(instance.image_4.path, image_4.path)
        instance.delete()

    def test_forward_dependency(self):
        instance = DependencyTesting.objects.create()
        lenna_rect = File(open(add_base("static/images/lenna_rect.jpg"), 'rb'))
        instance.image_3 = lenna_rect
        instance.image_4 = lenna_rect
        instance.save()
        image_3_path = instance.image_3.path
        image_4_path = instance.image_4.path
        self.assertEqual(instance.image_3.width, 400)
        self.assertEqual(instance.image_4.width, 400)
        self.assertEqual(
            instance.image_3.url,
            "/media/test_app/dependencytesting/%s/image_3.jpg" % instance.pk)
        self.assertEqual(
            instance.image_4.url,
            "/media/test_app/dependencytesting/%s/image_4.jpg" % instance.pk)
        instance.image_2 = lenna_rect
        self.assertTrue(os.path.isfile(image_3_path))
        self.assertTrue(os.path.isfile(image_4_path))
        instance.save()
        lenna_rect.close()
        self.assertEqual(instance.image_3.width, 100)
        self.assertEqual(instance.image_4.width, 150)
        # forward dependencies on django's FileFields will also do the cleanup
        self.assertFalse(os.path.isfile(image_3_path))
        self.assertFalse(os.path.isfile(image_4_path))
        instance.delete()

    def test_dependency_error(self):
        instance = ImageTesting()
        image_1 = instance._meta.get_field('image_1')
        image_2 = instance._meta.get_field('image_2')
        self.assertRaises(AssertionError, image_2.manager.dependencies[0].set_field, image_1)


    def test_rename_file_testing(self):
        instance = RenameFileTesting()
        lenna = File(open(add_base("static/images/lenna_rect.jpg"), 'rb'))
        instance.label = 'foo'
        instance.dynamic_name_file = lenna
        instance.save()
        self.assertEqual(instance.dynamic_name_file.url,
                         "/media/test_app/renamefiletesting/foo.jpg")
        foo_path = instance.dynamic_name_file.path
        self.assertTrue(os.path.isfile(foo_path))
        instance.label = "bar"
        instance.save()
        self.assertEqual(instance.dynamic_name_file.url,
                         "/media/test_app/renamefiletesting/bar.jpg")
        bar_path = instance.dynamic_name_file.path
        self.assertNotEqual(foo_path, bar_path)
        self.assertFalse(os.path.isfile(foo_path))
        self.assertTrue(os.path.isfile(bar_path))
        instance.delete()
        self.assertFalse(os.path.isfile(bar_path))
