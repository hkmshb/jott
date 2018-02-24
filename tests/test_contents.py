import os
import pytest
from jott import fs
from jott.contents import Jottbook



class TestJottbook(object):

    @pytest.mark.parametrize('filepath', [__file__])
    def test_from_file_fails_for_bad_jottfile(self, filepath):
        jbook = Jottbook.from_file(filepath)
        assert jbook is None

    @pytest.mark.parametrize('dirpath', [fs.dirname(__file__), None])
    def test_from_path_fails_for_bad_filepath(self, dirpath):
        jbook = Jottbook.from_path(dirpath)
        assert jbook is None

    def test_can_create_from_file(self, jbpath):
        file_args = ['.jott']
        path = fs.join(jbpath, *file_args)
        jbook = Jottbook.from_file(path)
        assert jbook is not None

    def test_can_create_from_path(self, jbpath):
        jbook = Jottbook.from_path(jbpath)
        assert jbook is not None

    def test_auto_discover_returns_project_if_found(self, jbpath):
        file_args = ['projects']
        path = fs.join(jbpath, *file_args)
        jbook = Jottbook.discover(path)
        assert jbook is not None

    def test_auto_discover_returns_None_if_no_project_found(self):
        jbook = Jottbook.discover(fs.dirname(__file__))
        assert jbook is None
