from django.test import TestCase

from smartfields.processors import ImageProcessor, ImageFormat

class ImageProcessorsTestCase(TestCase):

    def test_dimensions_scaling(self):
        p = ImageProcessor()
        # scaling up: hard set dims
        self.assertEqual(p.get_dimensions(200, 100, width=100), (100, 50))
        self.assertEqual(p.get_dimensions(200, 100, height=200), (400, 200))
        # scaling up: single
        self.assertEqual(p.get_dimensions(200, 100, min_width=300), (300, 150))
        self.assertEqual(p.get_dimensions(200, 100, min_height=200), (400, 200))
        # scaling up: both
        self.assertEqual(p.get_dimensions(200, 100, min_width=300, min_height=200), (400, 200))
        self.assertEqual(p.get_dimensions(200, 100, min_width=600, min_height=200), (600, 300))
        # scaling up: mixing
        self.assertEqual(p.get_dimensions(200, 100, min_width=300, max_width=400), (300, 150))
        self.assertEqual(p.get_dimensions(200, 100, min_height=200, max_height=400), (400, 200))
        # scaling down: single
        self.assertEqual(p.get_dimensions(200, 100, max_width=50), (50, 25))
        self.assertEqual(p.get_dimensions(200, 100, max_height=25), (50, 25))
        # scaling down: both
        self.assertEqual(p.get_dimensions(200, 100, max_width=100, max_height=75), (100, 50))
        self.assertEqual(p.get_dimensions(200, 100, max_width=150, max_height=50), (100, 50))
        # scaling down: mixin
        self.assertEqual(p.get_dimensions(200, 100, min_width=50, max_width=100), (100, 50))
        self.assertEqual(p.get_dimensions(200, 100, min_height=10, max_height=50), (100, 50))
        # no scaling: single
        self.assertEqual(p.get_dimensions(200, 100, min_width=100), (200, 100))
        self.assertEqual(p.get_dimensions(200, 100, min_height=50), (200, 100))
        self.assertEqual(p.get_dimensions(200, 100, max_width=300), (200, 100))
        self.assertEqual(p.get_dimensions(200, 100, max_height=150), (200, 100))
        # no scaling: both
        self.assertEqual(p.get_dimensions(200, 100, min_width=50, min_height=50), (200, 100))
        self.assertEqual(p.get_dimensions(200, 100, max_width=400, max_height=200), (200, 100))
        # without preserving ratio
        self.assertEqual(p.get_dimensions(
            200, 100, min_width=50, max_width=100, min_height=2000, 
            max_height=2001, preserve=False), (100, 2000))
        self.assertEqual(p.get_dimensions(
            200, 100, height=500, min_width=300, max_width=400, preserve=False), (300, 500))

    def test_dimensions_checking(self):
        p = ImageProcessor()
        # ones that totally don't make sense
        self.assertRaises(AssertionError, p._check_scale_params, width=100, min_width=50)
        self.assertRaises(AssertionError, p._check_scale_params, width=100, max_width=50)
        self.assertRaises(AssertionError, p._check_scale_params, height=50, min_height=50)
        self.assertRaises(AssertionError, p._check_scale_params, height=50, max_height=50)
        self.assertRaises(AssertionError, p._check_scale_params, min_width=100, max_width=50)
        self.assertRaises(AssertionError, p._check_scale_params, min_height=100, max_height=50)
        # ones that make no sense with preserve=True
        self.assertRaises(AssertionError, p._check_scale_params, width=100, height=50)
        self.assertRaises(AssertionError, p._check_scale_params, width=100, min_height=50)
        self.assertRaises(AssertionError, p._check_scale_params, width=100, max_height=50)
        self.assertRaises(AssertionError, p._check_scale_params, height=50, min_width=50)
        self.assertRaises(AssertionError, p._check_scale_params, height=50, min_height=50)
        self.assertRaises(AssertionError, p._check_scale_params, min_width=100, max_height=50)
        self.assertRaises(AssertionError, p._check_scale_params, max_width=100, min_height=50)

    def test_misc(self):
        f1 = ImageFormat('BMP', ext='dib')
        f2 = ImageFormat('BMP')
        f3 = ImageFormat('PSD')
        self.assertEqual(f1, f2)
        self.assertEqual(f1, 'BMP')
        self.assertNotEqual(f1, f3)
        self.assertTrue(f1.can_read)
        self.assertEqual(f1.get_ext(), 'dib')
        self.assertEqual(f2.get_ext(), 'bmp')
        self.assertEqual(f1.get_exts(), 'bmp,dib')
        self.assertEqual(f1.get_mode(), 'RGB')
        self.assertEqual(f1.get_mode(old_mode='non_existent'), 'RGB')
        self.assertEqual(f1.get_mode(old_mode='CMYK'), 'RGB')
        self.assertEqual(f1.get_mode(old_mode='LA'), 'P')
        p = ImageProcessor(format=f3)
        self.assertRaises(AssertionError, p.check_params)
        self.assertEqual(set(p.supported_formats.input_exts.split(',')),
                         set('sgi,pcx,xpm,tif,tiff,jpg,jpe,jpeg,jfif,xbm,gif,bmp,dib,tga,'
                         'tpic,im,psd,ppm,pgm,pbm,png'.split(',')))
        p = ImageProcessor()
        self.assertIsNone(p.get_ext())
        self.assertEquals(p.get_ext(format=ImageFormat('TIFF', ext='')), '')

        
