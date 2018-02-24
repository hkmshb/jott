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

    def test_dirobj_children_lists_all_contents_by_default(self, jbpath):
        dirobj = fs.Directory(jbpath)
        assert dirobj is not None

        root, dirs, files = next(os.walk(jbpath))
        children = list(dirobj.children)
        assert children is not None \
           and len(children) == len(files) + len(dirs)

        for c in children:
            if c.basename in files:
                assert isinstance(c, fs.File)
            elif c.basename in dirs:
                assert isinstance(c, fs.Directory)

    @pytest.mark.parametrize('flag', [
        fs.DirListingFlag.FILE, fs.DirListingFlag.DIRECTORY
    ])
    def test_dirobj_children_can_differ_by_listing_flat(self, jbpath, flag):
        root, dirs, files = next(os.walk(jbpath))
        dirobj = fs.Directory(jbpath, flag)

        target = (fs.File, files)
        if flag == fs.DirListingFlag.DIRECTORY:
            target = (fs.Directory, dirs)

        assert len(list(dirobj.children)) == len(target[1])
        for c in dirobj.children:
            assert isinstance(c, target[0])

    def test_dirobj_repr(self, jbpath):
        dirobj = fs.Directory(jbpath)
        assert repr(dirobj) == "<Directory 'jottbook'>"

    def test_fileobj_repr(self, jbpath):
        fileobj = fs.File(fs.join(jbpath, '.jott'))
        assert repr(fileobj) == "<File '.jott'>"
