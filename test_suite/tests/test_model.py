from django.test import TestCase

from smartfields.models import SmartfieldsModelMixin

from sample_app.models import ProcessorTestingModel


class ProcessingTestCase(TestCase):

    def test_model_setup(self):
        instance = ProcessorTestingModel()
        self.assertIsInstance(instance, SmartfieldsModelMixin)
        self.assertIsNotNone(getattr(instance, '_smartfields_managers', None))

    def test_individual_field_processing(self):
        instance = ProcessorTestingModel(field_1=u'foo bar')
        self.assertEquals(instance.field_3, "")
        # also tests SlugProcessor
        instance.smartfields_process(field_names=['field_3'])
        self.assertEquals(instance.field_2, "")
        self.assertEquals(instance.field_3, "foo-bar")

    def test_processing_order(self):
        instance = ProcessorTestingModel(field_1=u'foo bar')
        instance.smartfields_process()
        self.assertEquals(instance.field_1, "Foo_Bar")
        self.assertEquals(instance.field_2, "foo-bar")
        self.assertEquals(instance.field_3, "foo_bar")
