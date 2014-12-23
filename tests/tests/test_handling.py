from django.test import TestCase

from smartfields.managers import VALUE_NOT_SET

from tests.models import HandlingTesting, InstanceHandlingTesting


class HandlingTestCase(TestCase):

    def checkAttr(self, instance, p, event, name, value):
        # check if an event handler set proper value
        self.assertEqual(getattr(instance, "%s_event" % p),
                         "%s_%s.%s=%s" % (p, event, name, value))

    def test_handlers(self):
        instance = HandlingTesting(field_1=17)
        # pre_init doesn't have access to the value yet, so it is not incremented
        self.checkAttr(instance, 'pre', 'init', 'field_1', VALUE_NOT_SET)
        self.checkAttr(instance, 'post', 'init', 'field_1', 17)
        instance.save()
        self.checkAttr(instance, 'pre', 'save', 'field_1', 117)
        self.checkAttr(instance, 'post', 'save', 'field_1', 118)
        instance.delete()
        self.checkAttr(instance, 'pre', 'delete', 'field_1', 217)
        self.checkAttr(instance, 'post', 'delete', 'field_1', 218)

    def test_instance_handlers(self):
        instance = InstanceHandlingTesting(field_1=27)
        self.checkAttr(instance, 'pre', 'init', 'field_1', VALUE_NOT_SET)
        self.checkAttr(instance, 'post', 'init', 'field_1', 270)
        instance.field_1 = 127
        instance.save()
        self.checkAttr(instance, 'pre', 'save', 'field_1', 1270)
        self.checkAttr(instance, 'post', 'save', 'field_1', 12710)
        instance.field_1 = 227
        instance.delete()
        self.checkAttr(instance, 'pre', 'delete', 'field_1', 2270)
        self.checkAttr(instance, 'post', 'delete', 'field_1', 22710)
