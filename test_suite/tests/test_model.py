import os, time
from django.core.files.base import File
from django.db.models.fields.files import FileDescriptor
from django.test import TestCase
from django.utils import six

from smartfields.models import SmartfieldsModelMixin

from sample_app.models import ProcessingTesting


class ProcessingTestCase(TestCase):

    def test_model_setup(self):
        instance = ProcessingTesting()
        self.assertIsInstance(instance, SmartfieldsModelMixin)
        self.assertIsNotNone(getattr(instance, '_smartfields_managers', None))

    def _test_individual_field_processing(self):
        instance = ProcessingTesting(field_1=six.text_type('foo bar'))
        instance.smartfields_process(field_names=['field_3'])
        self.assertEqual(instance.field_2, "")
        self.assertEqual(instance.field_3, "foo-bar")
        self.assertEqual(instance.field_4, "foo-bar")
        # also tests SlugProcessor
        instance.smartfields_process(field_names=['field_1'])
        self.assertEqual(instance.field_1, "Foo_Bar")
        self.assertEqual(instance.field_2, "foo-bar")
        self.assertEqual(instance.field_3, "foo-bar")

    def _test_processing_order(self):
        instance = ProcessingTesting(field_1=six.text_type('foo bar'))
        instance.smartfields_process(field_names=['field_1', 'field_3'])
        self.assertEqual(instance.field_1, "Foo_Bar")
        self.assertEqual(instance.field_2, "foo-bar")
        self.assertEqual(instance.field_3, "foo_bar")
        instance = ProcessingTesting(field_1=six.text_type('foo bar'))
        instance.smartfields_process(field_names=['field_3', 'field_1'])
        self.assertEqual(instance.field_1, "Foo_Bar")
        self.assertEqual(instance.field_2, "foo-bar")
        self.assertEqual(instance.field_3, "foo-bar") # different then above: _

