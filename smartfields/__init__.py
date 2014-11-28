from smartfields.fields import *
from smartfields.dependencies import Dependency

# Major, minor, revision

VERSION = (1, 0, 0)

def get_version():
    return "%s.%s.%s" % VERSION

__version__ = get_version()
