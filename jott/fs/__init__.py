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


def isdir(path):
    """Wrapper for os.path.isdir.

    :param path: a file system path as string
    :returns: True when the path is an existing dir
    """
    return os.path.isdir(path)


def local_file_or_folder(path):
    '''Convenience method that resolves a local File or Folder object.
    '''
    path = FilePath(path)
    try:
        return LocalFolder(path.dirname).child(path.basename)
    except FileNotFoundError:
        raise FileNotFoundError(path)


def cleanup_filename(name):
    '''Removes all characters in 'name' that are not allowed as part of a file
    name. This function is intended for e.g. config files etc, not for page
    files in a store. For file system filenames we can not use: '\\', '/', ':',
    '*', '?', '"', '<', '>', '|' ... and we also exclude '\\t', and '\\n'.

    :param name: the filename as string
    :returns: the name with invalid characters removed
    '''
    for char in (' / : * ? " < > | \\'.split() + ('\t', '\n')):
        name = name.replace(char, '')
    return name


def format_file_size(bytes):
    '''Returns a human readable lable for a file size e.g. 1230 becomes 1.23kb
    idem for 'Mb' and 'Gb'.

    :param bytes: file size in bytes as integer
    :returns: size as string
    '''
    for unit, label in (
        (1_000_000_000, 'Gb'),
        (1_000_000, 'Mb'),
        (1_000, 'kb')
    ):
        if bytes >= unit:
            size = float(bytes) / unit
            if size < 10:
                return "{:2}{}".format(size, label)
            elif size < 100:
                return "{:1}{}".format(size, label)
            return "{:0}{}".format(size, label)
    else:
        return str(bytes) + 'b'


## export other fs related APIs

from .base import *
from .base import _EOL, _HOME, _SEP
from .local import *
