import re
#from BeautifulSoup import BeautifulSoup, Comment
from bs4 import BeautifulSoup, Comment # problem with mod_wsgi seems to be fixed
from django.conf import settings

from smartfields.processors.base import BaseProcessor

__all__ = [
    "HTMLStripper", "HTMLSanitizer"
]


VALID_TAGS = set(getattr(settings, 'SMARTFIELDS_VALID_TAGS', 'div p i strong'
                      ' em s b u a h1 h2 h3 blockquote br ul ol li img').split())
VALID_ATTRS = set(getattr(settings, 'SMARTFIELDS_VALID_ATTRS',
                       'href src width height').split())


class HTMLStripper(BaseProcessor):

    def remove_comments(self):
        for comment in self.soup.findAll(text=lambda text: isinstance(text, Comment)):
            comment.extract()


    def process_tag(self, tag):
        tag.hidden = True


    def process(self, **kwargs):
        self.soup = BeautifulSoup(self.data)
        self.remove_comments()
        for tag in self.soup.findAll(True):
            self.process_tag(tag)
        return self.soup.renderContents().decode('utf8')



class HTMLSanitizer(HTMLStripper):

    def __init__(self, data):
        rjs = r'[\s]*(&#x.{1,7})?'.join(list('javascript:'))
        rvb = r'[\s]*(&#x.{1,7})?'.join(list('vbscript:'))
        self.re_scripts = re.compile('(%s)|(%s)' % (rjs, rvb), re.IGNORECASE)
        super(HTMLSanitizer, self).__init__(data)


    def process_tag(self, tag):
        if tag.name not in self.valid_tags:
            tag.hidden = True
        else:
            attrs = tag.attrs
            tag.attrs = {}
            for attr, val in attrs.iteritems():
                if attr in self.valid_attrs:
                    new_val = self.re_scripts.sub('', val) # Remove scripts (vbs & js)
                    while new_val != val:
                        val = new_val
                        new_val = self.re_scripts.sub('', val)
                    tag.attrs[attr] = val


    def process(self, valid_tags=None, valid_attrs=None, **kwargs):
        self.valid_tags = valid_tags or VALID_TAGS
        self.valid_attrs = valid_attrs or VALID_ATTRS
        return super(HTMLSanitizer, self).process(**kwargs)
