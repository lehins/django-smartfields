from bs4 import BeautifulSoup, Comment

from smartfields.processors.base import BaseProcessor

__all__ = [
    "HTMLProcessor",
]

class HTMLProcessor(BaseProcessor):
    """Basic HTML processor that stripps out all the tags."""

    def remove_comments(self, soup):
        for comment in soup.findAll(text=lambda text: isinstance(text, Comment)):
            comment.extract()

    def process_tag(self, tag):
        tag.hidden = True

    def process(self, value, *args, **kwargs):
        soup = BeautifulSoup(value)
        self.remove_comments(soup)
        for tag in self.soup.findAll(True):
            self.process_tag(tag)
        return self.soup.renderContents().decode('utf8')
