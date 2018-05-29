'''This module contains base classes to map config files to dicts.

The main class is ConfigDict which defines a dictionary of config keys. To add
a key in the dictionary it must first be defined using one of the sub-classes
of ConfigDefinition. This definition takes care of validating the value of the
config keys and (de-)serializing the values from and to text representation
used in the config files.
'''
import sys
import collections
from blinker import Signal
from jott.signal import SignalHandler



class ControlledDict(collections.OrderedDict):
    '''Sub class of OrderedDict that tracks modified state which is recursive
    for nested ControlledDict.
    '''
    changed = Signal()

    def __init__(self, iterable=(), **kwargs):
        super(ControlledDict, self).__init__(iterable, **kwargs)
        self._modified = False

    def __delitem__(self, key):
        super(ControlledDict, self).__delitem__(key)
        self._on_changed()

    def __setitem__(self, key, value):
        super(ControlledDict, self).__setitem__(key, value)
        self._on_changed()

    @property
    def modified(self):
        '''True when the values were modified, used to e.g. track when a
        config needs to be written back to file.
        '''
        return self._modified

    @modified.setter
    def modified(self, value):
        '''Set the modified state. Used to reset modified to False after
        the configuration has been saved to file.

        :param value: True or False
        '''
        if value:
            self._modified = True
        else:
            self._modified = False
            for ivalue in self.values():
                if isinstance(ivalue, ControlledDict):
                    ivalue.modified = False

    def update(self, iterable=(), **kwargs):
        with self._on_changed.blocked():
            super(ControlledDict, self).update(iterable, **kwargs)
        self._on_changed()

    @SignalHandler
    def _on_changed(self, **kwargs):
        self.modified = True
        self.changed.send(self, **kwargs)
