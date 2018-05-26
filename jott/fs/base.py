import os
import re
import logging
from urllib.parse import urlencode

from . import FS_ENCODING, FS_SUPPORT_NON_LOCAL_FILE_SHARES
from jott.exc import Error

log = logging.getLogger('jott.fs')


#: regex patterns
is_url_re = re.compile(r'^\w{2,}:/')
is_share_re = re.compile(r'^\\\\\w')

#: consts
_SEP = os.path.sep
_EOL = 'dos' if os.name == 'nt' else 'unix'


class FileNotFoundError(Error):
    """Error thrown when a file is not found.
    """

    def __init__(self, path):
        self.file = path
        path = path.path if hasattr(path, 'path') else path
        super().__init__('No such file or folder: {}'.format(path))


class FolderNotEmptyError(Error):

    def __init__(self, path):
        path = path.path if hasattr(path, 'path') else path
        super().__init__('Folder not empty: {}'.format(path))


def _split_file_url(url):
    scheme, path = url.replace('\\', '/').split(':/', 1)
    if scheme not in ('file', 'smb'):
        raise ValueError('Not a file URL: {}'.format(url))
    if path.startswith('/localhost/'):
        path = path[11:]
        isshare = False
    elif scheme == 'smb' or re.match(r'^/\w', path):
        isshare = True
    else:
        isshare = False
    return path.strip('/').split('/'), isshare


def _split_normpath(path):
    # takes either string or list of anems and returns a normalized tuple
    # keeps leading "/" or "\\" to distinguish absolute paths
    if isinstance(path, str):
        if is_url_re.match(path):
            mkroot = True
            path, mkshare = _split_file_url(path)
        else:
            if path.startswith('~'):
                mkroot = True
                path = _os_expanduser(path)
            else:
                mkroot = path.startswith('/')
            mkshare = re.match(r'^\\\\\w', path) is not None
            path = re.split(r'[/\\]+', path.strip('/\\'))
    else:
        mkshare, mkroot = (False, False)

    # build abspath, by resolving '..' if present
    names = []
    for name in path:
        if name == '.' and names:
            pass
        elif name == '..':
            if names and names[-1] != '..':
                names.pop()
            else:
                names.append(name)
                mkroot = False
        else:
            names.append(name)

    if not names:
        raise ValueError('path reduces to empty string')
    elif mkshare:
        names[0] = '\\\\' + names[0]    # UNC host needs leading '\\'
    elif mkroot and os.name != 'nt' and names[0][0] != '/':
        names[0] = '/' + names[0]
    return tuple(names)


def _os_expanduser(path):
    """Wrapper for os.path.expanduser.
    """
    assert path.startswith('~')
    if FS_ENCODING == 'mbcs':
        parts = path.replace('\\', '/').strip('/').split('/')
        parts[0] = os.path.expanduser(parts[0])
        path = _SEP.join(parts)
    else:
        path = os.path.expanduser(path)
    
    if path.startswith('~'):
        # expansion failed - do a simple fallback
        from jott.env import environ

        home = environ['HOME']
        parts = path.replace('\\', '/').strip('/').split('/')
        if parts[0] == '~':
            path = _SEP.join([home] + parts[1:])
        else:   #~user
            dir = os.path.dirname(home) # /home or similar ?
            path = _SEP.join([dir, parts[0][1:]] + parts[1:])
    return path


if os.name == 'nt':
    def _join_abspath(names):
        # first element must be either drive letter or UNC host
        path = '\\'.join(names)
        if not re.match(r'^(\w:|\\\\\w)', names[0]):
            raise ValueError('Not an absolute path: {}'.format(path))
        return path

    def _join_uri(names):
        # first element must be either drive letter or UNC host
        if not re.match(r'^(\w:|\\\\\w)', names[0]):
            path = '\\'.join(names)
            raise ValueError('Not an absolute path: {}'.format(path))
        
        # drive letter - e.g: file:///c:/foo
        elif re.match(r'^\w:$', names[0]):
            return 'file:///' + names[0] + '/' + urlencode('/'.join(names[1:]))
        
        # UNC path - e.g. file://host/share
        elif re.match(r'^\\\\\w+$', names[0]):
            return 'file://' + urlencode(names[0].strip('\\') 
                                          + '/' + '/'.join(names[1:]))
##: if unix
else:
    def _join_abspath(names):
        if names[0].startswith('\\\\'):
            return '\\'.join(names)
        elif names[0].startswith('/'):
            return '/'.join(names)
        raise ValueError('Not an absolute path: {}'.format('/'.join(names)))

    def _join_uri(names):
        path = urlencode('/'.join(names))
        if names[0][0] == '/':
            return 'file://' + path
        return 'file:///' + path


class FilePath:
    """Represents filesystem paths and serves as the base class for file and
    directory/folder objects. Contains methods for file path manipulation.

    File paths should alwasy be absolute paths and can  not start with "../"
    or "./" for instance. On Windows they should always start with either a
    drive letter or a share drive. On Unix they should start at the root of
    the filesystem.

    Paths can be handled either as strings representing a local file path ("/"
    or "\\" separated), strings representing a file uri ("file:///" or "smb://")
    or list of path names.
    """
    __slots__ = ('path', 'pathnames', 'islocal')

    def __init__(self, path):
        if isinstance(path, (tuple, list, str)):
            self.pathnames = _split_normpath(path)
            self.path = _join_abspath(self.pathnames)
        elif isinstance(path, FilePath):
            self.pathnames = path.pathnames
            self.path = path.path
        else:
            raise TypeError('Cannot convert {!r} to a FilePath'.format(path))

        self.islocal = not self.pathnames[0].startswith('\\\\')

    @property
    def basename(self):
        return self.pathnames[-1]

    @property
    def dirname(self):
        if len(self.pathnames) >= 2:
            return _join_abspath(self.pathnames[:-1])
        return None

    # TODO: fix _join_uri
    # @property
    # def uri(self):
    #     return _join_uri(self.pathnames)

    @property
    def userpath(self):
        if self.ischild(_HOME):
            return '~' + _SEP + self.relpath(_HOME)
        return self.path

    def common_parent(self, other):
        if self.pathnames[0] != other.pathnames[0]:
            # prevent other drives and other shares
            return None
        elif self.ischild(other):
            return other
        elif other.ischild(self):
            return self
        for i in range(1, len(self.pathnames)):
            if self.pathnames[:i + 1] != other.pathnames[:i + 1]:
                return FilePath(self.pathnames[:i])

    def get_abspath(self, path):
        """Returns a FilePath for path where path can be either an absolute
        path or a path relative to this path (either upward or downward -
        use get_childpath() to only get child paths).
        """
        try:
            return FilePath(path)
        except ValueError:
            # not an absolute path
            names = _split_normpath(path)
            return FilePath(self.pathnames + names)

    def get_childpath(self, path):
        assert path
        names = _split_normpath(path)
        if not names or names[0] == '..':
            raise ValueError('Relative path not below parent: {}'.format(path))
        return FilePath(self.pathnames + names)

    def ischild(self, parent):
        names = parent.pathnames
        return len(names) < len(self.pathnames) \
            and self.pathnames[:len(names)] == names

    def relpath(self, start, allow_upward=False):
        if allow_upward and not self.ischild(start):
            parent = self.common_parent(start)
            if parent is None:
                errmsg = 'No common parent between {} and {}'
                raise ValueError(errmsg.format(self.path, start.path))
            relpath = self.relpath(parent)
            level_up = len(start.pathnames) - len(parent.pathnames)
            return (('..' + _SEP) * level_up) + relpath
        else:
            names = start.pathnames
            if not self.pathnames[:len(names)] == names:
                raise ValueError('Not a parent path: {}'.format(start.path))
            return _SEP.join(self.pathnames[len(names):])

    def __eq__(self, other):
        return isinstance(other, self.__class__) and other.path == self.path

    def __repr__(self):
        return "<{}: {}>".format(
            self.__class__.__name__,
            self.path
        )

    def __str__(self):
        return self.path


_HOME = FilePath('~')


class FSObjectBase(FilePath):
    """Base class which represents File and Folder objects on the filesystem.
    """

    def __init__(self, path, watcher=None):
        super(FSObjectBase, self).__init__(path)
        if not FS_SUPPORT_NON_LOCAL_FILE_SHARES and not self.islocal:
            raise ValueError('File system does not support non-local files')
        self.watcher = watcher

    def isequal(self, other):
        """Check file paths are equal based on stat results (inode number etc).
        Intended to detect when two files or dirs are the same on case-insensitive
        filesystems. Does not explicitly check if the content is the same.

        :param other: an other FilePath object
        :returns: True when the two paths are one and the same file
        """
        raise NotImplementedError()
    
    def copyto(self, other):
        raise NotImplementedError()

    def exists(self):
        raise NotImplementedError()

    def parent(self):
        raise NotImplementedError()

    def ctime(self):
        raise NotImplementedError()

    def mtime(self):
        raise NotImplementedError()

    def iswritable(self):
        raise NotImplementedError()

    def moveto(self):
        raise NotImplementedError()

    def remove(self):
        raise NotImplementedError()

    def touch(self):
        raise NotImplementedError()

    def _cleanup(self):
        try:
            self.parent().remove()
        except (ValueError, FolderNotEmptyError):
            pass

    def _moveto(self, other):
        log.debug('Crosss FS type move {} --> {}'.format(self, other))
        self._copyto(other)
        self.remove()
