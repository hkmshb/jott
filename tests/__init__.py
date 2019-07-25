import sys
import shutil
import tempfile
import logging
import os, os.path as osp


HERE = osp.abspath(osp.dirname(__file__))
TMPDIR = osp.abspath(osp.join(HERE, 'tmp'))
DATADIR = osp.abspath(osp.join(HERE, 'data'))

REAL_TMPDIR = tempfile.gettempdir()


def _setup_environment():
    '''Method to be run once before test suite starts'''
    os.environ.update({
        'JOTT_TEST_ROOT': os.getcwd(),
        'TMP': TMPDIR,
        'REAL_TMP': REAL_TMPDIR,
        'XDG_DATA_HOME': os.path.join(TMPDIR, 'data_home'),
        'XDG_DATA_DIRS': os.path.join(TMPDIR, 'data_dir'),
        'XDG_CONFIG_HOME': os.path.join(TMPDIR, 'config_home'),
        'XDG_CONFIG_DIRS': os.path.join(TMPDIR, 'config_dir'),
        'XDG_CACHE_HOME': os.path.join(TMPDIR, 'cache_home')
    })

    if os.path.isdir(TMPDIR):
        shutil.rmtree(TMPDIR)
    os.makedirs(TMPDIR)


_setup_environment()


class LoggingFilter(logging.Filter):
    '''Convenience class to supress jott errors and warnings in the test suite.
    Acts as a context manager and can be used with the 'with' keyword.
    '''
    # due to how "logging" module works, logging channels do inherit handlers
    # of parents but not filters. Therefore setting a filter on the 'jott'
    # channel will not supress messages from sub-channels. Instead we need to
    # set the filter both on the channel and on top level handlers to get the
    # desired effect.

    def __init__(self, logger, message=None):
        '''Constructor.

        :param logger: the logging channel name
        :param message: can be a string, or a sequence of strings
        '''
        self.logger = logger
        self.message = message

    def __enter__(self):
        logging.getLogger(self.logger).addFilter(self)
        for handler in logging.getLogger().handlers:
            handler.addFilter(self)

    def __exit__(self, *exc_info):
        logging.getLogger(self.logger).removeFilter(self)
        for handler in logging.getLogger().handlers:
            handler.removeFilter(self)

    def filter(self, record):
        if record.name.startswith(self.logger):
            msg = record.getMessage()
            if self.message is None:
                return False
            elif isinstance(self.message, tuple):
                return not any(msg.startswith(m) for m in self.message)
            else:
                return not msg.startswith(self.message)
        else:
            return True


class TestMixin:
    '''Class with helper functions for test cases.
    '''
    @classmethod
    def clear_tmp_dir(cls, name=None):
        '''Clears the tmp dir for this test.
        '''
        pth = cls._get_tmp_name(name)
        assert not os.path.exists(pth), (
            'This path should not exist: {}'.format(pth)
        )
        return pth

    @classmethod
    def create_tmp_dir(cls, name=None):
        '''Returns a path to a tmp dir where tests can write data. The dir is
        removed and recreated empty every time this function is called with
        the same name from the same class.
        '''
        cls.clear_tmp_dir(name)
        pth = cls._get_tmp_name(name)
        os.makedirs(pth)
        assert os.path.exists(pth)
        return pth

    @classmethod
    def get_tmp_name(cls, name=None):
        '''Returns the same path as create_tmp_dir() but without touching it.
        This method will raise an exception when a file or dir exists of the
        same.
        '''
        pth = self._get_tmp_name(name)
        assert os.path.exists(pth), (
            'This path should not exist: {}'.format(pth)
        )
        return pth

    @classmethod
    def _get_tmp_name(cls, name):
        if name:
            assert not os.path.sep in name, (
                "Dont use this method to get sub folders or file")
            name = cls.__name__ + '_' + name
        else:
            name = cls.__name__
        return os.path.join(TMPDIR, name)
