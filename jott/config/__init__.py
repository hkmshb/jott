'''Defines all functions and objects related to the application config.
'''
import logging
from .confdicts import *
from .basedirs import *
from .manager import *

from . import basedirs  # temp


def data_dirs(path=None):
    '''Generator listing paths that contain jott data files in the order
    that they should be searched. These will be the equivalent of e.g.
    '~/.local/share/jott', '/usr/share/jott' etc.

    :param path: a file path relative to the data dir; function will list
                 sub-folders with this relative path.
    :returns: yield Folder objects for the data dirs
    '''
    jottpath = ['jott']
    if path:
        if isinstance(path, str):
            path = [path]
        assert path[0] != 'jott'
        jottpath.extend(path)

    yield XDG_DATA_HOME.child(jottpath)
    if JOTT_DATA_DIR:
        if path:
            yield JOTT_DATA_DIR.child(path)
        yield JOTT_DATA_DIR

    for folder in XDG_DATA_DIRS:
        yield folder.child(jottpath)


def data_dir(path):
    '''Get a data dir sub-folder. Will look up path relative to all data
    dirs and return the first one that exists. Use this function to find
    any folders from the "data/" folder in the source package.`

    :param path: a file path relative to the data dir
    :returns: a Folder object or None
    '''
    for dir in data_dirs(path):
        if dir.exists():
            return dir
    return None


def data_file(path):
    '''Get a data file. Will look up path relative to all data dirs and
    return the first one that exists. Use this function to find any file
    from the "data/" folder in the source package.

    :param path: a file path relative to the data dir
    :returns: a File object or None
    '''
    for dir in data_dirs():
        file = dir.file(path)
        if file.exists():
            return file
    return None


def user_dirs():
    '''Get the XDG user dirs.

    :returns: a dict with directories for the XDG user dirs. These are
    typically defined in "~/.config/user-dirs.dirs". Common user dirs
    are "XDG_DESKTOP_DIR", "XDG_DOWNLOAD_DIR" etc. If no definition is
    found an empty dict will be returned.
    '''
    dirs = {}
    file = XDG_CONFIG_HOME.file('user-dirs.dirs')
    try:
        for line in file.readlines():
            line = line.strip()
            if line.isspace() or line.startswith('#'):
                continue
            else:
                try:
                    assert '=' in line
                    key, value = line.split('=', 1)
                    value = os.path.expandvars(value.strip('"'))
                    dirs[key] = LocalFolder(value)
                except:
                    errmsg = 'Exception while parsing: {}'
                    log.exception(errmsg.format(file))
    except FileNotFoundError:
        pass
    return dirs
