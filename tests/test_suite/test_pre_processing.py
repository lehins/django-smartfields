from decimal import Decimal
from django.test import TestCase

from test_app.models import PreProcessorTesting

class PreProcessingTestCase(TestCase):

    def test_invalid_decimal(self):
        """
        Validate the decimal.

        Args:
            self: (todo): write your description
        """
        instance = PreProcessorTesting()
        instance.field_1 = "foo"
        self.assertEqual(instance.field_1, 0)
        self.assertEqual(instance.field_2, 1)
        instance.save()
        self.assertEqual(instance.field_1, 1)
        self.assertEqual(instance.field_2, 1)

    def test_valid_decimal(self):
        """
        Validate that the decimal field.

        Args:
            self: (todo): write your description
        """
        instance = PreProcessorTesting()
        instance.field_1 = "56.1"
        self.assertEqual(instance.field_1, Decimal('56.1'))
        self.assertEqual(instance.field_2, 57)
        instance.save()
        self.assertEqual(instance.field_1, Decimal('57.1'))
        self.assertEqual(instance.field_2, 57)

    def test_slug(self):
        """
        Test if the field is a slug.

        Args:
            self: (todo): write your description
        """
        instance = PreProcessorTesting(field_3='Foo%BAR')
        self.assertEqual(instance.field_3, 'foobar')
