import os
import re
import logging
import jott.fs
from jott.fs import is_url_re
from jott.fs import File, Folder, LocalFile, LocalFolder

log = logging.getLogger('jott.jotter')



def get_jotter_info(path):
    '''Look up the jotter info for either a uri or a File or a Folder object.

    :param path: path a string, File or Folder object
    :returns: JotterInfo object, or None if no jotter config was found
    '''
    path = _get_path_object(path)
    info = JotterInfo(path.uri)
    if info.update():
        return info
    return None


def get_jotter_list():
    '''Returns a list of known jotter as a JotterInfoList

    This will load the list from the default 'jotter.list' file
    '''
    config = ConfigManager()
    file = config.get_config_file('jotters.list')
    return JotterInfoList(file)


def _get_path_object(path):
    if isinstance(path, str):
        file = LocalFile(path)
        if file.exists():
            path = file
        else:
            path = LocalFolder(path)
    else:
        assert isinstance(path, (File, Folder))
    return path


def resolve_jotter(string, pwd=None):
    '''Takes either a jotter name or a file or folder path. For a name it
    resolves the path by looking for a jotter of that name in the jotter
    list.

    Note that the JotterInfo for a file path is not using any actual info
    from the jotter, it just passes on the uri. Use build_jotter() to split
    the URI in a jotter location and an optional page path.

    :returns: a JotterInfo or None
    '''
    assert isinstance(string, str)
    from jott.fs import isabs

    if '/' in string or os.path.sep in string:
        # FIXME do we need a isfilepath function in fs
        if is_url_re.match(string):
            uri = string
        elif pwd and not isabs(string):
            uri = pwd + os.sep + string
        else:
            uri = string
        return JotterInfo(uri)
    else:
        jlist = get_jotter_list()
        return jlist.get_by_name(string)


class JotterInfo:
    '''This keeps the information for a jotter.
    '''

    def __init__(self, uri, name=None, icon=None, mtime=None, **kwargs):
        '''Initializes a new instance of JotterInfo.

        :param uri: the location of the jotter.
        :param user_path: the location of the jotter relative to the home folder
            (starts with '~/') or None
        :param name: the jotter name (or the basename of the uri)
        :param icon: the file uri for the jotter icon
        :param icon_path: the location of the icon as configured (either relative
            to the jotter location, relative to home folder or absolute path)
        :param mtime: the mtime of the config file this info was read from
        :param active: the attribute used to signal whether the jotter is already
            open or not.
        '''
        if isinstance(uri, str) and is_url_re.match(uri) and \
                not uri.startswith('file://'):
            self.uri = uri
            self.name = name
            self.user_path = None
        else:
            lfile = LocalFile(uri)  # TODO: use proxy
            self.uri = lfile.uri
            self.user_path = lfile.userpath
            self.name = name or lfile.basename
        self.icon_path = icon
        self.icon = LocalFile(icon).uri # TODO: use proxy
        self.mtime = mtime
        self.active = None

    def __eq__(self, other):
        if isinstance(other, str):
            return self.uri == other
        elif hasattr(other, 'uri'):
            return self.uri == other.uri
        return False

    def __repr__(self):
        return '<{}: {}>'.format(
            self.__class__.__name__,
            self.uri
        )

    def update(self):
        '''Checks if this info is up to date if not the object is updated.

        This checks the jotter.jott file for jotter folders and reads it if
        it changed. It uses the mtime attribute to keep tract of changes.

        :returns: True when data was updated, otherwise False.
        '''
        folder = LocalFolder(self.uri)  # TODO: use proxy
        lfile = folder.file('jotter.jott')
        if file.exists() and file.mtime() != self.mtime:
            config = JotterConfig(lfile)
            section = config['Jotter']

            self.name = section['name']
            self.icon_path = section['icon']
            
            icon, _ = _resolve_relconfig(folder, section)
            self.icon = icon.uri if icon else None
            self.mtime = lfile.mtime()
            return True
        return False


class VirtualFile:

    def __init__(self, lines):
        self.lines = lines

    def readlines(self):
        return self.lines


class JotterInfoList(list):
    '''Keeps a list of JotterInfo objects.

    It maps to a jotter.list config file that keeps a list of jotter locations
    and cached attributes from the various jotter.jott config files.
    '''

    def __init__(self, file):
        self.file = file
        self.default = None
        self. read()
        try:
            self.update()
        except:
            log.exception('Exception while loading jotter list')

    def get_by_name(self, name):
        '''Gets a JotterInfo object for a jotter by name.

        Names are checked case sensitive first, then case-insensitive.

        :param name: notebook name as string
        :returns: a JotterInfo object or None
        '''
        for info in self:
            if info.name == name:
                return info

        lname = name.lower()
        for info in self:
            if info.name.lower() == lname:
                return info
        return None

    def parse(self, text):
        '''Parses the config and cachje and populates the list

        Format is::

            [JotterList]
            Default=uri1
            1=uri1
            2=uri2

            [Jotter 1]
            name=Foo
            uri=uri1

        Then followed by more '[Jotter]' sections that are cache data

        :param text: a string or a list of lines
        '''
        if isinstance(text, str):
            text = text.splitlines(True)

        n, l = (0, 0)
        for i, line in enumerate(text):
            if line.strip() == '[Jotter]':
                n += 1
                text[i] = '[Jotter {}]\n'.format(n)
            elif line and not line.isspace() \
                and not line.lstrip().startswith('[') \
                and not line.lstrip().startswith('#') \
                and not '=' in line:
                l += 1
                text[i] = ('{}='.format(l)) + line

        config = ConfigFile(VirtualFile(text))
        jlist = config['JotterList']
        jlist.define(Default=String(None))
        jlist.define((k, String(None)) for k in jlist._input.keys())

        for key, uri in config['JotterList'].items():
            if key == 'Default':
                continue
            
            section = config['Jotter {}'.format(key)]
            section.define(
                uri=String(None),
                name=String(None),
                icon=String(None),
                mtime=String(None)
            )
            if section['uri'] == uri:
                info = JotterInfo(**section)
            else:
                info = JotterInfo(uri)
            self.append(info)

        if 'Default' in config['JotterList'] \
            and config['JotterList']['Default']:
            self.set_default(config['JotterList']['Default'])

    def set_default(self, uri):
        '''Sets the default jotter.

        :param uri: the file uri or filepath for the default jotter
        '''
        uri = LocalFile(uri).uri    # TODO: use proxy file object
        for info in self:
            if info.uri == uri:
                self.default = info
                return
        else:
            info = JotterInfo(uri)
            self.insert(0, info)
            self.default = info

    def update(self):
        '''Update JotterInfo objects and write cache.
        '''
        changed = False
        for info in self:
            changed = info.update() or changed
        if changed:
            self.write()

    def read(self):
        '''Read the config and cache and populate the list.
        '''
        lines = self.file.readlines()
        self.parse(lines)

    def write(self):
        '''Write the config and cache
        '''
        if self.default:
            default = self.default.user_path or self.default.uri
        else:
            default = None

        lines = [
            '[JotterList]\n',
            'Default={}\n'.format(default or '')
        ]
        for i, info in enumerate(self):
            n = i + 1
            uri = info.user_path or info.uri
            lines.append('{}={}\n'.format(n, uri))

        for i, info in enumerate(self):
            n = i + 1
            uri = info.user_path or info.uri
            lines.extend([
                '\n',
                '[Jotter {}]\n'.format(n),
                'uri={}\n'.format(uri),
                'name={}\n'.format(info.name),
                'icon={}\n'.format(info.icon_path)
            ])
        self.file.writelines(lines)