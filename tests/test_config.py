import tests
import pytest
import os, os.path as osp

from tests.test_env import EnvironContext
from jott.fs import File, Folder, LocalFile, LocalFolder

## set JOTT.EXEC for config import to work during tests
import jott
jott.JOTT_EXEC = osp.abspath(__file__)


from jott.config import *
import jott.config
import jott.env


_cwd = LocalFolder(osp.dirname(__file__))

def marshall_path_lookup(function):
    def marshalled_path_lookup(*args, **kwargs):
        value = function(*args, **kwargs)
        if isinstance(value, ConfigFile):
            p = value.file
        else:
            p = value
        if p is not None:
            assert isinstance(p, (File, Folder)), 'BUG: get {!r}'.format(p)
            assert p.ischild(_cwd), "Error: '{}' not below '{}'".format(p, _cwd)
        return value
    return marshalled_path_lookup


jott.config.data_file = marshall_path_lookup(jott.config.data_file)
jott.config.data_dir = marshall_path_lookup(jott.config.data_dir)


class EnvironConfigContext(EnvironContext):
    # here we use jott.env.environ rather than os.environ
    environ = jott.env.environ

    def __enter__(self):
        super(EnvironConfigContext, self).__enter__()
        jott.config.set_basedirs()  # refresh

    def __exit__(self, *exc_info):
        super(EnvironConfigContext, self).__exit__(*exc_info)
        jott.config.set_basedirs()  # refresh


class TestFoldersTestSetup:

    def test_setup(self):
        '''Test config environment setup of test.'''
        jott.config.log_basedirs()

        for key, value in (
            ('XDG_DATA_HOME', osp.join(tests.TMPDIR, 'data_home')),
            ('XDG_CONFIG_HOME', osp.join(tests.TMPDIR, 'config_home')),
            ('XDG_CACHE_HOME', osp.join(tests.TMPDIR, 'cache_home')),
        ):
            assert getattr(jott.config, key) == LocalFolder(value)

        sep = os.path.pathsep
        for key, value in (
            ('XDG_CONFIG_DIRS', osp.join(tests.TMPDIR, 'config_dir')),
        ):
            assert getattr(jott.config, key) == list(map(LocalFolder, value.split(sep)))
        
        _data_dir = osp.join(tests.TMPDIR, 'data_dir')
        assert jott.config.XDG_DATA_DIRS[0] == LocalFolder(_data_dir)


class TestXDGDirs:

    def test_validity(self):
        '''Test config environment is valid.'''
        for var in (
            JOTT_DATA_DIR, XDG_DATA_HOME, 
            XDG_CONFIG_HOME, XDG_CACHE_HOME
        ):
            assert isinstance(var, Folder)

        for var in (XDG_DATA_DIRS, XDG_CONFIG_DIRS):
            assert isinstance(var, list) and isinstance(var[0], Folder)

        HERE = osp.dirname(__file__)
        assert JOTT_DATA_DIR == LocalFolder([HERE, 'data'])
        # TODO: review commented out tests
        # assert JOTT_DATA_DIR.file('jott.png').exists() # TODO: uncomment
        # assert data_file('jott.png').exists() # TODO: uncomment
        # assert data_dir('templates').exists()
        # assert list(data_dirs(('foo', 'bar'))) == \
        #     [d.child(['foo', 'bar']) for d in data_dirs()]

    @pytest.mark.skipif(os.name == 'nt', reason='No standard defaults for windows')
    def test_correctness_of_defaults(self):
        '''Test default basedir paths.'''
        with EnvironConfigContext({
            'XDG_DATA_HOME': None, 'XDG_DATA_DIRS': None,
            'XDG_CONFIG_HOME': None, 'XDG_CONFIG_DIRS': None,
            'XDG_CACHE_HOME': None
        }):
            for key, value in (
                ('XDG_DATA_HOME', '~/.local/share'),
                ('XDG_CONFIG_HOME', '~/.config'),
                ('XDG_CACHE_HOME', '~/.cache')
            ):
                assert getattr(jott.config.basedirs, key) == LocalFolder(value)

            for key, value in (
                ('XDG_DATA_DIRS', '/usr/share:/usr/local/share'),
                ('XDG_CONFIG_DIRS', '/etc/xdg')
            ):
                assert getattr(jott.config.basedirs, key) == \
                            list(map(LocalFolder, value.split(':')))

    def test_correctness_for_non_defaults(self):
        local_env = {
            'XDG_DATA_HOME': '/foo/data/home',
            'XDG_DATA_DIRS': '/foo/data/dir1:/foo/data/dir2',
            'XDG_CONFIG_HOME': '/foo/config/home',
            'XDG_CONFIG_DIRS': '/foo/config/dir1:/foo/config/dir2',
            'XDG_CACHE_HOME': '/foo/cache'
        }
        if os.name == 'nt':
            local_env['XDG_DATA_DIRS'] = '/foo/data/dir1;/foo/data/dir2'
            local_env['XDG_CONFIG_DIRS'] = '/foo/config/dir1;/foo/config/dir2'

        with EnvironConfigContext(local_env):
            for key, value in (
                ('XDG_DATA_HOME', '/foo/data/home'),
                ('XDG_CONFIG_HOME', '/foo/config/home'),
                ('XDG_CACHE_HOME', '/foo/cache')
            ):
                getattr(jott.config.basedirs, key) == LocalFolder(value)

            for key, value in (
                ('XDG_DATA_DIRS', '/foo/data/dir1:/foo/data/dir2'),
                ('XDG_CONFIG_DIRS', '/foo/config/dir1:/foo/config/dir2'),
            ):
                getattr(jott.config.basedirs, key) == map(LocalFolder, value.split(':'))


class TestControlledDict:

    def test_modified_state(self):
        ctrldict = ControlledDict({'foo': 'bar'})
        assert ctrldict.modified == False

        ctrldict['bar'] = 'egg'
        assert ctrldict.modified == True
        ctrldict.modified = False

        ctrldict['section'] = ControlledDict()
        ctrldict['section']['go?'] = 'yes'
        assert ctrldict['section'].modified == True
        assert ctrldict.modified == True

        ctrldict.modified = False
        assert ctrldict.modified == False

        ctrldict['section'].modified = False
        assert ctrldict['section'].modified == False
        assert ctrldict.modified == False

        ## nested dict
        ctrldict['section'] = ControlledDict()
        ctrldict['section']['go?'] = 'FOO!'
        assert ctrldict['section'].modified == True
        assert ctrldict.modified == True

        ctrldict.modified = False
        assert ctrldict['section'].modified == False
        assert ctrldict.modified == False

        ctrldict.update({'new': 'book'})
        assert ctrldict.modified == True
        ctrldict.modified = False

        ctrldict.setdefault('new', 'XXX')
        assert ctrldict.modified == False
        ctrldict.setdefault('new2', 'XXY')
        assert ctrldict.modified == True

    def test_event_changed_subscription(self):
        counter = [0]
        def handler(source, **kwargs):
            counter[0] += 1

        ctrldict = ControlledDict({'foo': 'bar', 'section': ControlledDict()})
        ctrldict.changed.connect(handler)

        ctrldict['new'] = 'YYY'
        assert counter == [1]

        ctrldict.update({'a': 1, 'b': 2, 'c':3})
        assert counter == [2]

        ctrldict['section']['foo'] = 'zzz'
        assert counter == [3]
        ctrldict.modified = False

        value = ctrldict.pop('new')
        assert value == 'YYY'
        assert ctrldict.modified == True
        pytest.raises(KeyError, ctrldict.__getitem__, value)


class TestConfigDefinition:

    def test_build_definition(self):
        pytest.raises(AssertionError, build_config_definition)
        for default, check, cls in (
            ('foo', None, String),
            ('foo', str, String),
            (True, None, Boolean),
            (10, None, Integer),
            (1.0, None, Float),
            ('foo', ('foo', 'bar', 'baz'), Choice),
            (10, (1, 100), Range),
            ((10, 20), Coordinate, Coordinate)
        ):
            definition = build_config_definition(default, check)
            assert isinstance(definition, cls) == True

    def test_typed_config_definition(self):
        for value, cls in (
            ([1, 2, 3], list),
        ):
            definition = build_config_definition(value)
            assert isinstance(definition, TypedConfigDefinition) == True
            assert definition.cls == cls

    def test_typed_configdef_by_json_input(self):
        defn = TypedConfigDefinition([1, 2, 3])
        assert defn.check('[true,200,null]') == [True, 200, None]

    def test_typed_configdef_convertion_to_tuple(self):
        defn = TypedConfigDefinition((1, 2, 3))
        assert defn.check([5, 6, 7]) == (5, 6, 7)

    @pytest.mark.skip(reason="yet to implement interface 'new_from_jott_config'")
    def test_typed_configdef_convertion_from_jott_config(self):
        from jott.jotter import Path
        
        defn = TypedConfigDefinition(Path('foo'))
        assert defn.check('bar') == Path('bar')
        assert defn.check(':foo::bar') == Path('foo:bar')
        pytest.raises(ValueError, defn.check, ':::')

    def test_boolean_configdef(self):
        defn = Boolean(True)
        assert defn.check(False) == False
        assert defn.check('True') == True
        assert defn.check('false') == False
        pytest.raises(ValueError, defn.check, 'XXX')
        pytest.raises(ValueError, defn.check, '')
        pytest.raises(ValueError, defn.check, None)

    def test_string_configdef(self):
        defn = String('foo')
        assert defn.check('foo') == 'foo'
        pytest.raises(ValueError, defn.check, 10)
        pytest.raises(ValueError, defn.check, '')
        pytest.raises(ValueError, defn.check, None)

        defn = String('foo', allow_empty=True)
        assert defn.check('foo') == 'foo'
        assert defn.check('') == None
        assert defn.check(None) == None
        pytest.raises(ValueError, defn.check, 10)

    def test_integer_configdef(self):
        defn = Integer(10)
        assert defn.check(20) == 20
        assert defn.check('20') == 20
        assert defn.check('-20') == -20
        pytest.raises(ValueError, defn.check, 'XXX')
        pytest.raises(ValueError, defn.check, '')
        pytest.raises(ValueError, defn.check, None)

    def test_float_configdef(self):
        defn = Float(10)
        assert defn.check(20) == 20
        assert defn.check('2.0') == 2.0
        assert defn.check('-2.0') == -2.0
        pytest.raises(ValueError, defn.check, 'XXX')
        pytest.raises(ValueError, defn.check, '')
        pytest.raises(ValueError, defn.check, None)

    def test_choice_configdef(self):
        defn = Choice('xxx', ('xxx', 'foo', 'bar'))
        assert defn.check('foo') == 'foo'
        assert defn.check('Foo') == 'foo'   # case insensitive
        pytest.raises(ValueError, defn.check, 'YYY')
        pytest.raises(ValueError, defn.check, '')
        pytest.raises(ValueError, defn.check, None)

        defn = Choice('xxx', ('xxx', 'foo', 'bar'), allow_empty=True)
        pytest.raises(ValueError, defn.check, 'YYY')
        assert defn.check('foo') == 'foo'
        assert defn.check('Foo') == 'foo'   # case insensitive
        assert defn.check('') == None
        assert defn.check(None) == None

        defn = Choice((1, 2), ((1, 2), (3, 4), (5, 6)))
        defn.check([3, 4]) == (3, 4)

        # test hack for prefences with label
        pref = [
            ('xxx', 'XXX'), ('foo', 'Foo'), ('bar', 'Bar')
        ]
        defn = Choice('xxx', pref)
        assert defn.check('foo') == 'foo'

    def test_range_configdef(self):
        defn = Range(10, 1, 100)
        assert defn.check(20) == 20
        assert defn.check('20') == 20
        pytest.raises(ValueError, defn.check, -10)
        pytest.raises(ValueError, defn.check, 200)
        pytest.raises(ValueError, defn.check, 'XXX')
        pytest.raises(ValueError, defn.check, '')
        pytest.raises(ValueError, defn.check, None)

    def test_coordinate_configdef(self):
        defn = Coordinate((1, 2))
        assert defn.check((2, 3)) == (2, 3)
        assert defn.check([2, 3]) == (2, 3)
        pytest.raises(ValueError, defn.check, 'XXX')
        pytest.raises(ValueError, defn.check, (1, 2, 3))
        pytest.raises(ValueError, defn.check, (1, 'XXX'))
        pytest.raises(ValueError, defn.check, ('XXX', 2))
        pytest.raises(ValueError, defn.check, '')
        pytest.raises(ValueError, defn.check, None)

        defn = Coordinate((1, 2), allow_empty=True)
        assert defn.check('') == None
        assert defn.check(None) == None


class TestConfigDict:
    conf = ConfigDict((
        ('a', 'AAA'), ('b', 'BBB'), ('c', 'CCC')
    ))

    def test_confdict_state(self):
        assert self.conf.modified == False
        assert len(self.conf) == 0
        assert list(self.conf.keys()) == []
        assert list(self.conf.values()) == []
        assert list(self.conf.items()) == []

        pytest.raises(KeyError, self.conf.__getitem__, 'a')
        pytest.raises(KeyError, self.conf.__setitem__, 'a', 'XXX')

    def test_simple_string_values(self):
        assert self.conf.setdefault('a', 'foo') == 'AAA'
        assert len(self.conf) == 1
        assert list(self.conf.keys()) == ['a']
        assert self.conf['a'] == 'AAA'
        assert self.conf.modified == False

    def test_config_modified_status(self):
        self.conf['a'] = 'FOO'
        assert self.conf['a'] == 'FOO'
        assert self.conf.modified == True

        self.conf.modified = False
        pytest.raises(ValueError, self.conf.__setitem__, 'a', 10)
        assert self.conf.modified == False

    @pytest.mark.skip(reason='Path object yet to be defined')
    def test_path_object_value_conversion(self):
        assert self.conf.setdefault('b', Path('foo')) == Path('BBB')
        assert len(self.conf) == 2
        assert self.conf.keys() == ['a', 'b']
        assert self.conf['b'] == Path('BBB')
        assert self.conf.modified == False

        self.conf['b'] = 'FOO'
        assert self.conf['b'] == Path('FOO')
        assert self.conf.modified == True

        self.conf.modified = False
        pytest.raises(ValueError, self.conf.__setitem__, 'b', '::')
        assert self.conf.modified == False

    def test_confdict_with_choice_value(self):
        assert self.conf.setdefault('c', 'xxx', ('xxx', 'yyy', 'zzz')) == 'xxx'
        assert len(self.conf) == 2
        assert list(self.conf.keys()) == ['a', 'c']
        assert self.conf['c'] == 'xxx'
        assert self.conf.modified == False # True

        self.conf.input(d=10)
        assert self.conf['d'] == 'foo'
        self.conf.input(d='bar')
        assert self.conf['d'] == 'bar'
        assert self.conf.modified == False

    def test_confdict_copying(self):
        values = {
            'a': 'AAA', 'b': 'BBB', 'c': 'CCC'
        }
        conf = ConfigDict(values)
        conf.define(
            a=String(None),
            b=String(None),
            c=String(None)
        )
        assert dict(conf) == values

        conf_copy = conf.copy()
        assert dict(conf_copy) == values
        assert conf_copy == conf
