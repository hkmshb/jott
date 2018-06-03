import re
import enum

from .page import Path
from jott.fs import FS_ENCODING, File, Folder, _EOL, _SEP
from jott.formats import get_format



class FileType(enum.Enum):
    PAGE_SOURCE = 1
    ATTACHMENT = 2


class JotterLayout:
    pass


class FilesLayout(JotterLayout):
    '''Layout is responsible for mapping between pages and files.

    This is the most basic version, where each page maps to the
    like-named file.
    '''
    default_extension = '.md'
    default_format = get_format('markdown')

    def __init__(self, folder):
        assert isinstance(folder, Folder)
        self.root = folder
        self.endofine = _EOL

    def get_attachments_folder(self, pagename):
        raise NotImplementedError()

    def get_format(self, file):
        if file.path.endswith(self.default_extension):
            return self.default_format
        raise AssertionError('Unknown file type for page: {}'.format(file))

    def index_list_children(self, pagename):
        raise NotImplementedError()

    def map_file(self, file):
        '''Map a filepath to a pagename.

        :param file: a File or FilePath object.
        :returns: a Path and file type
        '''
        path = file.relpath(self.root)
        return self.map_filepath(path)

    def map_filepath(self, path):
        '''Like map_file but takes a string with relative path.
        '''
        if path.endswith(self.default_extension):
            path = path[:-len(self.default_extension)]
            type = FileType.PAGE_SOURCE
        else:
            type = FileType.PAGE_SOURCE
            if _SEP in path:
                path, _ = path.rsplit(_SEP, 1)
            else:
                path = ':'  # ROOT_PATH
        if path == ':':
            return Path(':'), type
        else:
            Path.assert_valid_page_name(path)
            return Path(path), type

    def map_page(self, pagename):
        '''Map a pagename to a default file.

        :param pagename: a Path
        :returns: a 2-tuple of a File for the source and a Folder for the
            attachements. Neither of these needs to exist.
        '''
        path = pagename.name
        file = self.root.file(path + self.default_extension)
        file.endofine = self.endofine   # TODO: make auto-detect
        folder = self.root.folder(path) if path else self.root
        return (file, folder)

    def resolve_conflict(self, *filepaths):
        '''Decide which is the real page file when multiple files map to the
        same page.

        :param filepaths: 2 or more FilePath objects
        :returns: FilePath that should take precedent as to page source
        '''
        filepaths.sort(key=lambda p: (p.ctime(), p.basename))
        return filepaths[0]
