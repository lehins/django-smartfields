
# Major, minor, revision

VERSION = (1, 1, 1)

def get_version():
    """
    Returns the version string.

    Args:
    """
    return "%s.%s.%s" % VERSION

__version__ = get_version()
