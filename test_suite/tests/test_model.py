from django.test import TestCase
from sample_app.models import Movie

class AnimalTestCase(TestCase):

    def test_model_init(self):
        movie = Movie.objects.create(title="snatch")
        self.assertIsInstance(movie, ModelMixin)
        self.assertIsNotNone(getattr(movie, 'smartfields_managers', None))