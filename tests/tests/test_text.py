import re
from django.test import TestCase
from django.db.utils import IntegrityError

from smartfields.models import SmartfieldsModelMixin

from tests.models import TextTesting
from tests.tests.test_files import add_base


class TextTestCase(TestCase):

    def setUp(self):
        descr = open(add_base("static/defaults/snatch.html"), 'r')
        TextTesting.objects.create(title='Snatch', summary=descr.read())
        descr.close()
        descr = open(add_base("static/defaults/lord_of_war.html"), 'r')
        i = TextTesting.objects.create(title='Lord of War', summary=descr.read())
        descr.close()

    def test_model_setup(self):
        instance = TextTesting()
        self.assertIsInstance(instance, SmartfieldsModelMixin)
        self.assertIsNotNone(getattr(instance, '_smartfields_managers', None))
        self.assertTrue(getattr(instance, 'smartfields_managers', None))

    def test_html(self):
        instance = TextTesting.objects.get(title='Snatch')
        descr_plain = open(add_base("static/defaults/snatch.txt"), 'r')
        self.assertEqual(instance.summary_plain, descr_plain.read())
        descr_plain.close()
        instance = TextTesting.objects.get(title='Lord of War')
        descr_plain = open(add_base("static/defaults/lord_of_war.txt"), 'r')
        self.assertEqual(instance.summary_plain, descr_plain.read())
        descr_plain.close()

    def test_cropping(self):
        instance = TextTesting.objects.get(title='Snatch')
        self.assertEqual(len(instance.summary_beginning), 100)
        self.assertEqual(instance.summary_beginning, instance.summary_plain[:100])
        instance = TextTesting.objects.get(title='Lord of War')
        self.assertEqual(len(instance.summary_beginning), 100)
        self.assertEqual(instance.summary_beginning, instance.summary_plain[:100])

    def test_slug(self):
        # make sure slug is in lower case and cropped
        instance = TextTesting.objects.get(title='Snatch')
        #self.assertEqual(instance.slug, 'snatch')
        instance = TextTesting.objects.get(title='Lord of War')
        self.assertEqual(instance.slug, 'lord-of-w')

    def test_unique(self):
        instance = TextTesting.objects.create(title='Snatch')
        self.assertRegexpMatches(instance.title, re.compile(r'Snatch\d{1,5}'))
        self.assertRegexpMatches(instance.slug, re.compile(r'snatch-\d{1,2}'))
        for n in range(10):
            # make sure it will use up allpossible values
            # although it is possible it will exhaust all 100 tries, chance
            # of it happenning is almost non-existent
            instance = TextTesting.objects.create(title='Lord of War')
            self.assertRegexpMatches(instance.title, re.compile(r'Lord of Wa\d'))
            self.assertRegexpMatches(instance.slug, re.compile(r'lord-of-\d'))
        # make sure infinite loop is impossible
        self.assertRaises(IntegrityError, TextTesting.objects.create, title='Lord of War')
