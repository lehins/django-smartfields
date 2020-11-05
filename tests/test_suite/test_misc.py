from django.test import TestCase

from smartfields.dependencies import FileDependency

class MiscTestCase(TestCase):

    def test_file_dependency(self):
        """
        Uploads the dependencies of the dependencies.

        Args:
            self: (todo): write your description
        """
        self.assertEqual(
            FileDependency(storage='foo', upload_to='somewhere', keep_orphans=True),
            FileDependency(storage='foo', upload_to='somewhere', keep_orphans=True)
        )