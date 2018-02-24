import os
from . import fs, utils



class Jottbook:
    """Represents a Jott book which is a directory containing a collection
    of plain text files which together can be managed by Jott with files
    rendered in a "jott-special" way.
    """
    EXT = '.jott'

    def __init__(self, name, jbook_file, tree):
        """The jbook_file together with tree params help with the case where
        the .jott file leaves outside the jott book directory to be managed.

        :param name: name of the jott book
        :param jbook_file: path to a .jott file
        :param tree: path to the root directory of a Jott book
        """
        if jbook_file in ('', None):
            raise ValueError('jbook_file cannot be null or empty')

        if not os.path.isfile(jbook_file):
            raise FileNotFoundError('jottbook file: %s' % jbook_file)

        self.name = name
        self.jbook_file = jbook_file
        self.tree = os.path.normpath(tree)

    def open(self):
        if self.jbook_file is None:
            raise RuntimeError('This jottbook has not .jott file')
        return utils.open_config(self.jbook_file)

    def save(self, jbook):
        """Saves the provided jott book.

        :param jbook: a `configparser.ConfigParser` object containing the
            configurations of a jottbook.
        """
        if self.jbook_file is None:
            raise RuntimeError('This jottbook has not .jott file')
        utils.save_config(jbook, self.jbook_file)

    @classmethod
    def from_file(cls, filepath):
        """Reads a jottbook from a .jott file.
        """
        jbook = utils.open_config(filepath)
        if len(jbook.keys()) == 1: # is empty
            return None

        default_name = (fs.basename(filepath).rsplit('.')[0]).title()
        name = jbook.get('jott', 'name', fallback=default_name)
        path = fs.join(fs.dirname(filepath),
                       jbook.get('jott', 'path', fallback='.'))
        return cls(name=name, jbook_file=filepath, tree=path)

    @classmethod
    def from_path(cls, path, extension_required=False):
        """Locates the jott book file from a path.
        """
        path = fs.abspath(path or '')
        file_ext_check_ok = not extension_required or path.endswith(cls.EXT)
        if fs.isfile(path) and file_ext_check_ok:
            return cls.from_file(path)

        try:
            files = [f for f in os.listdir(path)
                     if f.lower().endswith(cls.EXT)]
        except OSError:
            return None

        if len(files) == 1:
            return cls.from_file(fs.join(path, files[0]))
        return None

    @classmethod
    def discover(cls, base=None):
        """Auto discovers the closest jottbook.
        """
        if base is None:
            base = os.getcwd()
        here = base
        while True:
            jbook = cls.from_path(here, extension_required=True)
            if jbook is not None:
                return jbook
            node = fs.dirname(here)
            if node == here:
                break
            here = node

    @property
    def jottbook_path(self):
        return self.jbook_file or self.tree

    def get_directories(self):
        jottbook_dir = fs.fsobject(self.jottbook_path)
        return jottbook_dir.children
