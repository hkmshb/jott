"""Defines basic filesystem objects.

This module is to be used by all other Jott modules for filesystem
interactions.
"""
import os
import enum



## wrapper functions

def abspath(path):
    """Wrapper for os.path.abspath which returns the absolute version of a path.
    """
    return os.path.abspath(path)


def basename(path):
    """Wrapper for os.path.basename which returns the final component of a pathname.
    """
    return os.path.basename(path)


def dirname(path):
    """Wrapper for os.path.dirname which returns the directory component of a pathname.
    """
    return os.path.dirname(path)


def exists(path):
    """Wrapper for os.path.exists which tests whether a path exists.
    """
    return os.path.exists(path)


def fsobject(path):
    """Returns a FSObject which could either be a Directory or File object
    depending on what the path is.
    """
    if not exists(path):
        message = 'Invalid or none existing filesystem path provided: %s'
        raise ValueError(message % path)
    return Directory(path) if isdir(path) else File(path)


def isabs(path):
    """Wrapper for os.path.isabs which tests whether a path is absolute.
    """
    return os.path.isabs(path)


def isdir(path):
    """Wrapper for os.path.isdir which tests whether a path is a directory.
    """
    return os.path.isdir(path)


def isfile(path):
    """Wrapper for os.path.isfile which tests whether a path is a regular file.
    """
    return os.path.isfile(path)


def join(path, *paths):
    """Wrapper for os.path.joinpath which joins two or more pathname components,
    inserting '/' as needed. If any component is an absolute path, all previous
    path components will be discarded. An empty last part will result in a path
    that ends with a separator.
    """
    return os.path.join(path, *paths)


class FSObject:
    """Provides the common interface for FileSystem objects.
    """

    def __init__(self, fullpath):
        if not (isabs(fullpath) or exists(fullpath)):
            raise ValueError("Invalid path provided. Expected an absolute path "
                             "that exists. Provided path: %s" % fullpath)
        self.__fullpath = fullpath

    @property
    def basename(self):
        """Returns the base name of the filesystem object.
        """
        return os.path.basename(self.__fullpath)

    @property
    def children(self):
        """Returns an interator listing child objects of the current filesystem
        object as appropriate for the filesystem object type.
        """
        return iter(())

    @property
    def fullpath(self):
        """Returns the full path to the filesystem object.
        """
        return self.__fullpath

    @property
    def relpath(self, jottbook):
        """Returns the path for the filesystem object relative to the current
        jottbook path.
        """
        pass

    def __repr__(self):
        return "<%s %r>" % (
            self.__class__.__name__,
            self.basename
        )

    def __str__(self):
        return self.basename


class DirListingFlag(enum.IntFlag):
    FILE = 1
    DIRECTORY = 2
    ALL = FILE | DIRECTORY


class Directory(FSObject):
    """Represents a directory filesystem object.
    """

    def __init__(self, fullpath, listing_flag=DirListingFlag.ALL):
        if exists(fullpath) and not isdir(fullpath):
            fullpath = dirname(fullpath)

        super(Directory, self).__init__(fullpath)
        self._listing_flag = listing_flag

    def _get_listing_flag(self):
        return self._listing_flag

    def _set_listing_flag(self, value):
        self._listing_flag = value

    DirListing = property(_get_listing_flag, _set_listing_flag)

    @property
    def children(self):
        root, dirs, files = next(os.walk(self.fullpath))

        assets = []
        if DirListingFlag.DIRECTORY in self._listing_flag:
            assets.append((Directory, dirs))
        if DirListingFlag.FILE in self._listing_flag:
            assets.append((File, files))

        for factory, items in assets:
            for item in items:
                yield factory(join(root, item))


class File(FSObject):
    """Represents a file object.
    """

    def __init__(self, fullpath):
        if exists(fullpath) and not isfile(fullpath):
            raise ValueError('Full path to a file expected')
        super(File, self).__init__(fullpath)

    @property
    def last_modified(self):
        return os.path.getmtime(self.fullpath)

    def __str__(self):
        if '.' in self.basename:
            return self.basename.split('.')[0]
        return self.basename
