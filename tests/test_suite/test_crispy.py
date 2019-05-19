import re
from django.test import TestCase
from django.template import Context

from test_app.forms import TextTestingForm, ImageTestingForm, VideoTestingForm

from crispy_forms.templatetags.crispy_forms_tags import CrispyFormNode

class CripsyTestCase(TestCase):

    def render_form(self, form):
        node = CrispyFormNode('form', 'helper')
        f = node.render(Context({'form': form, 'helper': form.helper}))
        f = re.sub('( +|\t+|\n+)', ' ', f)
        return f

    def test_text_field(self):
        form = TextTestingForm()
        self.assertIn(len(self.render_form(form)), range(365, 375))

    def test_image_field(self):
        form = ImageTestingForm()
        self.assertIn(len(self.render_form(form)), range(1009, 1034))

    def test_video_field(self):
        form = VideoTestingForm()
        self.assertIn(len(self.render_form(form)), range(954, 964))
