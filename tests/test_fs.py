import pytest
from jott.fs import *
from jott.fs import _HOME, _SEP



def P(path):
    # returns a windows path on windows, to make test cases platform
    # independent and keep them readable
    if os.name == 'nt':
        if path.startswith('/'):
            path = 'C:' + path
        return path.replace('/', '\\')
    return path


class TestFilePath:

    testpath = P('/foo/bar')
    test_pathnames = ('/foo', 'bar') if os.name != 'nt' else ('C:', 'foo', 'bar')
    test_uri = 'file:///foo/bar' if os.name != 'nt' else 'file:///C:/foo/bar'

    def test_file_path_ctor(self):
        # all variants should give equal result in constructor
        for p in (
            self.testpath, self.test_pathnames, self.test_uri,
            self.testpath + '///', P('/foo/./bar/../bar'),
            'file://localhost/' + self.test_uri[8:],
            'file:/' + self.test_uri[8:],
        ):
            mypath = FilePath(p)
            assert mypath.islocal is True
            assert mypath.uri == self.test_uri
            assert mypath.path == self.testpath
            assert mypath.pathnames == self.test_pathnames

    def test_filepath_basename_and_dirname(self):
        # check basename and dirname, including unicode
        mypath = FilePath(self.testpath)
        assert mypath.basename == 'bar'
        assert mypath.dirname == P('/foo')

        mypath = FilePath(P(u'/foo/\u0421\u0430\u0439\u0442\u043e\u0432\u044b\u0439'))
        assert mypath.basename == '\u0421\u0430\u0439\u0442\u043e\u0432\u044b\u0439'
        assert isinstance(mypath.basename, str) is True

        path = FilePath(P('/foo'))
        assert path.path is not None

    def test_filepath_creation_with_relpaths(self):
        # test relative paths are not accepted in constructor
        for p in (P('../foo'), P('/foo/bar/../../..')):
            assert pytest.raises(ValueError, FilePath, p)

    def test_filepath_on_windows(self):
        if os.name != 'nt':
            return
        # absolute paths either have a drive letter, or a host name
        assert pytest.raises(ValueError, FilePath, 'foo/bar')
        assert pytest.raises(ValueError, FilePath, '/foo/bar') # no drive letter
        assert pytest.raises(ValueError, FilePath, 'flie:/host/share/foo',)
        assert pytest.raises(ValueError, FilePath, 'file:///host/share/foo',)

    def test_filepath_home_dir_fallback(self):
        f = FilePath('~non-existing-user/foo')
        assert f.path == _HOME.dirname + _SEP + 'non-existing-user' + _SEP + 'foo'
