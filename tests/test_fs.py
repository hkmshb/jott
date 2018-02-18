import os

import pytest
from jott import fs


class TestFSObject(object):

    def test_fileobj_creation_with_dirpath_fails(self, jbpath):
        with pytest.raises(ValueError):
            fs.File(jbpath)

    def test_dirobj_creation_with_filepath_passes(self, jbpath):
        filepath = fs.join(jbpath, '.jott')
        assert fs.isfile(filepath) == True

        dirobj = fs.Directory(filepath)
        assert dirobj is not None \
           and dirobj.fullpath == jbpath \
           and dirobj.basename == 'jottbook'

    def test_dirobj_children_lists_files_only_by_default(self, jbpath):
        dirobj = fs.Directory(jbpath)
        assert dirobj is not None

        root, dirs, files = next(os.walk(jbpath))
        children = list(dirobj.children)
        assert children is not None \
           and len(children) == len(files)

        for f in children:
            assert isinstance(f, fs.File)
            assert f.basename in files

    def test_dirobj_children_can_contain_dirs_also(self, jbpath):
        root, dirs, files = next(os.walk(jbpath))
        dirobj = fs.Directory(jbpath, True)
        assert len(list(dirobj.children)) == len(dirs + files)

    def test_dirobj_children_with_dirs_lists_dirs_first(self, jbpath):
        root, dirs, files = next(os.walk(jbpath))
        dirobj = fs.Directory(jbpath, True)
        children = list(dirobj.children)
        assert len(children) == len(dirs + files)

        for fsobj in children[:len(dirs)]:
            assert fs.isdir(fsobj.fullpath) == True
            assert fsobj.basename in dirs

        for fsobj in children[len(dirs):]:
            assert fs.isfile(fsobj.fullpath)

    def test_dirobj_children_with_dirs_can_list_files_first(self, jbpath):
        root, dirs, files = next(os.walk(jbpath))
        dirobj = fs.Directory(jbpath, True, False)
        children = list(dirobj.children)
        assert len(children) == len(dirs + files)

        for fsobj in children[:len(files)]:
            assert fs.isfile(fsobj.fullpath)
            assert fsobj.basename in files

        for fsobj in children[len(files):]:
            assert fs.isdir(fsobj.fullpath)
            assert fsobj.basename in dirs

    def test_dirobj_repr(self, jbpath):
        dirobj = fs.Directory(jbpath)
        assert repr(dirobj) == "<Directory 'jottbook'>"

    def test_fileobj_repr(self, jbpath):
        fileobj = fs.File(fs.join(jbpath, '.jott'))
        assert repr(fileobj) == "<File '.jott'>"
