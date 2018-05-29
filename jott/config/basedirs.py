import os
import logging
from jott.fs import LocalFile, LocalFolder
from jott.env import environ

log = logging.getLogger('jott.config')


## initialize config paths
JOTT_DATA_DIR = None    # 'data' dir rel to script file, Folder or None
XDG_DATA_HOME = None    # Folder for XDG data home
XDG_DATA_DIRS = None    # list of Folder objects for XDG data dirs path
XDG_CONFIG_HOME = None  # Folder for XDG config home
XDG_CONFIG_DIRS = None  # list of Folder objects for XDG config dirs path
XDG_CACHE_HOME = None   # Folder for XDG cache home


def set_basedirs():
    '''This method sets the global configuration paths for according to
    the freedesktop basedir specification.

    Called automatically when module is first loaded, should be called
    explicitly only when environment has changed.
    '''
    global JOTT_DATA_DIR
    global XDG_DATA_HOME
    global XDG_DATA_DIRS
    global XDG_CONFIG_HOME
    global XDG_CONFIG_DIRS
    global XDG_CACHE_HOME

    # cast string to folder
    import jott
    jott_data_dir = LocalFile(jott.JOTT_EXEC).parent().child('data')
    if jott_data_dir.exists():
        JOTT_DATA_DIR = jott_data_dir

    if os.name == 'nt':
        APPDATA = environ['APPDATA']
        XDG_DATA_HOME = LocalFolder(
            environ.get('XDG_DATA_HOME', APPDATA + r'\jott\data'))
        XDG_DATA_DIRS = list(map(LocalFolder,
            environ.get_list('XDG_DATA_DIRS', '~/.local/share/')))
        XDG_CONFIG_HOME = LocalFolder(
            environ.get('XDG_CONFIG_HOME', APPDATA + r'\jott\config'))
        XDG_CONFIG_DIRS = list(map(LocalFolder,
            environ.get('XDG_CONFIG_DIRS', '~/.config/')))
        XDG_CACHE_HOME = LocalFolder(
            environ.get('XDG_CACHE_HOME', APPDATA + r'\jott\cache'))
    else:
        XDG_DATA_HOME = LocalFolder(
            environ.get('XDG_DATA_HOME', '~/.local/share/'))
        XDG_DATA_DIRS = list(map(LocalFolder,
            environ.get_list(
                'XDG_DATA_DIRS',('/usr/share/', '/usr/local/share/'))))
        XDG_CONFIG_HOME = LocalFolder(
            environ.get('XDG_CONFIG_HOME', '~/.config/'))
        XDG_CONFIG_DIRS = list(map(LocalFolder,
            environ.get_list('XDG_CONFIG_DIRS', ('/etc/xdg/',))))
        XDG_CACHE_HOME = LocalFolder(
            environ.get('XDG_CACHE_HOME', '~/.cache/'))


# called on initialization to set defaults
set_basedirs()


def log_basedirs():
    '''Write the search paths used to the logger, used to generate debug output.
    '''
    if JOTT_DATA_DIR:
        log.debug('Running from a source dir: {}'.format(JOTT_DATA_DIR.basename))
    else:
        log.debug('Not running from a source dir')
    log.debug('Set XDG_DATA_HOME to {}'.format(XDG_DATA_HOME))
    log.debug('Set XDG_DATA_DIRS to {}'.format(XDG_DATA_DIRS))
    log.debug('Set XDG_CONFIG_HOME to {}'.format(XDG_CONFIG_HOME))
    log.debug('Set XDG_CONFIG_DIRS to {}'.format(XDG_CONFIG_DIRS))
    log.debug('Set XDG_CACHE_HOME to {}'.format(XDG_CACHE_HOME))
