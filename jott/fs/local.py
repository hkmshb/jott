"""Local file system object.
"""

import os
import sys
import time
import errno
import shutil
import logging
import tempfile

log = logging.getLogger('jott.fs')

from . import FS_CASE_SENSITIVE, FS_ENCODING
from . base import *
from .base import _EOL, _SEP
from jott.env import environ


def _os_lrmdir(path):
    """Wrapper for os.rmdir that also knows how to unlink symlinks. Fails
    when the folder is not a link and is not empty.

    :param path: a file system path as string
    """
    try:
        os.rmdir(path)
    except OSError:
        if os.path.islink(path) and os.path.isdir(path) \
            and not os.listdir(path):
            os.unlink(path)
        else:
            raise


class LocalFSObjectBase(FSObjectBase):

    def __init__(self, path, watcher=None):
        FSObjectBase.__init__(self, path, watcher=watcher)

    def _stat(self):
        try:
            return os.stat(self.path)
        except OSError:
            raise FileNotFoundError(self)

    def _set_mtime(self, mtime):
        os.utime(self.path, (mtime, mtime))

    def parent(self):
        dirname = self.dirname
        if dirname is None:
            raise ValueError('Cannot get parent of root')
        return LocalFolder(dirname, watcher=self.watcher)

    def ctime(self):
        return self._stat().st_ctime

    def mtime(self):
        return self._stat().st_mime

    def iswritable(self):
        if self.exists():
            return os.access(self.path, os.W_OK)
        else:
            return self.parent().iswritable()

    def isequal(self, other):
        try:
            stat_result = os.stat(self.path)
            other_stat_result = os.stat(other.path)
        except OSError:
            return False
        else:
            return stat_result == other_stat_result

    def moveto(self, other):
        if isinstance(self, File):
            if isinstance(other, Folder):
                other = other.file(self.basename)

            assert isinstance(other, File)
        else:
            assert isinstance(other, Folder)

        if not isinstance(other, LocalFSObjectBase):
            errmsg = 'TODO: support cross object type move'
            raise NotImplementedError(errmsg)

        assert not other.path == self.path
        log.info('Rename {} to {}'.format(self.path, other.path))

        if not FS_CASE_SENSITIVE \
            and self.path.lower() == other.path.lower():
            # rename to other case - need in between step
            other = self.__class__(other, watcher=self.watcher)
            tmp = self.parent().new_file(self.basename)
            shutil.move(self.path, tmp.path)
            shutil.move(tmp.path, other.path)
        elif os.path.exists(other.path):
            raise FileExistsError(other)
        else:
            # normal case
            other = self.__class__(other, watcher=self.watcher)
            other.parent().touch()
            shutil.move(self.path, other.path)

        if self.watcher:
            self.watcher.emit('moved', self, other)
        self._cleanup()
        return other


class LocalFolder(LocalFSObjectBase, Folder):

    def exists(self):
        return os.path.isdir(self.path)

    def touch(self, mode=None):
        if not self.exists():
            self.parent().touch(mode)
            try:
                if mode is not None:
                    os.mkdir(self.path, mode)
                else:
                    os.mkdir(self.path)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
            else:
                if self.watcher:
                    self.watcher.emit('created', self)

    def __iter__(self):
        names = self.list_names()
        return self._object_iter(names, True, True)

    def list_files(self):
        names = self.list_names()
        return self._object_iter(names, True, False)

    def list_folders(self):
        names = self.list_names()
        return self._object_iter(names, False, True)

    def _object_iter(self, names, showfile, showdir):
        # inner iter to force FileNotFoundError on call instead of first iter call
        for name in names:
            path = self.path + _SEP + name
            if os.path.isdir(path):
                if showdir:
                    yield self.folder(name)
            else:
                if showfile:
                    yield self.file(name)

    def list_names(self):
        try:
            names = os.listdir(self.path)
        except OSError:
            raise FileNotFoundError(self)

        # ignore hidden files and tmp files
        names = sorted([n for n in names
            if n[0] not in ('.', '~') and n[-1] != '~'])

        return names

    def file(self, path):
        return LocalFile(self.get_childpath(path), watcher=self.watcher)

    def folder(self, path):
        return LocalFolder(self.get_childpath(path), watcher=self.watcher)

    def child(self, path):
        p = self.get_childpath(path)
        if os.path.isdir(path):
            return self.folder(path)
        elif os.path.isfile(path):
            return self.file(path)
        raise FileNotFoundError(p)

    def copyto(self, other):
        assert isinstance(other, Folder)
        assert other.path != self.path
        log.info('Copy dir {} to {}'.format(self.path, other.path))

        if isinstance(other, LocalFolder):
            if os.path.exists(other.path):
                raise FileExistsError(other)
            shutil.copytree(self.path, other.path, symlinks=True)
        else:
            self._copyto(other)

        if self.watcher:
            self.watcher.emit('created', other)
        return other

    def remove(self):
        if os.path.isdir(self.path):
            try:
                _os_lrmdir(self.path)
            except OSError:
                errmsg = 'Folder not empty: {}'.format(self.path)
                raise FolderNotEmptyError(errmsg)
            else:
                if self.watcher:
                    self.watcher.emit('removed', self)
        self._cleanup()


class AtomicWriteContext:
    """Context manager use by LocalFile for atomic write.

    Exposed as separate object to make testable. Should not be needed
    outside this module.
    """
    def __init__(self, file, mode='w'):
        self.path = file.path
        self.tmppath = self.path + '.jott-new!'
        self.mode = mode

    def __enter__(self):
        self.fh = open(self.tmppath, self.mode)
        return self.fh

    def __exit__(self, *exc_info):
        # flush to ensure write is done
        self.fh.flush()
        os.fsync(self.fh.fileno())
        self.fh.close()

        if not any(exc_info) and os.path.isfile(self.tmppath):
            os.replace(self.tmppath, self.path)
        else:
            # errors happened, try clean up
            try:
                os.remove(self.tmppath)
            except:
                pass


class LocalFile(LocalFSObjectBase, File):

    def __init__(self, path, endofline=_EOL, watcher=None):
        super(LocalFile, self).__init__(path, watcher=watcher)
        self.endofline = endofline
        self._mimetype = None

    def exists(self):
        return os.path.isfile(self.path)

    def read_binary(self):
        try:
            with open(self.path, 'rb') as fh:
                return fh.read()
        except IOError:
            if not self.exists():
                raise FileNotFoundError(self)
            else:
                raise

    def read(self):
        try:
            with open(self.path, 'rU') as fh:
                text = fh.read().decode('UTF-8')
                # strip unicode byte order mark; internally we use Unix line
                # ends - so strip out \r
                return text.lstrip('\ufeff').replace('\x00', '')
        except IOError:
            if not self.exists():
                raise FileNotFoundError(self)
            else:
                raise

    def readlines(self):
        try:
            with open(self.path, 'rU') as fh:
                return [l.decode('UTF-8').lstrip('\ufeff').replace('\x00', '')
                            for l in fh]
        except IOError:
            if not self.exists():
                raise FileNotFoundError(self)
            else:
                raise

    def write(self, text):
        text = text.encode('UTF-8')
        if self.endofline != _EOL:
            if self.endofline == 'dos':
                text = text.replace('\n', '\r\n')
            mode = 'wb'
        else:
            mode = 'w'  # trust newlines to be handled

        with self._write_decoration():
            with AtomicWriteContext(self, mode=mode) as fh:
                fh.writelines(text)

    def write_binary(self, data):
        with self._write_decoration():
            with AtomicWriteContext(self, mode='wb') as fh:
                fh.write(data)

    def touch(self):
        # overloaded bcos atomic write can cause mtime < ctime
        if not self.exists():
            with self._write_decoration():
                with open(self.path, 'w') as fh:
                    fh.write('')

    def copyto(self, other):
        if isinstance(other, Folder):
            other = other.file(self.basename)

        assert isinstance(other, File)
        assert other.path != self.path
        log.info('Copy {} to {}'.format(self.path, other.path))

        if isinstance(other, LocalFile):
            if os.path.exists(other.path):
                raise FileExistsError(other)

            other.parent().touch()
            shutil.copy2(self.path, other.path)
        else:
            self._copyto(other)

        if self.watcher:
            self.watcher.emit('created', other)
        return other

    def remove(self):
        if os.path.isfile(self.path):
            os.remove(self.path)
        if self.watcher:
            self.watcher.emit('removed', self)
        self._cleanup()


class TempFile(LocalFile):
    """Class for temporary files. These are stored in the temp directory
    and by default they are deleted again when the object is destructed.
    """

    def __init__(self, basename, unique=True, persistent=False):
        dir = get_tmpdir()
        if unique:
            super(TempFile, self).__init__(dir.new_file(basename))
        else:
            super(TempFile, self).__init__(dir.get_childpath(basename))
        self.persistent = persistent

    def __del__(self):
        if not self.persistent:
            self.remove()


def get_tmpdir():
    """Get a folder in the system temp dir for usage by jott. This jott
    specific temp folder has permission set to be readable only by the
    current users, and is touched if ti didn't exist yet.
    """
    root = tempfile.gettempdir()
    username = environ['USER']
    dir = LocalFolder(root).folder('jott-{}'.format(username))
    try:
        dir.touch(mode=0o700)   # limit to single user
        os.listdir(dir.path)    # raises error if no access
    except OSError:
        raise AssertionError(('Either you are not the owner of "{}" or '
            'the permissions are un-safe.\nIf you cannot resolve this, '
            'try setting $TMP to a different location').format(dir.path))
    else:
        return dir  # all is ok
