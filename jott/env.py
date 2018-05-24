"""Provides a wrapper class for os.environ.

When this module is loaded it will try to set proper values for HOME
and USER if they are not set, and on Windows it will also try to set
APPDATA.
"""
import os
import logging
import collections
from jott.fs import ENCODING, isdir

log = logging.getLogger('jott')


class Environ(collections.MutableMapping):

    def __getitem__(self, key):
        return os.environ[key]

    def __setitem__(self, key, value):
        os.environ[key] = value

    def __delitem__(self, key):
        del os.environ[key]

    def __iter__(self):
        return iter(os.environ)

    def __len__(self):
        return len(os.environ)

    def get(self, key, default=None):
        """Get a parameter from the environment like os.environ.get().

        :param key: the parameter to get
        :param default: the default if param does not exists
        :returns: string
        """
        try:
            value = self[key]
        except KeyError:
            return default
        else:
            if not value or value.isspace():
                return default
            return value

    def get_list(self, key, default=None, sep=None):
        """Get a parameter from the environment and convert to a list.

        :param key: the parameter to get
        :param default: the default if param does not exists
        :param sep: optional separator, default to os.path.sep if not given
        :returns: a list or the default
        """
        value = self.get(key, default)
        if value is None:
            return []
        elif isinstance(value, str):
            if sep is None:
                sep = os.pathsep
            return value.split(sep)
        else:
            assert isinstance(value, (list, tuple))
            return value


environ = Environ() # Singleton
