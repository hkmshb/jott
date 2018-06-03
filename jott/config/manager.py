from weakref import WeakKeyDictionary
from jott.fs import FileNotFoundError
from .confdicts import ConfigFile
from . import basedirs



class ConfigManager:
    '''This cklass defines an object that manages a set of config files.

    The config manager abstracts the lookup of files using the XDG search
    paths and ensures that ther is only a single instance used for each
    config file.

    The config manager can switch the config file based on the config
    profile that is used. The profile is determined by the jotter 
    properties. However this object relies on it's creator to setup the
    hooks to get the property from the jotter. Changes to the profile are
    communicated to all users of the config by means of the "changed"
    signal on ConfigFile and ConfigDict objects.
    '''

    def __init__(self, folder=None, folders=None, profile=None):
        '''Initializes a new instance of the ConfigManager class.

        :param folder: the folder for reading and writing config files,
            e.g. a Folder or a VirtualConfigBackend object. If no folder
            is given, the XDG basedirs are used and folders is ignored.
        :param folders: list of generator of Folder objects used as search
            path when a config file does not exist on Folder.
        :profile: initial profile name
        '''
        self.profile = profile
        self._config_files = WeakKeyDictionary()
        self._config_dicts = WeakKeyDictionary()
        if folder is None:
            assert folders is None, "Do not provide 'folders' without 'folder'"
        self._folder = folder
        self._folders = folders

    def get_config_dict(self, filename):
        '''Returns a ConfigSection object for filename.
        '''
        if filename not in self._config_dicts:
            file = self.get_config_file(filename)
            config_dict = ConfigFile(file)
            self._config_dicts[filename] = config_dict
        return self._config_dicts[filename]

    def get_config_file(self, filename):
        '''Returns a ConfigFile object for filename.
        '''
        if filename not in self._config_files:
            file, defaults = self._get_file(filename)
            config_file = ConfigFile(file)  # defaults omitted
            self._config_files[filename] = config_file
        return self._config_files[filename]

    def set_profile(self, profile):
        '''Set the profile to use for the configuration.

        :param profile: the profile name or None
        '''
        assert profile is None or isinstance(profile, str)
        if profile != self.profile:
            self.profile = profile
            for path, conffile in self._config_files.items():
                if path.startswith('<profile>/'):
                    file, defaults = self._get_file(path)
                    conffile.set_files(file, defaults)

    def _get_file(self, filename):
        basepath = filename.replace('<profile>/', '')
        if self.profile:
            newpath = 'profiles/{}/'.format(self.profile)
            path = filename.replace('<profile>/', newpath)
        else:
            path = basepath

        if self._folder:
            file = self._folder.file(path)
            if self._folders:
                defaults = DefaultFileIter(self._folders, path)
            else:
                defaults = DefaultFileIter([], path)

            if self.profile and filename.startswith('<profile>/'):
                mypath = filename.replace('<profile>/', '')
                defaults.extra.insert(0, self._folder.file(mypath))
        else:
            file = basedirs.XDG_CONFIG_HOME.file('jott/' + path)
            defaults = XDGConfigFileIter(basepath)
        return file, defaults


class DefaultFileIter:
    '''Generator for iterating default files.

    Will yield first the files in extra followed by files that are based on
    path and folders. Yields only existing files.
    '''

    def __init__(self, folders, path, extra=None):
        self.path = path
        self.folders = folders
        self.extra = extra or []

    def __iter__(self):
        for file in self.extra:
            if file.exists():
                yield file

        for folder in self.folders:
            file = folder.file(self.path)
            if file.exists():
                yield file


class XDGConfigFileIter(DefaultFileIter):
    '''Like DefaultFileIter, but uses XDG config folders.
    '''
    def __init__(self, path, extra=None):
        self.path = path
        self.extra = extra or []
        self.folders = XDGConfigDirsIter()


class XDGConfigDirsIter:
    '''Generator for iterating XDG config folders.

    Yields the 'jott' sub-folder of each XDG config file.
    '''

    def __iter__(self):
        from . import data_dirs
        yield basedirs.XDG_CONFIG_HOME.child(('jott',))
        for folder in basedirs.XDG_CONFIG_DIRS:
            yield folder.child(('jott',))
        for folder in data_dirs():
            yield folder
