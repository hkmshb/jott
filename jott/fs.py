"""Provides classes and helper functions to interact with the filesystem.
"""
import os
import os.path as osp


ENCODING = None


def isdir(path):
    return osp.isdir(path)


class Dir:
    
    def __init__(self, path):
        self._path = path

    def exists(self):
        return osp.exists(self._path) and isdir(self._path)
