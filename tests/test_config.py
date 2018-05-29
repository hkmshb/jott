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
