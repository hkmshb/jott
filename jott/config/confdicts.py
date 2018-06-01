'''This module contains base classes to map config files to dicts.

The main class is ConfigDict which defines a dictionary of config keys. To add
a key in the dictionary it must first be defined using one of the sub-classes
of ConfigDefinition. This definition takes care of validating the value of the
config keys and (de-)serializing the values from and to text representation
used in the config files.
'''
import ast
import sys
import json
import logging
import collections
from blinker import Signal
from jott.signal import SignalHandler
from jott.fs import FileNotFoundError

log = logging.getLogger('jott.config')


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
        if isinstance(value, ControlledDict):
            # had lot of trouble getting this to work, i.e connecting
            # a handler.. it works now and can't tell why exactly thou
            # I suspect it all has to do with 'changed' being a class
            # object as opposed an instance object
            handler = lambda sender: self._on_changed()
            self.changed.connect_via(value)(handler)
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


class ConfigDefinition:
    '''Definition for a key in a ConfigDict.
    '''
    __slots__ = ('default', 'allow_empty')

    def __init__(self, default, allow_empty=False):
        if default is None:
            allow_empty = True
        self.allow_empty = allow_empty
        # ensure default value follows check
        self.default = self.check(default)

    def __eq__(self, other):
        return self.__class__ == other.__class__ \
            and self.allow_empty == other.allow_empty

    def __ne__(self, other):
        return not self.__eq__(other)

    def _check_allow_empty(self, value):
        if value in ('', None, 'None', 'null'):
            if self.allow_empty:
                return True
            else:
                raise ValueError('Value not allowed to be empty')
        else:
            return False

    def _eval_string(self, value):
        if not value:
            return value
        elif value[0] in ('{', '['):
            try:
                value = json.loads(value)
            except:
                pass
        else:
            try:
                value = ast.literal_eval(value)
            except:
                pass
        return value

    def check(self, value):
        '''Checks value to be a valid value for this key.
        
        :raises ValueError: if value is invalid and cannot be converted.
        :returns: (converted) value if valid
        '''
        raise NotImplementedError()

    def to_string(self, value):
        return str(value)


class TypedConfigDefinition(ConfigDefinition):
    '''Definition that enforces that value is instance of a certain class.

    Classes that have a 'new_from_jott_config' method can convert values to
    the desired class.
    '''
    __slots__ = ('cls',)

    def __init__(self, default, cls=None, allow_empty=False):
        cls = cls or default.__class__
        if issubclass(cls, str):
            self.cls = str
        else:
            self.cls = cls
        super(TypedConfigDefinition, self).__init__(default, allow_empty)

    def __eq__(self, other):
        return super(TypedConfigDefinition, self).__eq__(self, other) \
            and self.cls == other.cls

    def check(self, value):
        if self._check_allow_empty(value):
            return None
        elif isinstance(value, str) and not self.cls is str:
            value = self._eval_string(value)

        if isinstance(value, self.cls):
            return value
        elif self.cls is tuple and isinstance(value, list):
            return tuple(value)
        elif hasattr(self.cls, 'new_from_jott_config'):
            try:
                return self.cls.new_from_jott_config(value)
            except:
                errmsg = 'Cannot convert {} to {}'
                log.debug(errmsg.format(value, self.cls), exc_info=1)
                raise ValueError(errmsg.format(value, self.cls))
        else:
            errmsg = 'Value should be of type: {}'
            raise ValueError(errmsg.format(self.cls.__name__))

    def to_string(self, value):
        if hasattr(value, 'serialize_jott_config'):
            return value.serialize_jott_config()
        return json.dumps(value, separators=(',', ':'))


class Boolean(ConfigDefinition):
    '''Defines a config key that maps to a boolean.
    '''

    def check(self, value):
        if self._check_allow_empty(value):
            return None
        elif isinstance(value, bool):
            return value
        elif value in ('True', 'true', 'False', 'false'):
            return value in ('True', 'true')
        raise ValueError('Must be True or False')


class Choice(ConfigDefinition):
    '''Definition that allows selecting a value from a given set. 
    '''
    __slots__ = ('choices',)

    def __init__(self, default, choices, allow_empty=False):
        self.choices = choices
        super(Choice, self).__init__(default, allow_empty)

    def __eq__(self, other):
        return super(Choice, self).__eq__(other) and \
            self.choices == other.choices

    def check(self, value):
        if self._check_allow_empty(value):
            return None
        if isinstance(value, str) and \
            not all(isinstance(c, str) for c in self.choices):
            value = self._eval_string(value)

        # HACK to allow for preferences with 'choices' item
        if all(isinstance(t, tuple) for t in self.choices):
            choices = list(self.choices) + [t[0] for t in self.choices]
        else:
            choices = self.choices

        # convert json list to tuple
        if all(isinstance(t, tuple) for t in self.choices) \
            and isinstance(value, list):
            value = tuple(value)

        if value in choices:
            return value
        elif isinstance(value, str) and value.lower() in choices:
            return value.lower()
        raise ValueError('Value should be one of {}'.format(choices))


class Float(ConfigDefinition):
    '''Defines a config key that maps to a float.
    '''

    def check(self, value):
        if self._check_allow_empty(value):
            return None
        elif isinstance(value, float):
            return value
        else:
            try:
                return float(value)
            except:
                raise ValueError('Must be float')


class Integer(ConfigDefinition):
    '''Defines a config key that maps to an integer.
    '''

    def check(self, value):
        if self._check_allow_empty(value):
            return None
        elif isinstance(value, int):
            return value
        else:
            try:
                return int(value)
            except:
                raise ValueError('Must be integer')


class Range(Integer):
    '''Definition that defines an integer value in a certain range.
    '''
    __slots__ = ('min', 'max')

    def __init__(self, default, min, max):
        self.min, self.max = (min, max)
        super(Range, self).__init__(default)

    def __eq__(self, other):
        return super(Range, self).__eq__(other) \
            and (self.min, self.max) == (other.min, other.max)

    def check(self, value):
        value = Integer.check(self, value)
        if self._check_allow_empty(value):
            return None
        if self.min <= value <= self.max:
            return value
        errmsg = 'Value should be between {} and {}'
        raise ValueError(errmsg.format(self.min, self.max))


class String(ConfigDefinition):
    '''Defines a config key that maps to a string.
    '''
    def __init__(self, default, allow_empty=False):
        if default == '':
            default = None
        super(String, self).__init__(default, allow_empty)

    def check(self, value):
        if self._check_allow_empty(value):
            return None
        if isinstance(value, str):
            return value
        elif hasattr(value, 'serialize_jott_config'):
            return value.serialize_jott_config()
        raise ValueError('Must be string')

    def to_string(self, value):
        return ('' if value is None else value)


class StringAllowEmpty(String):
    '''Like string but default to allow_empty=True.
    '''
    def __init__(self, default, allow_empty=True):
        super(StringAllowEmpty, self).__init__(default, allow_empty)


class Coordinate(ConfigDefinition):
    '''Defines a config value that is a tuple of two integers.

    This can be used to store windows coordinates. If the value is a list
    of two integers, it will automatically be converted to a tuple.
    '''

    def __init__(self, default, allow_empty=False):
        if default == (None, None):
            allow_empty = True
        super(Coordinate, self).__init__(default, allow_empty)

    def check(self, value):
        if isinstance(value, str):
            value = self._eval_string(value)
        if self._check_allow_empty(value) \
            or value == (None, None) and self.allow_empty:
            return None
        else:
            if isinstance(value, list):
                value = tuple(value)
            if (isinstance(value, tuple) and len(value) == 2 and
                isinstance(value[0], int) and isinstance(value[1], int)):
                return value
        raise ValueError('Value should be a coordinate (tuple of 2 int)')


_definition_classes = {
    str: String,
    int: Integer,
    float: Float,
    bool: Boolean
}


def build_config_definition(default=None, check=None, allow_empty=False):
    '''Convenience method to construct a ConfigDefinition object based on a
    default value and/or a check.
    '''
    if default is None and check is None:
        errmsg = 'At least provide either a default or a check'
        raise AssertionError(errmsg)
    elif check is None:
        check = default.__class__

    if isinstance(check, (type, type)):
        if issubclass(check, ConfigDefinition):
            return check(default, allow_empty=allow_empty)
        elif check in _definition_classes:
            return _definition_classes[check](default, allow_empty)
        else:
            return TypedConfigDefinition(default, check, allow_empty)
    elif isinstance(check, (set, list)) or (
         isinstance(check, tuple) and not isinstance(default, int)):
         return Choice(default, check, allow_empty)
    elif isinstance(check, tuple) and isinstance(default, int):
        assert len(check) == 2 \
            and isinstance(check[0], int) \
            and isinstance(check[1], int)
        return Range(default, check[0], check[1])
    raise ValueError('Unrecognized check type')


class ConfigDict(ControlledDict):
    '''The class defines a dictionary of config keys.

    To add a key in this dictionary it must first be defined using one of the
    sub-classes of ConfigDefinition. This definition takes care of validating
    the value of the config keys and (de-)serializing the values from and to
    text representation used in the config files.

    Both getting and setting a value will raise a KeyError when the key has
    not been defined first. A ValueError is raised when value does not conform
    to the definition.

    This class derives from ControlledDict which in turn derives from OrderedDict
    so changes to the config can be tracked by the changed signal, and values
    are kept in the same order so the order in which items are written to the
    config file is predictable.
    '''

    def __init__(self, iterable=(), **kwargs):
        assert not (iterable and kwargs)
        super(ConfigDict, self).__init__(self)
        self.definitions = collections.OrderedDict()
        self._input = collections.OrderedDict()
        if iterable or kwargs:
            self.input(iterable or kwargs)

    def __delitem__(self, key):
        super(ConfigDict, self).__delitem__(key)
        if key in self._input:
            del self._input[key]

    def __setitem__(self, key, value):
        if key in self.definitions:
            try:
                value = self.definitions[key].check(value)
                super(ConfigDict, self).__setitem__(key, value)
            except ValueError as error:
                errmsg = 'Invalid config value for {}: {} - {}'
                raise ValueError(errmsg.format(key, value, error.args[0]))
        else:
            errmsg = 'Config key "{}" has not been defined'
            raise KeyError(errmsg.format(key))

    def all_items(self):
        all_keys = list(self.keys()) + list(self._input.keys())
        for key in all_keys:
            if key in self:
                yield key, self[key]
            else:
                yield key, self._input[key]

    def copy(self):
        '''Shallow copy of the items.

        :returns: a new object of the same class with the same items
        '''
        localcopy = self.__class__()
        localcopy.update(self)
        localcopy._input.update(self._input)
        return localcopy

    def define(self, iterable=(), **kwargs):
        '''Set one or more definitions for this config dict.
        
        Can cause error log when values prior given to input() do not match
        the definition.
        '''
        assert not (iterable and kwargs)
        update = iterable or kwargs
        if isinstance(update, collections.Mapping):
            items = update.items()
        else:
            items = update

        for key, definition in items:
            if key in self.definitions:
                if definition != self.definitions[key]:
                    raise AssertionError('Key is already defined with different '
                        'definitions: {}\n{} != {}'.format(
                            key, definition, self.definitions[key]))
                else:
                    continue
            
            self.definitions[key] = definition
            if key in self._input:
                value = self._input.pop(key)
                self._set_input(key, value)
            else:
                with self._on_changed.blocked():
                    super(ConfigDict, self).__setitem__(key, definition.default)

    def dump(self):
        '''Returns a dict that combines the defined keys with any undefined
        input keys. Used e.g. when you only define part of keys in the dict,
        but want to preserve all of them writing back to a file.
        '''
        return collections.OrderedDict(self.all_items())

    def input(self, iterable=(), **kwargs):
        '''Like 'update' but won't raise on failures.

        Values for undefined keys are stored and validated once the key is
        defined. Invalid values only cause a logged error message but do not
        cause errors to be raised.
        '''
        assert not (iterable and kwargs)
        update = iterable or kwargs
        if hasattr(update, 'items'):
            items = update.items()
        else:
            items = update

        for key, value in items:
            if key in self.definitions:
                self._set_input(key, value)
            else:
                self._input[key] = value

    def update(self, iterable=(), **kwargs):
        '''Like 'dict.update()' copying values for 'iterable' or 'kwargs'.
        However if 'iterable' is also a 'ConfigDict', also the definition
        are copied along.

        Do use update when setting multiple values at once since it results
        in emitting 'changed' only once.
        '''
        if iterable and isinstance(iterable, ConfigDict):
            self.define((k, iterable.definitions[k])
                        for k in iterable if not k in self)
            super(ConfigDict, self).update(iterable, **kwargs)

    def _set_input(self, key, value):
        try:
            value = self.definitions[key].check(value)
        except ValueError as error:
            log.warn('Invalid config value for {}: "{}" - {}'.format(
                key, value, error.args[0]))
            value = self.definitions[key].default

        with self._on_changed.blocked():
            super(ConfigDict, self).__setitem__(key, value)

    def setdefault(self, key, default, check=None, allow_empty=False):
        if key in self.definitions and check is None and allow_empty is False:
            return super(ConfigDict, self).setdefault(self, key, default)
        else:
            definition = build_config_definition(default, check, allow_empty)
            self.define({key: definition})
            return self.__getitem__(key)


class ConfigSection(ControlledDict):
    '''Dict with multiple sections of config values.
    '''

    def __setitem__(self, key, value):
        assert isinstance(value, (ControlledDict, list))
        super(ConfigSection, self).__setitem__(key, value)

    def __getitem__(self, key):
        try:
            value = super(ConfigSection, self).__getitem__(key)
            return value
        except KeyError:
            with self._on_changed.blocked():
                super(ConfigSection, self).__setitem__(key, ConfigDict())
            return super(ConfigSection, self).__getitem__(key)


class ConfigFile(ConfigSection):
    '''Represents an "ini-style" configuration file.

    This models the sections as a dict-of-dicts as found in regular .ini
    files. This class represents the top-level with a key for each section.
    The values are in turn ConfigDicts which contain the key value pairs in
    that section.

    A typical file might look like::

        [Section1]
        param1=foo
        param2=bar

        [Section2]
        enabled=True
        data={'foo': 1, 'bar': 2}

    By default when parsing sections of the same name they will be merged and
    values that appear under the same section name later in the file will
    overwrite values that appeared earlier.

    Sections and parameters whose name start with '_' are considered private
    and are not stored when the config is written to file. This can be used
    for caching values that should not be persisted across instances.
    '''

    def __init__(self, file):
        '''Constructor

        :param file: a File object for reading and writing config
        '''
        super(ConfigFile, self).__init__()
        self.file = file
        try:
            with self._on_changed.blocked():
                self.read()
            self.modified = False
        except (FileNotFoundError):
            pass

    def dump(self):
        '''Serializes the config to a "ini-style" config file.
        :returns: a list of lines with text in "ini-style" formatting
        '''
        lines = []
        def dump_section(name, section):
            lines.append('[{}]\n'.format(name))
            for key, value in section.all_items():
                if not key.startswith('_'):
                    try:
                        if key in section.definitions:
                            _val = section.definitions[key].to_string(value)
                            lines.append('{}={}\n'.format(key, _val))
                        else:
                            lines.append('{}={}\n'.format(key, value))
                    except:
                        errmsg = 'Error serializing "{}" in section "[{}]"'
                        log.exception(errmsg.format(key, name))
            lines.append('\n')

        for name, section in self.items():
            if not name.startswith('_'):
                if isinstance(section, list):
                    for s in section:
                        dump_section(name, s)
                else:
                    dump_section(name, section)
        return lines[:-1]   # remove last '\n'

    def read(self):
        '''Read data from file.
        '''
        assert not self.modified, 'dict has unsaved changes'
        log.debug('Loading config from: {}'.format(self.file))
        self.parse(self.file.readlines())

    def parse(self, text):
        '''Parse an "ini-style" configuration. Fills the dictionary with values
        from this text, will merge with existing sections overwriting existing
        values.

        :param text: a string or a list of lines.
        '''
        if isinstance(text, str):
            text = text.splitlines(True)

        section, values = (None, [])
        for line in text:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            elif line.startswith('[') and line.endswith(']'):
                if values:
                    section.input(values)
                    values = []

                name = line[1:-1].strip()
                section = self[name]
            elif '=' in line:
                if section is None:
                    log.warn('Parameter outside section: {}'.format(line))
                else:
                    key, value = line.split('=', 1)
                    value = value.split('#')[0].strip() # remove inline comments
                    values.append((str(key.strip()), value))
            else:
                log.warn('Could not parse line: {}'.format(line))
        else:
            if values:
                section.input(values)

    def write(self):
        '''Write data and set modified to False.
        '''
        self.file.writelines(self.dump())
        self.modified = False
