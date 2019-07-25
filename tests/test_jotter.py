import os
import tests
import pytest
from jott.jotter import *
from jott.config import ConfigManager
from jott.fs import LocalFile, LocalFolder



class TestJotterInfo:

    def test_jotter_info(self):
        for location, uri in (
            (LocalFile('file:///foo/bar'), 'file:///foo/bar'),
            ('file:///foo/bar', 'file:///foo/bar'),
            ('jott+file:///foo?bar', 'jott+file:///foo?bar')
        ):
            if os.name == 'nt':
                if isinstance(location, str):
                    location = location.replace('///', '///C:/')
                uri = uri.replace('///', '///C:/')
            info = JotterInfo(location)
            assert info.uri == uri


class TestJotterListInfo(tests.TestMixin):

    def _setup_test(self):
        config = ConfigManager()
        list = config.get_config_file('jotter.list')
        file = list.file
        if file.exists():
            file.remove

    def test_simple_ops_on_empty_instance(self):
        self._setup_test()
        relpath = 'some_utf8_here_\u0421\u0430\u0439'
        root = LocalFolder(self.create_tmp_dir(relpath))

        jlist = get_jotter_list()
        assert isinstance(jlist, JotterInfoList)
        assert len(jlist) == 0

        info = jlist.get_by_name('foo')
        assert info is None

        # now create it
        folder = root.child('/jotter')
        init_jotter(folder, name='foo')

        jlist = get_jotter_list()
        jlist.append(JotterInfo(folder.uri, name='foo'))
        jlist.write()

        assert len(jlist) == 1
        assert isinstance(jlist[0], JotterInfo)

        info = jlist.get_by_name('foo')
        assert info.uri == folder.uri
        assert info.name == 'foo'

class TestPath:
    '''Test Path object.
    '''

    def generator(self, name):
        return Path(name)

    def test_valid_page_name(self):
        # valid names
        for name in ('test', 'test this', 'test (this)', 'test:this (2)'):
            Path.assert_valid_page_name(name)

        # invalid names
        for name in (':test', '+test', 'foo:_bar', 'foo::bar', 'foo#bar'):
            assert pytest.raises(
                AssertionError,
                Path.assert_valid_page_name, name)

    def test_namespaced_page_names(self):
        for name, ns, basename in (
            ('Test:foo', 'Test', 'foo'),
            ('Test', '', 'Test')
        ):
            # test name
            Path.assert_valid_page_name(name)
            assert Path.make_valid_page_name(name) == name

            # get object
            path = self.generator(name)

            # test basic props
            assert path.name == name
            assert path.basename == basename
            assert path.namespace == ns
            assert path.name in path.__repr__()

