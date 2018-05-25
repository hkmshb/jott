"""Provides classes and helper functions to interact with the filesystem.
"""
import os
import re
import sys
import logging
from urllib.parse import urlencode

log = logging.getLogger('jott.fs')


#: flag to indicate if filesystem is case sensitive
FS_CASE_SENSITIVE = (os.name != 'nt')

#: flag to indicate if filesystem supports \\host\share
FS_SUPPORT_NON_LOCAL_FILE_SHARES = (os.name == 'nt')

#: filesystem encoding
FS_ENCODING = sys.getfilesystemencoding()


from .base import *
from .base import _EOL, _HOME, _SEP


def isdir(path):
    """Wrapper for os.path.isdir.

    :param path: a file system path as string
    :returns: True when the path is an existing dir
    """
    return os.path.isdir(path)


class Dir:
    
    def __init__(self, path):
        self._path = path

    def exists(self):
        return os.path.exists(self._path) and isdir(self._path)
