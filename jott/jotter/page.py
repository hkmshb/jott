import re
import logging
from datetime import datetime
from blinker import Signal

from jott import fs

log = logging.getLogger('jott.jotter')



## re patterns
_pagename_reduce_colon_re = re.compile('::+')
_pagename_invalid_char_re = re.compile(
    '(' +
        '^[_\W]|(?<=:)[_\W]' +
    '|' +
        '[' + re.escape(''.join(
            ('?', '#', '/', '\\', '*', '"', '<', '>', '|', '%', '\t', '\n', '\r')
        )) + ']' +
    ')')


class Path:
    '''Represents a page name in a jotter.

    This is the parent class for the Page class. It contains the name of the
    page and is used instead of the actual page object by methods that only
    need to know the name of the page.

    Path objects have no internal state and are essentially normalized page
    names. It also has a number of methods to compare page names and determine
    what the parent pages are.

    A number of characters are not valid in page names as used in Jott jotters.
    Reserved characters are:
     - ':' is reserved as a separator
     - '?' is reserved to encode url style options
     - '#' is reserved as anchor separator
     - '/' and '\' are reserved to distinguish file links & urls
    '''
    __slots__ = ('name',)

    @staticmethod
    def assert_valid_page_name(name):
        '''Raises an AssertionError if name does not represent a valid page
        name.

        This is a strict check, most names that fail this test can still be
        cleaned up by the make_valid_page_name() function.

        :param name: a string
        :raises AssertionError: if the name is not valid
        '''
        assert isinstance(name, str)
        if not name.strip(':') \
            or _pagename_reduce_colon_re.search(name) \
            or _pagename_invalid_char_re.search(name):
            raise AssertionError('Not a valid page name: {}'.format(name))

    @staticmethod
    def make_valid_page_name(name):
        '''Remove any invalid character from the string and return a valid
        page name. Only string that can not be turned into something valid
        is a string that reduces to an empty string after removing all
        invalid characters.

        :param name: a string
        :returs: a string
        :raises ValueError: when the result would be an empty string
        '''
        newname = _pagename_reduce_colon_re.sub(':', name.strip(':'))
        newname = _pagename_invalid_char_re.sub('', newname)
        newname = newname.replace('_', ' ')
        try:
            Path.assert_valid_page_name(newname)
        except AssertionError:
            errmsg = 'Not a valid page name: {} (was: {})'
            raise ValueError(errmsg.format(newname, name))
        return newname

    @classmethod
    def new_from_jott_config(cls, string):
        '''Returns a new object based on the string representation for that 
        path.
        '''
        return cls(cls.make_valid_page_name(string))

    def __init__(self, name):
        '''Initializes a new instance of Path class.

        :param name: the absolute page name in the right case as a string
            or as a tuple string.
        :note: The name ':' is used as a special case to construct a path
            for the toplevel namespace in a jotter.
        '''
        if isinstance(name, (list, tuple)):
            self.name = ':'.join(name)
        else:
            self.name = name.strip(':')

    @property
    def basename(self):
        '''Get the basename of the path (last part of the name)
        '''
        index = self.name.rfind(':')
        return self.name[index + 1:]

    @property
    def isroot(self):
        '''True when the Path represents the top level namespace.
        '''
        return self.name == ''

    @property
    def namespace(self):
        '''Gives the name for the parent page.

        Returns an empty string for the top level namespace.
        '''
        index = self.name.rfind(':')
        if index > 0:
            return self.name[index]
        return ''

    @property
    def parts(self):
        '''Get all the parts of the name (split on ':')
        '''
        return self.name.split(':')

    @property
    def parent(self):
        '''Get the path for the parent page.
        '''
        ns = self.namespace
        if ns:
            return Path(ns)
        elif self.isroot:
            return None
        return Path(':')

    def child(self, basename):
        '''Get a child Path.

        :param basename: the relative name for the child
        :returns: a new Path object
        '''
        return Path(self.name + ':' + basename)

    def ischild(self, parent):
        '''Checks if this Path is a child of a given Path.
        
        :param parent: a Path object.
        :returns: True when this path is a (grand-)child of parent
        '''
        return parent.isroot or self.name.startswith(parent.name + ':')

    def common_parent(self, other):
        '''Find a common parent for two Paths

        :param other: another Path object
        :returns: a Path object for the first common parent
        '''
        parent = []
        parts = self.parts
        other = other.parts
        if parts[0] != other[0]:
            return Path(':')
        else:
            for i in range(min(len(parts), len(other))):
                if parts[i] == other[i]:
                    parent.append(parts[i])
                else:
                    return Path(':'.join(parent))
            else:
                return Path(':'.join(parent))

    def parents(self):
        '''Generator function for parent Paths including root
        '''
        if ':' in self.name:
            path = self.name.split(':')
            path.pop()
            while len(path) > 0:
                ns = ':'.join(path)
                yield Path(ns)
                path.pop()
        yield Path(':')

    def relname(self, path):
        '''Gets a part of this Path relative to a parent Path

        :param path: a parent Path.
        :returns: the part of the Path that is relative to path
        :note: raises an error if path is not a parent
        '''
        if path.name == ':':
            return self.name
        elif self.name.startswith(path.name + ':'):
            index = len(path.name) + 1
            return self.name[index:].strip(':')
        raise ValueError("'{}' is not below '{}'".format(self, path))


class SourceFile(fs.File):

    @property
    def iswritable(self):
        return False

    def write(self, **kwargs):
        raise AssertionError('Not writable')

    def writelines(self, **kwargs):
        raise AssertionError('Not writable')


class Page(Path):
    '''Represents a single page in a jotter.

    Page objects inherit from Path but have internal state reflecting content
    in the jotter. We try to keep Page objects unique by hashing them in
    Jotter.get_page(), Path object on the other hand are cheap and can have
    multiple instances for the same logical path. We ask for a path object of
    a name in the constructor to encourage the use of Path objects over passing
    around page names as string.
    '''
    page_changed = Signal()

    def __init__(self, path, has_children, file, folder):
        assert isinstance(path, Path)
        self.name = path.name
        self.has_children = has_children
        self.valid = True
        self.modified = False
        self._parsetree = None
        self._ui_object = None
        self._meta = None
        self._readonly = None
        self._last_etag = None
        #self.format = None              # TODO: review
        self.source = SourceFile(file.path)
        self.source_file = file
        #self.attachment_folder = None   # TODO: review

    @property
    def ctime(self):
        if self.source_file.exists():
            return self.source_file.ctime()
        return None

    @property
    def mtime(self):
        if self.source_file.exists():
            return self.source_file.mtime()
        return None

    @property
    def has_content(self):
        '''Returns whether this page has content.
        '''
        if self._parsetree:
            return self._parsetree.has_content
        elif self._ui_object:
            tree = self._ui_object.get_parsetree()
            if tree:
                return tree.has_content
            return False
        else:
            return self.source_file.exists()

    @property
    def readonly(self):
        if self._readonly is None:
            self._readonly = not self.source_file.iswritable()
        return self._readonly

    def dump(self, format, linker=None):
        '''Get content in a specific format.

        Convenience method that converts the current parse tree to a particular
        format first.

        :param format: either a format module or a string that is understood by
            jott.format.get_format()
        :param linker: a linker object (see BaseLinker)
        :returns: text as a list of lines or an empty list
        '''
        if isinstance(format, str):
            format = jott.format.get_format(format)
        
        if linker is not None:
            linker.set_path(self)

        tree = self.get_parsetree()
        if tree:
            return format.Dumper(linker=linker).dump(tree)
        else:
            return []

    def parse(self, format, text, append=False):
        '''Store formatted text in the page.

        Convenience method that parses text and sets the parse tree accordingly.

        :param format: either a format module or a string that is understood by
            jott.formats.get_format()
        :param text: text as a string or as a list of lines
        :param append: if True the text is appended instead of replacing current
            content.
        '''
        if isinstance(format, str):
            format = jott.format.get_format(format)

        parsed_content = format.Parse().parse(text)
        if append:
            self.append_parsetree(parsed_content)
        else:
            self.set_parsetree(parsed_content)

    def exists(self):
        '''True when the page has either content or children.
        '''
        return self.has_children or self.has_content

    def get_title(self):
        tree = self.get_parsetree()
        if tree:
            return tree.get_heading() or self.basename
        return self.basename

    def heading_matches_pagename(self):
        '''Returns whether the heading matches the page name.

        Used to determine whether the page should hav its heading auto-changed
        on remove/move.
        
        :returns: True whe the heading can be auto-changed.
        '''
        tree = self.get_parsetree()
        if tree:
            return tree.get_heading() == self.basename
        return False

    def append_parsetree(self, tree):
        '''Append content.
        '''
        current_tree = self.get_parsetree()
        if current_tree:
            self.set_parsetree(current_tree + tree)
        else:
            self.set_parsetree(tree)

    def get_parsetree(self):
        '''Returns the contents of the page.

        :returns: a jott.format.ParseTree object or None
        '''
        assert self.valid, 'DEBUG! Page object became invalid.'
        if self._parsetree:
            return self._parsetree
        elif self._ui_object:
            return self._ui_object.get_parsetree()
        else:
            try:
                text, self._last_etag = self.source_file.read_with_etag()
            except fs.FileNotFoundError:
                return None
            else:
                parser = self.format.Parser()
                self._parsetree = parser.parse(text)
                self._meta = self._parsetree.meta
                assert self._meta is not None
                return self._parsetree

        def set_parsetree(self, tree):
            '''Set the parsetree with content for this page.

            :param tree: a jott.format.ParseTree object with content or None
                to remove all content from the page.
            :note: after setting new content in the Page object it still needs
                to be stored in the jotter to save this content permanently.
            '''
            assert self.valid, 'DEBUG! Page object became invalid'
            if self.readonly:
                raise PageReadOnlyError(self)
            
            if self._ui_object:
                self._ui_object.set_parsetree(tree)
            else:
                self._parsetree = tree
            self.modified = True

    def set_ui_object(self, object):
        '''Lock the page to an interface widget.

        Setting a "ui object" locks the page and turns it into a proxy for that
        widget - typically a jott.gui.pageview.PageView. The "ui object" should
        in turn have a get_parsetree() and a set_parsetree() method which will
        be called by the page object.
        '''
        if object is None:
            if self._ui_object:
                self._parsetree = self._ui_object.get_parsetree()
                self._ui_object = None
        else:
            assert self._ui_object is None, (
                'DEBUG! Page already being edited by another widget')
            self._parsetree = None
            self._ui_object = object

    def _check_source_etag(self):
        if (
            self._last_etag and
            not self.source_file.verify_etag(self._last_etag)
        ) or (
            not self._last_etag
            and self._parsetree
            and self.source_file.exists()
        ):
            log.info('Page changed on disk: {}'.format(self.name))
            self._last_etag = None
            self._meta = None
            self._parsetree = None
            self.changed.send(True)

    def _store(self):
        tree = self.get_parsetree()
        self._store_tree(tree)

    def _store_tree(self, tree):
        if tree and tree.has_content:
            if self._meta is not None:
                tree.meta.update(self._meta)    # preserve headers
            elif self.source_file.exists():
                # try getting headers from file
                try:
                    text = self.source_file.read()
                except fs.FileNotFoundError:
                    return None
                else:
                    parser = self.format.Parser()
                    tree = parser.parse(text)
                    self._meta = tree.meta
                    tree.meta.update(self._meta)    # preserve headers
            else:
                now = datetime.now()
                tree.meta['Date-Created'] = now.isoformat()
